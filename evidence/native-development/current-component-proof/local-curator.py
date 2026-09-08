"""Bind separately completed full proofs to the exact current proof inputs."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import sys

ROOT = Path('/home/nia/devbox/niaos/nia-os-consent')
WORK = ROOT.parent / '.work'
sys.path.insert(0, str(ROOT / 'assurance/ci'))
import engineering as eng

inputs = json.loads((WORK / 'final-proof-inputs.json').read_text())
subject = eng.source_subject(ROOT)
assert subject == inputs['source_subject']
records = []
sources = {}
for repo, expected in inputs['repositories'].items():
    r = ROOT / repo
    paths = [r / 'proof.gpr', r / 'Makefile', r / 'ci/proof.mk',
             r / 'ci/proof-guard.py', r / 'ci/gnatprove.lock.json',
             *r.glob('src/*.ad?'), *r.glob('vendor/**/src/*.ad?')]
    current = {str(p.relative_to(r)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(paths)}
    assert current == expected, repo
    if repo == 'pkgcore':
        source = ROOT / 'assurance/evidence/native-development/scoped-proof-3015db9/pkgcore'
    elif repo == 'assurance':
        source = ROOT / 'assurance/evidence/native-development/scoped-proof-inductive-20260908/assurance'
    elif repo == 'capsulecore':
        source = WORK / 'capsule-final-strict-proof'
    else:
        source = WORK / 'remaining-strict-proof' / repo
    evidence = json.loads((source / 'report.json').read_text())
    assert evidence['result'] == 'pass', repo
    if 'proof_inputs' in evidence:
        assert evidence['proof_inputs'] == current, repo
    else:
        assert evidence['proof_inputs_before'] == evidence['proof_inputs_after'] == current, repo
    guards = {}
    for mode in ('flow', 'prove'):
        content = (source / (mode + '.log')).read_text()
        guard = [json.loads(line.split('proof-guard: ', 1)[1])
                 for line in content.splitlines() if line.startswith('proof-guard: {')]
        assert guard[-1]['result'] == 'pass' and guard[-1]['returncode'] == 0, (repo, mode)
        command = guard[0]['command']
        for flag in ('-j1', '-U', '--checks-as-errors=on', '--warnings=error'):
            assert flag in command, (repo, mode, flag)
        assert '--mode=' + ('flow' if mode == 'flow' else 'all') in command
        if mode == 'prove':
            assert '--level=4' in command and '--proof-warnings=on' in command
            match = re.findall(r'Success: all checks proved \((\d+) checks\)\.', content)
            assert len(match) == 1, repo
            count = int(match[0])
        guards[mode] = guard[-1]
    records.append({'repository': repo, 'result': 'pass', 'checks': count,
                    'guards': guards, 'proof_inputs': current,
                    'reused_from_older_workspace_subject': repo != 'capsulecore'})
    sources[repo] = source

assert eng.source_subject(ROOT) == subject
out = ROOT / 'assurance/evidence/native-development/current-component-proof'
out.mkdir(exist_ok=False)
for repo, source in sources.items():
    shutil.copytree(source, out / repo)
    scope = (WORK / 'capsule-final-strict-proof-scope.log' if repo == 'capsulecore'
             else WORK / 'remaining-strict-proof' / (repo + '-scope.log'))
    if scope.exists():
        shutil.copy2(scope, out / repo / 'scope.log')
shutil.copy2(ROOT / 'assurance/evidence/engineering-0jo5t77n/gnatprove-version.log',
             out / 'gnatprove-version.log')
shutil.copy2(WORK / 'full-proof-scoped-current.log', out / 'first-workspace-scope.log')
shutil.copy2(WORK / 'full-proof-inductive-current.log', out / 'second-workspace-scope.log')
report = {'result': 'all-seven-components-strict-flow-and-full-level-4-proof-pass',
          'source_subject': subject, 'production_qualified': False,
          'scope': 'SPARK units in each proof.gpr, including fixed vendors; excludes runtime FFI and operating-system integration',
          'counting': 'Each component includes its vendors, so per-component counts overlap.',
          'binding': 'Each current proof input set was compared exactly with its completed full proof. pkgcore mathematical inputs are unchanged from workspace subject 091ce3fc116c93462e9aa47810c913a42c8f6d78b2578d1810e6e3a8c5a95945; only its container dependency setup changed. Assurance, statecore, controlcore, configcore and resolvercore likewise retain the exact mathematical inputs of their completed runs at workspace subject 330e7a97392a3a2706e0ca6f69c4cb4b52995be0cf8f7da200a40be2a4a73c70. Capsule is verified after its own final contract changes. This is a composition of complete per-component runs, not a claim that an interrupted workspace command passed.',
          'components': records}
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
manifest = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(out.rglob('*')) if p.is_file()}
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(out / 'report.json')
