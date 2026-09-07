#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Development-only traceability validator. No installation or production approval.

Requires seven independent checkouts as sibling directories for integration review.
Individual Ada repositories still build without this bundle-wide tool.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import subprocess
from typing import Any

REPOS = ('assurance', 'pkgcore', 'statecore', 'controlcore', 'configcore', 'resolvercore', 'capsulecore')
WORKTREES = REPOS + ('distribution',)
EXCLUDED = {'.git', 'build', 'evidence', '__pycache__', '.pytest_cache'}
LIMIT = 8 * 1024 * 1024
class Invalid(ValueError):
    pass

def read_regular(p: Path, limit: int = LIMIT) -> bytes:
    s = p.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_size > limit:
        raise Invalid(f'not a bounded regular file: {p}')
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        if (before.st_dev, before.st_ino) != (s.st_dev, s.st_ino):
            raise Invalid(f'file changed before read: {p}')
        chunks, total = [], 0
        while True:
            b = os.read(fd, min(65536, limit + 1 - total))
            if not b:
                break
            total += len(b)
            if total > limit:
                raise Invalid(f'file exceeds limit: {p}')
            chunks.append(b)
        after = os.fstat(fd)
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise Invalid(f'file changed during read: {p}')
        return b''.join(chunks)
    finally:
        os.close(fd)

def regular_tree(root: Path):
    for repo in WORKTREES:
        base = root / repo
        if base.is_symlink() or not base.is_dir():
            raise Invalid(f'missing ordinary repository: {repo}')
        for parent, ds, fs in os.walk(base, followlinks=False):
            ds[:] = sorted(d for d in ds if d not in EXCLUDED)
            for d in ds:
                if (Path(parent) / d).is_symlink():
                    raise Invalid(f'directory link: {d}')
            for f in sorted(fs):
                p = Path(parent) / f
                if f.endswith('.pyc'):
                    continue
                yield p, read_regular(p)

def source_subject(root: Path) -> str:
    lines = sorted((p.relative_to(root).as_posix(), hashlib.sha256(b).hexdigest()) for p, b in regular_tree(root))
    raw = ''.join(f'{h}  {n}\n' for n, h in lines).encode()
    return hashlib.sha256(b'MISSION-ENGINEERING-SOURCE-v1\n' + raw).hexdigest()

def resolve_ref(root: Path, ref: str) -> tuple[Path, str]:
    if not isinstance(ref, str) or ref.count('#') > 1:
        raise Invalid('invalid reference')
    path, _, symbol = ref.partition('#')
    p = PurePosixPath(path)
    if p.is_absolute() or not p.parts or any(x in ('','..','.') for x in path.split('/')) or '\\' in path:
        raise Invalid(f'unsafe reference: {ref}')
    if p.parts[0] not in WORKTREES:
        raise Invalid(f'reference outside repositories: {ref}')
    target = root
    for part in p.parts:
        target = target / part
        if target.is_symlink():
            raise Invalid(f'linked reference: {ref}')
    content = read_regular(target).decode('utf-8')
    if symbol and not re.search(r'\b' + re.escape(symbol) + r'\b', content, flags=re.I):
        raise Invalid(f'unknown source symbol (lexical check): {ref}')
    return target, content

def inventory(root: Path) -> dict[str, Any]:
    modules = []
    for p, raw in regular_tree(root):
        parts = p.relative_to(root).parts
        if len(parts) != 3 or parts[1] not in ('src', 'runtime', 'app') or p.suffix not in ('.ads', '.adb'):
            continue
        text = raw.decode('utf-8')
        symbols = []
        for n, line in enumerate(text.splitlines(), 1):
            m = re.match(r'\s*(?:overriding\s+)?(?:procedure|function|package(?:\s+body)?)\s+([A-Za-z][A-Za-z0-9_.]*)', line, re.I)
            if m:
                symbols.append({'name': m.group(1), 'line': n})
        deps = sorted(set(re.findall(r'\bwith\s+([A-Za-z][A-Za-z0-9_.]*)\s*;', text, re.I)))
        modules.append({'path': p.relative_to(root).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(),
                        'repository': parts[0], 'layer': parts[1],
                        'verification_boundary': 'non-SPARK-or-boundary' if re.search(r'SPARK_Mode\s*=>\s*Off', text, re.I) else 'SPARK-intent-not-proof',
                        'symbols': symbols, 'with_dependencies': deps,
                        'semantic_analysis': False})
    return {'format': 1, 'scope': 'canonical Ada src/runtime/app; vendor copies excluded',
            'formal_proof': False, 'modules': sorted(modules, key=lambda r: r['path'])}

