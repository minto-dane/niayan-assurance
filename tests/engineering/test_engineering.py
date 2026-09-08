# SPDX-License-Identifier: MIT
"""Tests of the development validator itself, NOT of compiled Ada behavior."""
from __future__ import annotations
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'assurance/ci'))
import engineering as eng
spec=importlib.util.spec_from_file_location('engineering_runner',ROOT/'assurance/ci/run-engineering-checks.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

class SafeInputTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='mission-validator-input-')
        self.root=Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def test_regular_read_and_bound(self):
        p=self.root/'f';p.write_bytes(b'abcd')
        self.assertEqual(eng.read_regular(p),b'abcd')
        with self.assertRaises(eng.Invalid):eng.read_regular(p,3)
    def test_final_symlink_refused(self):
        p=self.root/'f';p.write_bytes(b'a');q=self.root/'s';q.symlink_to(p)
        with self.assertRaises(eng.Invalid):eng.read_regular(q)
    def test_fifo_refused_before_read(self):
        p=self.root/'f';os.mkfifo(p)
        with self.assertRaises(eng.Invalid):eng.read_regular(p)
    def test_socket_refused_before_read(self):
        p=self.root/'s'
        with socket.socket(socket.AF_UNIX) as sock:
            sock.bind(str(p))
            with self.assertRaises(eng.Invalid):eng.read_regular(p)
    def test_directory_refused(self):
        with self.assertRaises(eng.Invalid):eng.read_regular(self.root)
    def test_duplicate_json_refused(self):
        p=self.root/'j';p.write_text('{"version":1,"version":2}')
        with self.assertRaises(eng.Invalid):eng.load_json(p)
    def test_nested_duplicate_json_refused(self):
        p=self.root/'j';p.write_text('{"v":{"x":1,"x":2}}')
        with self.assertRaises(eng.Invalid):eng.load_json(p)
    def test_unsafe_references_refused(self):
        for value in ('../outside','/etc/passwd','assurance/../pkgcore/x','assurance//x','assurance/./x','assurance\\x'):
            with self.subTest(value=value):
                with self.assertRaises(eng.Invalid):eng.resolve_ref(self.root,value)
    def test_parent_symlink_refused(self):
        (self.root/'assurance').mkdir();(self.root/'outside').mkdir()
        (self.root/'outside/x').write_text('content');(self.root/'assurance/l').symlink_to(self.root/'outside')
        with self.assertRaises(eng.Invalid):eng.resolve_ref(self.root,'assurance/l/x')
    def test_exact_temporary_arguments(self):
        t={'arguments':['$TEMP/root','$TEMP/state','fixtures/example'],
           'prepare_directories':['$TEMP/root/usr','$TEMP/state']}
        args=runner.expand_test_args(t,self.root)
        self.assertEqual(args,[str(self.root/'root'),str(self.root/'state'),'fixtures/example'])
        self.assertTrue((self.root/'root/usr').is_dir())
        self.assertEqual((self.root/'state').stat().st_mode&0o777,0o700)
    def test_absent_temporary_argument(self):
        args=runner.expand_test_args({'arguments':['$TEMP/new'],'prepare_directories':[]},self.root)
        self.assertEqual(args,[str(self.root/'new')])
        self.assertFalse((self.root/'new').exists())
    def test_unsafe_temporary_argument_refused(self):
        for value in ('$TEMP/../../etc','/etc/passwd','${OTHER}/x'):
            with self.subTest(value=value):
                with self.assertRaises(eng.Invalid):runner.expand_test_args({'arguments':[value]},self.root)
    def test_child_environment_omits_secrets(self):
        old=os.environ.get('MISSION_TEST_SECRET');os.environ['MISSION_TEST_SECRET']='synthetic-test'
        try:self.assertNotIn('MISSION_TEST_SECRET',runner.clean_env(self.root))
        finally:
            if old is None:os.environ.pop('MISSION_TEST_SECRET',None)
            else:os.environ['MISSION_TEST_SECRET']=old
    def test_command_exit_and_log_boundaries(self):
        r=runner.run_command([sys.executable,'-c','print("ok")'],self.root,self.root/'log',runner.clean_env(self.root),5)
        self.assertEqual(r['result'],'pass');self.assertEqual((self.root/'log').read_text(),'ok\n')
        r=runner.run_command([sys.executable,'-c','raise SystemExit(3)'],self.root,self.root/'log2',runner.clean_env(self.root),5)
        self.assertEqual(r['result'],'fail');self.assertEqual(r['returncode'],3)
    def test_absent_command_is_not_run(self):
        r=runner.run_command([str(self.root/'does-not-exist')],self.root,self.root/'log',runner.clean_env(self.root),5)
        self.assertEqual(r['result'],'not-run');self.assertIsNone(r['returncode'])
    def test_timeout_is_not_success(self):
        r=runner.run_command([sys.executable,'-c','import time;time.sleep(5)'],self.root,self.root/'log',runner.clean_env(self.root),1)
        self.assertEqual(r['result'],'timeout')

class TraceabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='mission-traceability-')
        cls.root=Path(cls.tmp.name)
        for repo in eng.WORKTREES:
            shutil.copytree(ROOT/repo,cls.root/repo,ignore=shutil.ignore_patterns('build','evidence','.git','__pycache__'))
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    @contextmanager
    def changed_json(self,name,mutate):
        p=self.root/'assurance/engineering'/name;original=p.read_bytes()
        data=json.loads(original);mutate(data);p.write_text(json.dumps(data))
        try:yield
        finally:p.write_bytes(original)
    def test_baseline_resolves_without_claiming_proof(self):
        r=eng.validate(self.root)
        self.assertEqual(r['result'],'pass');self.assertFalse(r['production_approval'])
        self.assertFalse(r['ada_executed']);self.assertFalse(r['formal_proof'])
    def test_replaced_adr_requires_superseded_status(self):
        with self.changed_json('adrs.json',lambda d:d['decisions'][1].update(status='proposed-for-review')):
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
    def test_requirement_cannot_use_superseded_decision(self):
        with self.changed_json('requirements.json',lambda d:d['requirements'][0].update(adr=['ADR-0002'])):
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
    def test_claimed_production_qualification_rejected(self):
        with self.changed_json('requirements.json',lambda d:d['requirements'][0].update(status='production-qualified')):
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
    def test_missing_adr_reference_rejected(self):
        with self.changed_json('requirements.json',lambda d:d['requirements'][0].update(adr=['ADR-9999'])):
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
    def test_missing_code_reference_rejected(self):
        with self.changed_json('requirements.json',lambda d:d['requirements'][0].update(code=['pkgcore/src/missing.adb'])):
            with self.assertRaises((eng.Invalid,OSError)):eng.validate(self.root)
    def test_duplicate_requirement_rejected(self):
        with self.changed_json('requirements.json',lambda d:d['requirements'].append(d['requirements'][0])):
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
    def test_unknown_requirement_field_rejected(self):
        with self.changed_json('requirements.json',lambda d:d['requirements'][0].update(passed=True)):
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
    def test_empty_verification_obligation_rejected(self):
        with self.changed_json('requirements.json',lambda d:d['requirements'][0].update(required_evidence=[])):
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
    def test_stale_source_inventory_rejected(self):
        p=self.root/'pkgcore/src/pkg_file_replay.adb';original=p.read_bytes()
        try:
            p.write_bytes(original+b'\n-- test-only mutation\n')
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
        finally:p.write_bytes(original)
    def test_missing_test_registration_rejected(self):
        with self.changed_json('test-plan.json',lambda d:d['ada_tests'].pop()):
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
    def test_duplicate_test_registration_rejected(self):
        with self.changed_json('test-plan.json',lambda d:d['ada_tests'].append(d['ada_tests'][0])):
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
    def test_test_plan_cannot_assert_a_pass(self):
        with self.changed_json('test-plan.json',lambda d:d['ada_tests'][0].update(result='pass')):
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
    def test_wrong_io_argument_count_rejected(self):
        def mutate(d):
            next(x for x in d['ada_tests'] if 'run_control_io_tests' in x['main'])['arguments']=['$TEMP/only-one']
        with self.changed_json('test-plan.json',mutate):
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
    def test_missing_hazard_reference_rejected(self):
        with self.changed_json('requirements.json',lambda d:d['requirements'][0].update(hazards=['HAZ-999'])):
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
    def test_fault_catalog_does_not_assert_runtime_execution(self):
        with self.changed_json('fault-cases.json',lambda d:d['cases'][0].update(execution='production-passed')):
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
    def test_evidence_is_excluded_from_source_subject(self):
        a=eng.source_subject(self.root);e=self.root/'assurance/evidence';e.mkdir()
        try:
            (e/'test-report.json').write_text('{"test":"new"}')
            self.assertEqual(a,eng.source_subject(self.root))
        finally:shutil.rmtree(e)
    def test_submodule_gitfile_is_not_source(self):
        a=eng.source_subject(self.root);p=self.root/'assurance/.git'
        p.write_text('gitdir: ../.git/modules/assurance\n')
        try:self.assertEqual(a,eng.source_subject(self.root))
        finally:p.unlink()
    def test_document_change_changes_source_subject(self):
        p=self.root/'assurance/docs/engineering/README.ja.md';original=p.read_bytes()
        try:
            a=eng.source_subject(self.root);p.write_bytes(original+b'\nTest-only review change.\n')
            self.assertNotEqual(a,eng.source_subject(self.root))
        finally:p.write_bytes(original)
    def test_unknown_file_changes_source_subject(self):
        p=self.root/'assurance/engineering/extra.txt';a=eng.source_subject(self.root)
        try:p.write_text('unexpected');self.assertNotEqual(a,eng.source_subject(self.root))
        finally:p.unlink()
    def test_fault_catalog_cannot_claim_ada_execution(self):
        with self.changed_json('fault-cases.json',lambda d:d.update(actual_ada_execution=True)):
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
    def test_unknown_hazard_fields_rejected(self):
        with self.changed_json('hazards.json',lambda d:d['hazards'][0].update(automatically_closed=True)):
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
    def test_unassigned_owners_not_implicitly_approved(self):
        with self.changed_json('ownership.json',lambda d:d.update(unassigned_is_approved=True)):
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
    def test_stale_api_index_rejected(self):
        p=self.root/'assurance/docs/engineering/api-index.ja.md';old=p.read_bytes()
        try:
            p.write_bytes(old+b'\nNot generated.\n')
            with self.assertRaises(eng.Invalid):eng.validate(self.root)
        finally:p.write_bytes(old)
    def test_unknown_fault_reference_rejected(self):
        with self.changed_json('fault-cases.json',lambda d:d['cases'][0].update(reference_tests='assurance/tests/missing.py')):
            with self.assertRaises((eng.Invalid,OSError)):eng.validate(self.root)
    def test_api_inventory_is_lexical_not_semantic(self):
        d=eng.inventory(self.root)
        self.assertFalse(d['formal_proof'])
        self.assertTrue(all(x['semantic_analysis'] is False for x in d['modules']))
        self.assertTrue(any(x['path']=='pkgcore/src/pkg_file_replay.adb' for x in d['modules']))

if __name__=='__main__':unittest.main()
