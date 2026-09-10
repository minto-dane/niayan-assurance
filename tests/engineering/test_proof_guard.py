# SPDX-License-Identifier: BSD-3-Clause
"""Small process tests of development limits; no real prover or host pressure."""
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

GUARD = Path(__file__).resolve().parents[2] / 'ci/proof-guard.py'
spec = importlib.util.spec_from_file_location('proof_guard', GUARD)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
TEST_SESSION_MIB = 128


class ProofGuardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='nia-proof-guard-test-')
        self.directory = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def run_small(self, source, **limits):
        # Tighten the aggregate fixture limit as well as RLIMIT_AS. Keep the
        # real host reserve and the production prover defaults unchanged.
        limits = {'session_mib': TEST_SESSION_MIB, **limits}
        return guard.supervise([sys.executable, '-I', '-c', source],
                               address_mib=128, seconds=5, **limits)

    def test_exit_status_is_preserved(self):
        for code in (0, 9):
            with self.subTest(code=code):
                r = self.run_small(f'raise SystemExit({code})')
                self.assertEqual(r['returncode'], code, r)
                self.assertEqual(r['result'], 'pass' if code == 0 else 'fail', r)
                self.assertEqual(r['limits']['sampled_session_rss_mib'], TEST_SESSION_MIB)
                self.assertEqual(r['limits']['minimum_available_mib'], 2048)

    def test_all_component_make_targets_use_guard_even_with_build_jobs_override(self):
        root = GUARD.parents[2]
        for repo in ('assurance', 'pkgcore', 'statecore', 'controlcore',
                     'configcore', 'resolvercore', 'capsulecore'):
            with self.subTest(repo=repo):
                r = subprocess.run(['make', '--no-print-directory', '-n', 'flow', 'prove',
                                    'JOBS=8', 'GNATPROVE=/usr/bin/true'],
                                   cwd=root / repo, capture_output=True, text=True, timeout=5)
                self.assertEqual(r.returncode, 0, r.stderr)
                commands = [line for line in r.stdout.splitlines() if 'python3 ci/proof-guard.py -- ' in line]
                self.assertEqual(len(commands), 2, r.stdout)
                self.assertNotIn('-j8', r.stdout)
                self.assertIn('--checks-as-errors=on --warnings=error', commands[0])
                self.assertIn('--level=4 --checks-as-errors=on --warnings=error', commands[1])

    def test_limits_and_priority_reach_grandchild(self):
        target = self.directory / 'limits.json'
        source = ('import json,os,resource,subprocess,sys; '
                  'data=[resource.getrlimit(resource.RLIMIT_AS), '
                  'resource.getrlimit(resource.RLIMIT_CORE), '
                  'resource.getrlimit(resource.RLIMIT_CPU), os.getpriority(os.PRIO_PROCESS,0)]; '
                  f'open({str(target)!r},"w").write(json.dumps(data))')
        r = self.run_small(f'import subprocess,sys; subprocess.run([sys.executable,"-I","-c",{source!r}],check=True)')
        self.assertEqual(r['result'], 'pass', r)
        memory, core, cpu, priority = json.loads(target.read_text())
        self.assertEqual(memory, [128 * guard.MIB] * 2)
        self.assertEqual(core, [0, 0])
        self.assertEqual(cpu, [5, 5])
        self.assertGreaterEqual(priority, 15)

    def test_excess_allocation_is_refused_without_allocating_it(self):
        target = self.directory / 'refused'
        r = self.run_small('try:\n    bytearray(256*1024*1024)\n'
                           f'except MemoryError:\n    open({str(target)!r},"w").write("refused")\n'
                           'else:\n    raise SystemExit(2)\n')
        self.assertEqual(r['result'], 'pass', r)
        self.assertEqual(target.read_text(), 'refused')
        self.assertLess(r['peak_session_rss_bytes'], 64 * guard.MIB)

    def test_shared_lock_refuses_second_run(self):
        lock = guard.acquire_lock()
        try:
            r = self.run_small('raise SystemExit(0)')
            self.assertEqual(r['result'], 'not-run', r)
            self.assertEqual(r['reason'], 'another-proof-is-running', r)
        finally:
            os.close(lock)
        self.assertEqual(self.run_small('pass')['result'], 'pass')

    def test_low_starting_memory_launches_nothing(self):
        with patch.object(guard, 'available_bytes', return_value=guard.RESERVE_MIB * guard.MIB):
            r = self.run_small('raise SystemExit(0)')
        self.assertEqual(r['result'], 'not-run', r)
        self.assertEqual(r['reason'], 'insufficient-memory-before-start', r)
        self.assertIsNone(r['returncode'])

    def test_fixture_budget_still_requires_reserve_plus_its_full_limit(self):
        available = (guard.RESERVE_MIB + TEST_SESSION_MIB) * guard.MIB - 1
        with patch.object(guard, 'available_bytes', return_value=available), \
                patch.object(guard.subprocess, 'Popen') as launch:
            r = self.run_small('raise SystemExit(0)')
        self.assertEqual(r['reason'], 'insufficient-memory-before-start', r)
        self.assertEqual(r['result'], 'not-run', r)
        launch.assert_not_called()

    def test_default_prover_budget_still_requires_four_gib_before_start(self):
        self.assertEqual(guard.SESSION_MIB, 2048)
        self.assertEqual(guard.RESERVE_MIB, 2048)
        with patch.object(guard, 'available_bytes', return_value=4096 * guard.MIB - 1), \
                patch.object(guard.subprocess, 'Popen') as launch:
            r = guard.supervise([sys.executable, '-I', '-c', 'raise SystemExit(0)'])
        self.assertEqual(r['reason'], 'insufficient-memory-before-start', r)
        self.assertEqual(r['result'], 'not-run', r)
        self.assertEqual(r['limits']['sampled_session_rss_mib'], 2048)
        self.assertEqual(r['limits']['minimum_available_mib'], 2048)
        launch.assert_not_called()

    def test_memory_drop_stops_running_child(self):
        with patch.object(guard, 'available_bytes', side_effect=[8 * 1024 * guard.MIB, 0]):
            r = self.run_small('import time; time.sleep(10)')
        self.assertEqual(r['result'], 'fail', r)
        self.assertEqual(r['reason'], 'host-memory-stop', r)

    def test_aggregate_accounts_for_two_small_children(self):
        # Total actual allocation is 40 MiB; intentionally tiny test threshold.
        worker = 'import os,time; os.setpgid(0,0); a=bytearray(20*1024*1024); time.sleep(10)'
        r = self.run_small('import subprocess,sys,time; '
                           f'p=[subprocess.Popen([sys.executable,"-I","-c",{worker!r}]) for _ in range(2)]; '
                           'time.sleep(10)', session_mib=40)
        self.assertEqual(r['reason'], 'session-memory-stop', r)
        self.assertEqual(r['result'], 'fail', r)
        self.assertGreater(r['peak_session_rss_bytes'], 40 * guard.MIB)

    def test_timeout_cleans_descendant(self):
        target = self.directory / 'child-pid'
        worker = f'import os,time; os.setpgid(0,0); open({str(target)!r},"w").write(str(os.getpid())); time.sleep(10)'
        r = guard.supervise([sys.executable, '-I', '-c',
              f'import subprocess,sys,time; subprocess.Popen([sys.executable,"-I","-c",{worker!r}]); time.sleep(10)'],
              seconds=0.5, address_mib=128, session_mib=TEST_SESSION_MIB)
        self.assertEqual(r['reason'], 'wall-time-limit', r)
        self.assertEqual(r['result'], 'fail', r)
        self.assert_stopped(int(target.read_text()))

    def test_normal_leader_exit_reaps_solver_in_another_group(self):
        target = self.directory / 'child-pid'
        worker = f'import os,time; os.setpgid(0,0); open({str(target)!r},"w").write(str(os.getpid())); time.sleep(10)'
        source = ('import subprocess,sys,time; '
                  f'p=subprocess.Popen([sys.executable,"-I","-c",{worker!r}]); '
                  'time.sleep(0.15)')
        before = guard.subreaper()
        r = self.run_small(source)
        self.assertEqual(r['result'], 'pass', r)
        self.assert_stopped(int(target.read_text()))
        self.assertEqual(guard.direct_children(), [])
        self.assertEqual(guard.subreaper(), before)

    def test_existing_child_is_not_adopted_or_killed(self):
        child = subprocess.Popen([sys.executable, '-I', '-c', 'import time; time.sleep(5)'])
        try:
            r = self.run_small('pass')
            self.assertEqual(r['result'], 'not-run', r)
            self.assertIn('no existing children', r['reason'])
            self.assertIsNone(child.poll())
        finally:
            child.terminate()
            child.wait(timeout=2)

    def test_timeout_reaps_multiple_generations_of_separate_groups(self):
        target = self.directory / 'grandchild-pid'
        worker = f'import os,time; os.setpgid(0,0); open({str(target)!r},"w").write(str(os.getpid())); time.sleep(10)'
        middle = ('import os,subprocess,sys,time; os.setpgid(0,0); '
                  f'subprocess.Popen([sys.executable,"-I","-c",{worker!r}]); time.sleep(10)')
        outer = f'import subprocess,sys,time; subprocess.Popen([sys.executable,"-I","-c",{middle!r}]); time.sleep(10)'
        r = guard.supervise([sys.executable, '-I', '-c', outer], seconds=0.5, address_mib=128,
                            session_mib=TEST_SESSION_MIB)
        self.assertEqual(r['reason'], 'wall-time-limit', r)
        self.assert_stopped(int(target.read_text()))
        self.assertEqual(guard.direct_children(), [])

    def assert_stopped(self, pid):
        for _ in range(20):
            try:
                state = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[0]
                if state == 'Z':
                    return  # Exited; adoption/reaping belongs to container init.
            except FileNotFoundError:
                return
            time.sleep(0.05)
        self.fail('guard left a running child')

    def test_term_cleans_descendant_and_releases_lock(self):
        target = self.directory / 'child-pid'
        worker = f'import os,time; open({str(target)!r},"w").write(str(os.getpid())); time.sleep(10)'
        launcher = ('import importlib.util,sys; '
                    f's=importlib.util.spec_from_file_location("g",{str(GUARD)!r}); '
                    'g=importlib.util.module_from_spec(s); s.loader.exec_module(g); '
                    f'r=g.supervise([sys.executable,"-I","-c",{worker!r}],seconds=5,address_mib=128,session_mib={TEST_SESSION_MIB}); '
                    'print(r["reason"],flush=True)')
        child = subprocess.Popen([sys.executable, '-I', '-c', launcher], stdout=subprocess.PIPE, text=True)
        try:
            end = time.monotonic() + 3
            while not target.exists() and time.monotonic() < end:
                time.sleep(0.02)
            self.assertTrue(target.exists())
            child.send_signal(signal.SIGTERM)
            output, _ = child.communicate(timeout=3)
            self.assertIn('signal-interrupted', output)
            self.assert_stopped(int(target.read_text()))
            self.assertEqual(self.run_small('pass')['result'], 'pass')
        finally:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=6)
            child.stdout.close()

    def test_invalid_or_relaxed_limits_are_refused(self):
        for limits in ({'address_mib': 2048}, {'session_mib': 4096},
                       {'reserve_mib': 1024}, {'seconds': 7200}):
            with self.subTest(limits=limits), self.assertRaises(ValueError):
                guard.supervise([sys.executable, '-c', 'pass'], **limits)

    def test_outer_runner_timeout_allows_guard_to_clean_its_group(self):
        sys.path.insert(0, str(GUARD.parent))
        spec = importlib.util.spec_from_file_location('guard_outer_runner', GUARD.parent / 'run-engineering-checks.py')
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        target = self.directory / 'child-pid'
        worker = f'import os,time; open({str(target)!r},"w").write(str(os.getpid())); time.sleep(10)'
        launcher = ('import importlib.util,sys; '
                    f's=importlib.util.spec_from_file_location("g",{str(GUARD)!r}); '
                    'g=importlib.util.module_from_spec(s); s.loader.exec_module(g); '
                    f'r=g.supervise([sys.executable,"-I","-c",{worker!r}],seconds=5,address_mib=128,session_mib={TEST_SESSION_MIB}); '
                    'print(r["reason"],flush=True)')
        r = runner.run_command([sys.executable, '-I', '-c', launcher], self.directory,
                               self.directory / 'outer.log', runner.clean_env(self.directory),
                               timeout=0.5, termination_grace=1)
        self.assertEqual(r['result'], 'timeout', r)
        self.assert_stopped(int(target.read_text()))
        self.assertEqual(self.run_small('pass')['result'], 'pass')


if __name__ == '__main__':
    unittest.main()