def api_index(data: dict[str, Any]) -> str:
    lines = ['# Canonical Ada API / 境界索引', '',
             '生成元: assurance/engineering/component-catalog.json。字句索引であり、意味解析・証明・完全な各API仕様ではありません。',
             'src/runtime/appの全canonical Adaファイルを列挙します。vendor重複とtestsは別台帳です。',
             'SPARK-intentはソース上の意図であり、未指定コードや外部依存まで証明済みとは扱いません。', '',
             '|ファイル|層 / 検証境界|宣言/定義（行）|', '|---|---|---|']
    for m in data['modules']:
        symbols = '<br>'.join(f'{x["name"]}:{x["line"]}' for x in m['symbols']) or '(字句抽出対象なし)'
        lines.append(f'|[{m["path"]}](../../../{m["path"]})|{m["layer"]} / {m["verification_boundary"]}|{symbols}|')
    return '\n'.join(lines)+'\n'

def fields(value: Any, names: set[str], what: str) -> None:
    if not isinstance(value,dict) or set(value)!=names:
        raise Invalid(f'{what}: schema mismatch')

def strings(value: Any, what: str, allow_empty: bool = False) -> None:
    if not isinstance(value,list) or (not allow_empty and not value) or any(not isinstance(x,str) or not x for x in value) or len(set(value))!=len(value):
        raise Invalid(f'{what}: expected unique nonempty strings')

def load_json(p: Path) -> Any:
    def unique(pairs):
        out = {}
        for key, val in pairs:
            if key in out:
                raise Invalid(f'duplicate JSON field: {key}')
            out[key] = val
        return out
    return json.loads(read_regular(p).decode(), object_pairs_hook=unique)

