"""Local acceptance orchestration: each heavy child enters the verified scope."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import shutil
import subprocess
import sys

ROOT = Path('/home/nia/devbox/niaos/nia-os-consent')
WORK = ROOT.parent / '.work'
REPOS = ('assurance', 'pkgcore', 'statecore', 'controlcore', 'configcore',
         'resolvercore', 'capsulecore', 'distribution')
IMAGE = 'localhost/niaos-dev:20260908-gpg'
PODMAN = ['sudo', '-n', 'podman', '--cgroup-manager=cgroupfs', '--events-backend=file',
          '--storage-driver=vfs', '--root', str(WORK / 'podman-root'),
          '--runroot', str(WORK / 'podman-session-run'),
          '--tmpdir', str(WORK / 'podman-session-tmp'), '--transient-store']
OUT = WORK / 'fixed-current-acceptance'
OUT.mkdir(exist_ok=False)
TREE = OUT / 'workspace'
TREE.mkdir()
sys.path.insert(0, str(ROOT / 'assurance/ci'))
import engineering as eng


def copy_checkout(source, destination):
    paths = subprocess.check_output(['git', 'ls-files', '-c', '-o',
                                     '--exclude-standard', '-z'], cwd=source)
    for item in paths.split(b'\0'):
        if not item:
            continue
        name = item.decode()
        p = source / name
        if p.is_dir():
            continue  # Submodule copied from its own tracked file list below.
        if p.is_symlink():
            raise RuntimeError('unexpected checkout symlink: ' + str(p))
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)


copy_checkout(ROOT, TREE)
for repo in REPOS:
    copy_checkout(ROOT / repo, TREE / repo)
subject = eng.source_subject(ROOT)
assert eng.source_subject(TREE) == subject
report = {'result': 'in-progress-not-accepted', 'source_subject': subject,
          'started_utc': datetime.now(timezone.utc).isoformat(),
          'production_qualified': False, 'checks': []}


def save():
    (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


def run(name, command, timeout=3600):
    argv = ['sh', str(ROOT / 'dev/run-limited.sh'), *command]
    try:
        with (OUT / (name + '.log')).open('w') as log:
            result = subprocess.run(argv, cwd=ROOT, stdin=subprocess.DEVNULL,
                                    stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        if '--cidfile' in command:
            cidfile = Path(command[command.index('--cidfile') + 1])
            if cidfile.exists():
                subprocess.run([*PODMAN, 'rm', '--force', '--ignore',
                                '--cidfile', str(cidfile)], check=True, timeout=30)
        raise
    record = {'name': name, 'argv': argv, 'returncode': result.returncode,
              'log_sha256': hashlib.sha256((OUT / (name + '.log')).read_bytes()).hexdigest()}
    report['checks'].append(record)
    save()
    print(name, result.returncode, flush=True)
    if result.returncode:
        raise RuntimeError(name + ' failed')


def container(mount, *command, user='1000:1000'):
    cidfile = OUT / ('container-' + str(len(report['checks'])) + '.cid')
    return [*PODMAN, 'run', '--rm', '--cidfile', str(cidfile), '--cgroups=disabled', '--network=none',
            '--user=' + user, '-e', 'HOME=/tmp', '-v', str(mount) + ':/workspace',
            IMAGE, *command]


save()
try:
    run('image-identity', [*PODMAN, 'image', 'inspect', IMAGE], 60)
    run('kernel-and-packages', container(TREE, 'python3', '-c',
        "from pathlib import Path; import json,subprocess; "
        "expected={'memory.max':'3221225472','memory.swap.max':'0',"
        "'cpu.max':'100000 100000','pids.max':'128'}; "
        "actual={k:(Path('/sys/fs/cgroup')/k).read_text().strip() for k in expected}; "
        "print(json.dumps(actual),flush=True); assert actual==expected,actual; "
        "subprocess.run(['dpkg-query','-W'],check=True)"))
    run('native', container(TREE, 'make', 'check'))
    native_reports = list((TREE / 'assurance/evidence').glob('engineering-*/report.json'))
    assert len(native_reports) == 1, native_reports
    native = json.loads(native_reports[0].read_text())
    assert native['result'] == 'pass-for-requested-layer-only'
    assert native['source_subject_before'] == native['source_subject_after'] == subject
    counts = {'engineering-unittests': (131, 0), 'manager-reference-tests': (44, 0),
              'configuration-reference-tests': (31, 0), 'resolution-reference-tests': (70, 1),
              'cohort-recovery-tests': (50, 0), 'capsule-policy-tree-tests': (95, 10),
              'distribution-tool-tests': (134, 0)}
    for name, (count, skipped) in counts.items():
        contents = (native_reports[0].parent / (name + '.log')).read_text()
        actual = re.findall(r'^Ran (\d+) tests? in ', contents, re.M)
        assert actual == [str(count)], (name, actual)
        expected = 'OK' + (f' (skipped={skipped})' if skipped else '')
        assert contents.rstrip().endswith(expected), name
    report['native_python_counts'] = counts
    save()
    run('private-dbus', container(TREE, 'make', 'private-dbus'))
    assert 'skipped=' not in (OUT / 'private-dbus.log').read_text()
    run('root-refusal', container(TREE, 'sh', '-ec',
        'cd resolvercore/tests; python3 -B -m unittest '
        'test_resolution_reference.ToolTests.test_unprivileged_helpers_refuse_root -v',
        user='0:0'))
    assert 'skipped=' not in (OUT / 'root-refusal.log').read_text()
    run('reproducible', container(TREE, 'make', 'reproducible'))
    for repo in REPOS[:-1]:
        single = OUT / ('standalone-' + repo)
        copy_checkout(ROOT / repo, single)
        run('standalone-' + repo, container(single, 'make', 'compile-all', 'build', 'test'))
    assert eng.source_subject(ROOT) == subject
    assert eng.source_subject(TREE) == subject
    report['result'] = 'pass'
except Exception as exc:
    report['result'] = 'failed-or-incomplete'
    report['error'] = str(exc)
finally:
    report['ended_utc'] = datetime.now(timezone.utc).isoformat()
    save()
raise SystemExit(0 if report['result'] == 'pass' else 1)
