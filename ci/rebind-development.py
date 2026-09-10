#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
"""Explicit development-only regeneration of dependent source locks and PUBLIC test fixtures.

No production keys, signatures, downloads, installation or service operations.
On error leave the worktree for review; never roll back human edits automatically.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import shutil
import engineering as eng

BASE=Path(__file__).resolve().parents[2]

def plan() -> list[dict]:
    commands=[
      ('shared-contract',['assurance/ci/refresh-contract.py','--write','--acknowledge-interface-change','--sync-sibling-vendors']),
      ('resolver-profile',['resolvercore/ci/profile.py','--write','--acknowledge-incompatible-change','--sync-pkgcore']),
      ('manager-profile',['controlcore/ci/manager-profile.py','--write','--acknowledge-interface-change']),
      ('public-shared-fixtures',['assurance/ci/regenerate-public-fixtures.py','--public-test-only']),
      ('public-manager-fixtures',['controlcore/ci/generate-test-fixtures.py','--public-test-only']),
      ('source-inventory',['assurance/ci/engineering.py','inventory','--write']),
      ('traceability',['assurance/ci/engineering.py','check']),
      ('resolver-check',['resolvercore/ci/profile.py']),
      ('native-resolver-check',['pkgcore/ci/check-resolver.py']),
      ('manager-check',['controlcore/ci/manager-profile.py']),
    ]
    return [{'name':name,'argv':[sys.executable,'-B',*argv]} for name,argv in commands]+[
      {'name':repo+'-contract','argv':['/bin/sh',repo+'/ci/check-contract.sh'],'cwd':repo}
      for repo in eng.REPOS]

def checked_plan(root: Path) -> list[dict]:
    if root.is_symlink() or not root.is_dir(): raise eng.Invalid('ordinary root required')
    for repo in eng.WORKTREES:
        if (root/repo).is_symlink() or not (root/repo).is_dir(): raise eng.Invalid('seven ordinary repositories and distribution required')
    steps=plan()
    for step in steps:
        relative=step['argv'][2] if step['argv'][0]==sys.executable else step['argv'][1]
        current=root
        for part in Path(relative).parts:
            current=current/part
            if current.is_symlink():raise eng.Invalid('linked tool path')
        eng.read_regular(root/relative)
        if 'cwd' in step:step['argv']=['/bin/sh','ci/check-contract.sh']
    return steps

def authorize_write(write:bool,ack:bool,public:bool,euid:int) -> None:
    if not write:
        if ack or public:raise eng.Invalid('acknowledgements require --write')
        return
    if not ack or not public:raise eng.Invalid('both explicit acknowledgements required')
    if euid==0:raise eng.Invalid('run only as an unprivileged developer in an isolated checkout')

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--acknowledge-incompatible-change',action='store_true')
    parser.add_argument('--public-test-only',action='store_true')
    args=parser.parse_args()
    authorize_write(args.write,args.acknowledge_incompatible_change,args.public_test_only,os.geteuid())
    steps=checked_plan(BASE)
    if not args.write:
        print(json.dumps({'mode':'plan-only','commands':steps,'production_authority':False},indent=2));return 0
    spec=importlib.util.spec_from_file_location('nia_rebind_runner',BASE/'assurance/ci/run-engineering-checks.py')
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    evidence=BASE/'assurance/evidence'
    if evidence.is_symlink():raise eng.Invalid('linked evidence directory')
    evidence.mkdir(exist_ok=True)
    out=Path(tempfile.mkdtemp(prefix='development-rebind-',dir=evidence))
    home=Path(tempfile.mkdtemp(prefix='nia-public-fixture-home-'))
    report={'schema':'org.niaos.development-rebind/v1','production_authority':False,
            'source_before':eng.source_subject(BASE),'started':datetime.now(timezone.utc).isoformat(),
            'commands':[],'result':'incomplete'}
    try:
        env=runner.clean_env(home)
        for step in steps:
            result=runner.run_command(step['argv'],BASE/step.get('cwd','.'),out/(step['name']+'.log'),env,120)
            report['commands'].append(dict(name=step['name'],**result))
            if result['result']!='pass':raise eng.Invalid('stopped after failed step '+step['name'])
        report['result']='development-locks-only-pass'
        return 0
    finally:
        report['source_after']=eng.source_subject(BASE)
        report['ended']=datetime.now(timezone.utc).isoformat()
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        shutil.rmtree(home)
        print(out/'report.json')

if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError) as exc:raise SystemExit(str(exc))