def validate(root: Path) -> dict[str, Any]:
    e = root/'assurance/engineering'
    data = load_json(e/'requirements.json')
    if set(data) != {'format', 'qualification', 'requirements'} or data['format'] != 1 or data['qualification'] != 'unqualified':
        raise Invalid('requirement schema or qualification declaration')
    decisions = load_json(e/'adrs.json')
    if set(decisions) != {'format', 'decisions'} or decisions['format'] != 1:
        raise Invalid('ADR registry schema')
    adrs = {}
    for d in decisions['decisions']:
        if set(d) != {'id','path','status','supersedes'} or not re.fullmatch(r'ADR-\d{4}',d['id']) or d['id'] in adrs:
            raise Invalid('duplicate/invalid ADR')
        if d['status'] not in ('proposed-for-review','accepted-by-maintainers','superseded'):
            raise Invalid('invalid ADR status')
        _, text = resolve_ref(root,d['path'])
        for heading in ('## 背景','## 決定','## 代替案','## 影響','## 検証と残る条件'):
            if heading not in text:
                raise Invalid(f'{d["id"]}: missing {heading}')
        adrs[d['id']] = d
    for d in adrs.values():
        for old in d['supersedes']:
            if old not in adrs or old == d['id']:
                raise Invalid('invalid superseded ADR')
    incoming = {k: set() for k in adrs}
    for d in adrs.values():
        for old in d['supersedes']: incoming[old].add(d['id'])
    for key,d in adrs.items():
        if d['status']=='superseded' and not incoming[key]:
            raise Invalid('superseded ADR has no replacement')
        if incoming[key] and d['status']!='superseded':
            raise Invalid('replaced ADR not marked superseded')
        stack=[key];seen=set()
        while stack:
            node=stack.pop()
            for old in adrs[node]['supersedes']:
                if old==key:raise Invalid('cyclic ADR replacement')
                if old not in seen:seen.add(old);stack.append(old)
    ids = set()
    req_fields = {'id','title','shall','status','adr','spec','code','tests','hazards','required_evidence'}
    for r in data['requirements']:
        if set(r) != req_fields or not re.fullmatch(r'REQ-\d{3}',r['id']) or r['id'] in ids:
            raise Invalid('duplicate/invalid requirement or unknown field')
        ids.add(r['id'])
        if r['status'] not in ('implemented-unvalidated','partial-integration','specification-only'):
            raise Invalid(f'{r["id"]}: source cannot declare production qualification')
        if len(r['shall']) < 20 or not r['adr'] or not r['spec'] or not r['required_evidence']:
            raise Invalid(f'{r["id"]}: missing obligation')
        if any(a not in adrs for a in r['adr']):
            raise Invalid(f'{r["id"]}: missing ADR')
        if any(adrs[a]['status']=='superseded' for a in r['adr']):
            raise Invalid('current requirement references superseded ADR')
        if r['status'] == 'implemented-unvalidated' and (not r['code'] or not r['tests']):
            raise Invalid(f'{r["id"]}: implementation needs code and tests')
        for ref in r['spec'] + r['code'] + r['tests']:
            resolve_ref(root, ref)
    hazards = load_json(e/'hazards.json')
    fields(hazards,{'format','hazards'},'hazard catalog')
    if type(hazards['format']) is not int or hazards['format']!=1: raise Invalid('hazard format')
    hids = set()
    for h in hazards['hazards']:
        fields(h,{'id','title','severity','mitigation','residual_risk','requirements','runbook'},'hazard')
        strings(h['requirements'],'hazard requirements')
        if h['severity'] not in ('critical','high','medium','low') or not h['residual_risk']:
            raise Invalid('hazard severity or residual risk missing')
        if h['id'] in hids or not re.fullmatch(r'HAZ-\d{3}', h['id']):
            raise Invalid('duplicate hazard')
        hids.add(h['id'])
        if not h['requirements'] or any(r not in ids for r in h['requirements']):
            raise Invalid(f'{h["id"]}: unresolved mitigation requirement')
        resolve_ref(root,h['runbook'])
    for r in data['requirements']:
        if not r['hazards'] or any(h not in hids for h in r['hazards']):
            raise Invalid(f'{r["id"]}: hazard link missing')
    cases = load_json(e/'fault-cases.json')
    fields(cases,{'format','actual_ada_execution','cases'},'fault catalog')
    if type(cases['format']) is not int or cases['format']!=1 or cases['actual_ada_execution'] is not False:
        raise Invalid('fault catalog cannot attest Ada execution')
    seen = set()
    for c in cases['cases']:
        fields(c,{'id','scenario','requirements','runbook','expected','execution','reference_tests'},'fault case')
        strings(c['requirements'],'fault requirements')
        if c['id'] in seen or not re.fullmatch(r'FAULT-\d{3}',c['id']):
            raise Invalid('duplicate fault case')
        seen.add(c['id'])
        if any(r not in ids for r in c['requirements']):
            raise Invalid('unknown fault case requirement')
        if c['execution'] not in ('not-run','reference-only','linux-probe-only'):
            raise Invalid('fault catalog is not an actual runtime test attestation')
        resolve_ref(root,c['runbook'])
        resolve_ref(root,c['reference_tests'])
    saved = load_json(e/'component-catalog.json')
    actual = inventory(root)
    if read_regular(root/'assurance/docs/engineering/api-index.ja.md').decode()!=api_index(actual):
        raise Invalid('API index stale')
    if saved != actual:
        raise Invalid('component inventory stale; review, regenerate and diff it')
    # Every unit registered as a test main must have an execution tier and arguments.
    test_plan = load_json(e/'test-plan.json')
    fields(test_plan,{'format','ada_tests'},'test plan')
    if type(test_plan['format']) is not int or test_plan['format']!=1: raise Invalid('test plan format')
    owners=load_json(e/'ownership.json')
    fields(owners,{'format','roles','unassigned_is_approved'},'ownership')
    if owners['unassigned_is_approved'] is not False: raise Invalid('unassigned owner is not an approval')
    role_ids=set()
    for role in owners['roles']:
        fields(role,{'role','scope','assigned_people'},'role')
        strings(role['scope'],'role scope');strings(role['assigned_people'],'role people',True)
        if role['role'] in role_ids: raise Invalid('duplicate role')
        role_ids.add(role['role'])
    planned = {r['main'] for r in test_plan['ada_tests']}
    if len(planned) != len(test_plan['ada_tests']):
        raise Invalid('duplicate test main')
    expected = set()
    for repo in REPOS:
        text = read_regular(root/repo/'tests.gpr').decode()
        m = re.search(r'for Main use\s*\((.*?)\);', text, re.S)
        if not m:
            raise Invalid('missing GPR test main list')
        expected |= {f'{repo}/tests/{f}' for f in re.findall(r'"([^"]+\.adb)"',m.group(1))}
    if planned != expected:
        raise Invalid(f'test plan mismatch: missing={sorted(expected-planned)}, extra={sorted(planned-expected)}')
    for t in test_plan['ada_tests']:
        fields(t,{'main','tier','arguments','result','prepare_directories','execution_owner','note'},'test plan entry')
        strings(t['arguments'],'test arguments',True);strings(t['prepare_directories'],'test preparation',True)
        if t['execution_owner'] not in role_ids: raise Invalid('unassigned test execution role')
        _, text = resolve_ref(root,t['main'])
        n = (re.search(r'Argument_Count\s*/=\s*(\d+)', text, re.I) or
             re.search(r'\bExpect\s*\(\s*(?:Ada\.Command_Line\.)?Argument_Count\s*=\s*(\d+)', text, re.I))
        if n and len(t['arguments']) != int(n.group(1)):
            raise Invalid(f'{t["main"]}: wrong argument count in execution plan')
        for arg in t['arguments'] + t.get('prepare_directories',[]):
            if not isinstance(arg,str) or not arg or ('\x00' in arg):
                raise Invalid('invalid argument in test plan')
            relative = arg[6:] if arg.startswith('$TEMP/') else arg
            if '$' in relative or relative.startswith('/') or any(p in ('','..','.') for p in relative.split('/')):
                raise Invalid('unsafe argument in test plan')
        if t['tier'] not in ('unit','isolated-io','host-read-only') or t['result'] != 'not-run':
            raise Invalid('test-plan execution status is not evidence')
    return {'format':1,'checks':'traceability-and-source-inventory','result':'pass',
            'requirements':len(ids),'decisions':len(adrs),'hazards':len(hids),'fault_cases':len(seen),
            'canonical_ada_files':len(actual['modules']),'registered_ada_tests':len(planned),
            'source_subject':source_subject(root),'ada_executed':False,'formal_proof':False,
            'production_approval':False}

def lint(root: Path) -> dict[str, Any]:
    checks=[]
    for p,raw in regular_tree(root):
        if p.suffix=='.py':
            try:
                ast.parse(raw,filename=str(p)); result='pass'; detail=''
            except SyntaxError as exc:
                result='fail'; detail=str(exc)
            checks.append({'path':p.relative_to(root).as_posix(),'kind':'python-syntax','result':result,'detail':detail})
        elif p.suffix=='.sh':
            run=subprocess.run(['/bin/sh','-n',str(p)],stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=10,text=True,
                env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'})
            checks.append({'path':p.relative_to(root).as_posix(),'kind':'shell-syntax',
                'result':'pass' if run.returncode==0 else 'fail','detail':run.stdout})
    for p in sorted((root/'assurance/docs/engineering').rglob('*.md')):
        for ref in re.findall(r'\]\(([^)]+)\)',read_regular(p).decode()):
            if '://' in ref or ref.startswith('#'):continue
            path=ref.split('#',1)[0];destination=(p.parent/path).resolve()
            valid=destination.is_relative_to(root) and destination.is_file()
            checks.append({'path':p.relative_to(root).as_posix(),'kind':'local-document-link',
                'target':ref,'result':'pass' if valid else 'fail'})
    return {'format':1,'layer':'syntax-and-local-links-only','checks':checks,
            'result':'pass' if all(c['result']=='pass' for c in checks) else 'fail',
            'ada_execution':False,'formal_proof':False,'production_approval':False}

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('check','inventory','subject','lint'))
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument('--write',action='store_true')
    a = p.parse_args()
    try:
        root = a.root.resolve(strict=True)
        if a.command == 'lint':
            if a.write: p.error('--write only valid with inventory')
            result=lint(root);print(json.dumps(result,ensure_ascii=False,indent=2))
            return 0 if result['result']=='pass' else 1
        elif a.command == 'check':
            if a.write:
                p.error('--write only valid with inventory')
            print(json.dumps(validate(root),ensure_ascii=False,indent=2))
        elif a.command == 'subject':
            if a.write: p.error('--write only valid with inventory')
            print(source_subject(root))
        else:
            content = json.dumps(inventory(root),ensure_ascii=False,indent=2)+'\n'
            if a.write:
                target = root/'assurance/engineering/component-catalog.json'
                if target.is_symlink():
                    raise Invalid('linked catalog target')
                # Build-time generated data, not durable production state.
                target.write_text(content)
                index=root/'assurance/docs/engineering/api-index.ja.md'
                if index.is_symlink(): raise Invalid('linked API index target')
                index.write_text(api_index(inventory(root)))
            else:
                print(content,end='')
        return 0
    except (OSError,ValueError,KeyError,TypeError,subprocess.TimeoutExpired) as err:
        print(f'engineering check failed: {err}',file=sys.stderr)
        return 1
if __name__ == '__main__':
    raise SystemExit(main())
