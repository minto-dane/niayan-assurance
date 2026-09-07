#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run source checks or the explicitly registered Ada checks in a private workspace.

This is a development tool, not a production qualification authority. No package
installation, downloads, service changes or hardware fault injection are performed.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import engineering as eng

MAX_LOG = 16 * 1024 * 1024

def clean_env(home: Path) -> dict[str,str]:
    path = os.environ.get('PATH', '/usr/bin:/bin')
    if any(not x or not Path(x).is_absolute() for x in path.split(':')):
        raise eng.Invalid('PATH must contain only nonempty absolute directories')
    # Do not pass proxy credentials, cloud keys, signing credentials or overrides
    # such as LD_PRELOAD, GPR_PROJECT_PATH, PYTHONPATH, BASH_ENV to test children.
    return {'PATH':path,'HOME':str(home),'TMPDIR':str(home),'LANG':'C.UTF-8',
            'LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'}

def run_command(argv: list[str], cwd: Path, log: Path, env: dict[str,str], timeout: int) -> dict:
    start = time.monotonic()
    record = {'argv':argv, 'cwd':str(cwd), 'result':'not-run', 'returncode':None,
              'leader_reaped':False, 'external_effects_checked':False}
    child = None
    owns_pid = False
    sel = None
    try:
        if signal.getsignal(signal.SIGCHLD) is not signal.SIG_DFL and signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL:
            raise eng.Invalid('test runner requires exclusive child ownership and default SIGCHLD')
        with log.open('xb') as out:
            try:
                child = subprocess.Popen(argv,cwd=cwd,env=env,stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
                owns_pid = True
            except FileNotFoundError:
                record.update(result='not-run',reason='tool-or-executable-unavailable')
                return record
            sel = selectors.DefaultSelector()
            sel.register(child.stdout,selectors.EVENT_READ)
            total = 0
            while True:
                # WNOWAIT deliberately retains the leader until group cleanup.
                # Popen.poll()/wait() here would recycle its PID before killpg.
                observed = os.waitid(os.P_PID,child.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
                if observed is not None and not sel.get_map(): break
                if time.monotonic()-start > timeout:
                    record.update(result='timeout',reason='time-limit')
                    break
                events = sel.select(timeout=0.05) if sel.get_map() else []
                if not sel.get_map() and observed is None: time.sleep(0.01)
                for key,_ in events:
                    block = os.read(key.fileobj.fileno(),65536)
                    if not block:
                        sel.unregister(key.fileobj)
                        continue
                    remaining = MAX_LOG-total
                    out.write(block[:remaining]); total += min(len(block),remaining)
                    if len(block)>remaining:
                        record.update(result='fail',reason='log-size-limit')
                        break
                if record['result']=='fail': break
            sel.close(); sel=None
            # Group signals occur ONLY while its leader remains our unreaped child.
            # This is not confinement of a test that deliberately changes session.
            try: os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            rc=child.wait(timeout=5)
            owns_pid=False
            record.update(returncode=rc,leader_reaped=True,log_bytes=total)
            if record['result']=='not-run': record['result']='pass' if rc==0 else 'fail'
    except ChildProcessError:
        owns_pid=False
        record.update(result='fail',reason='exclusive-reaper-ownership-lost')
    except subprocess.TimeoutExpired:
        record.update(result='timeout',reason='leader-not-reaped-after-cleanup')
    except OSError as exc:
        record.update(result='fail',reason=f'os-error-{exc.errno}')
    finally:
        if sel is not None: sel.close()
        if child is not None and owns_pid:
            # Do not signal a PID after child.wait() or any external reap.
            try:
                pending=os.waitid(os.P_PID,child.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
                try: os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError: pass
                child.wait(timeout=5)
                record['leader_reaped']=True
            except (ChildProcessError,subprocess.TimeoutExpired,OSError):
                record.update(result='fail',reason='cleanup-incomplete-or-reaper-lost')
        if child is not None and child.stdout is not None: child.stdout.close()
        record['seconds'] = round(time.monotonic()-start,3)
        if log.exists(): record['log_sha256']=hashlib.sha256(eng.read_regular(log,MAX_LOG)).hexdigest()
    return record

def expand_test_args(test: dict, temp: Path) -> list[str]:
    def expand(v: str) -> str:
        if v.startswith('$TEMP/'):
            tail = v[6:]
            if not tail or '..' in Path(tail).parts or Path(tail).is_absolute():
                raise eng.Invalid('unsafe temporary test argument')
            return str(temp/tail)
        if '$' in v or Path(v).is_absolute() or '..' in Path(v).parts:
            raise eng.Invalid('unsupported test argument')
        return v
    # Registered temporary arguments are private directories, not arbitrary files.
    for value in test['arguments']+test.get('prepare_directories',[]):
        if value.startswith('$TEMP/'):
            Path(expand(value)).mkdir(mode=0o700,parents=True,exist_ok=True)
    return [expand(v) for v in test['arguments']]

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument('--mode',choices=['source','build','proof'],default='source')
    p.add_argument('--include-host-observers',action='store_true')
    p.add_argument('--timeout',type=int,default=600)
    a=p.parse_args()
    if not 5<=a.timeout<=86400: p.error('timeout must be 5..86400 seconds')
    if a.mode!='source' and os.geteuid()==0:
        p.error('build/proof/test execution must be an unprivileged isolated user')
    root=a.root.resolve(strict=True)
    ev=root/'assurance/evidence'
    if ev.is_symlink(): raise eng.Invalid('linked evidence directory')
    ev.mkdir(exist_ok=True)
    output=Path(tempfile.mkdtemp(prefix='engineering-',dir=ev))
    temporary=Path(tempfile.mkdtemp(prefix='mission-engineering-tests-'))
    checks=[]; code=1
    report={'format':1,'mode':a.mode,'created_utc':datetime.now(timezone.utc).isoformat(),
            'production_approval':False,'ada_execution':'not-run','formal_proof':'not-run',
            'temporary_io_tree':str(temporary),'checks':checks}
    try:
        env=clean_env(temporary)
        report['environment']={'python':sys.version,'kernel':platform.release(),'architecture':platform.machine(),
            'gprbuild':shutil.which('gprbuild',path=env['PATH']), 'gnatprove':shutil.which('gnatprove',path=env['PATH'])}
        before=eng.source_subject(root); report['source_subject_before']=before
        val=eng.validate(root)
        (output/'traceability.json').write_text(json.dumps(val,ensure_ascii=False,indent=2)+'\n')
        checks.append({'name':'traceability','result':'pass','layer':'source'})
        def invoke(name,argv,cwd,layer):
            r=run_command(argv,cwd,output/(name+'.log'),env,a.timeout)
            r.update(name=name,layer=layer);checks.append(r);return r['result']=='pass'
        for tool in ('gprbuild','gnatprove'):
            if shutil.which(tool,path=env['PATH']):
                invoke(tool+'-version',[tool,'--version'],root,'tool-identification')
        source_ok=invoke('engineering-unittests',[sys.executable,'-B','-m','unittest','discover',
             '-s','assurance/tests/engineering','-p','test_*.py','-v'],root,'source-and-reference')
        source_ok=invoke('manager-reference-tests',[sys.executable,'-B','-m','unittest','discover',
             '-s','controlcore/tests/reference','-p','test_*.py','-v'],root,'source-and-reference') and source_ok
        source_ok=invoke('configuration-reference-tests',[sys.executable,'-B','-m','unittest','discover',
             '-s','configcore/tests','-p','test_*.py','-v'],root,'reference-and-limited-native-probe') and source_ok
        source_ok=invoke('resolution-reference-tests',[sys.executable,'-B','-m','unittest','discover',
             '-s','resolvercore/tests','-p','test_*.py','-v'],root,'reference-and-untrusted-proposal-tool-tests') and source_ok
        source_ok=invoke('cohort-recovery-tests',[sys.executable,'-B','-m','unittest','discover',
             '-s','assurance/tests_py','-p','test_*.py','-v'],root,'actual-nonprivileged-cryptography-and-io') and source_ok
        source_ok=invoke('capsule-policy-tree-tests',[sys.executable,'-B','-m','unittest','discover',
             '-s','capsulecore/tests_py','-p','test_*.py','-v'],root,'reference-and-actual-candidate-tree-io') and source_ok
        source_ok=invoke('resolver-source-profile',[sys.executable,'ci/profile.py'],root/'resolvercore','source') and source_ok
        source_ok=invoke('resolver-neutral-boundary',[sys.executable,'ci/check-neutral.py'],root/'resolvercore','source') and source_ok
        source_ok=invoke('native-resolver-lock',[sys.executable,'ci/check-resolver.py'],root/'pkgcore','source') and source_ok
        source_ok=invoke('distribution-tool-tests',[sys.executable,'-B','-m','unittest','discover',
             '-s','distribution/tests','-p','test_*.py','-v'],root,'actual-build-tool-tests') and source_ok
        source_ok=invoke('nia-product-audit',[sys.executable,'-B','assurance/ci/nia-product-audit.py'],root,'source-product-coherence') and source_ok
        source_ok=invoke('unified-architecture-audit',[sys.executable,'-B','assurance/ci/unified-audit.py'],root,'source') and source_ok
        source_ok=invoke('syntax-and-doc-links',[sys.executable,'-B','assurance/ci/engineering.py','lint'],root,'source') and source_ok
        for repo in eng.REPOS:
            source_ok=invoke(repo+'-contract',['/bin/sh','ci/check-contract.sh'],root/repo,'source') and source_ok
        source_ok=invoke('manager-implementation-profile',[sys.executable,'ci/manager-profile.py'],root/'controlcore','source') and source_ok
        if not source_ok: raise eng.Invalid('source checks failed; build/proof not attempted')
        if a.mode=='build':
            available=shutil.which('gprbuild',path=env['PATH']) is not None
            report['ada_execution']='requested-not-completed'
            for repo in eng.REPOS:
                if not available:
                    checks.append({'name':repo+'-ada-build','result':'not-run','layer':'ada-build','reason':'gprbuild unavailable'})
                    continue
                compiled=invoke(repo+'-compile-all',['make','compile-all'],root/repo,'ada-build')
                built=invoke(repo+'-tests-build',['make','test-build'],root/repo,'ada-build') if compiled else False
                if not built: continue
                plan=eng.load_json(root/'assurance/engineering/test-plan.json')['ada_tests']
                for test in plan:
                    if not test['main'].startswith(repo+'/'): continue
                    stem=Path(test['main']).stem
                    if test['tier']=='host-read-only' and not a.include_host_observers:
                        checks.append({'name':stem,'result':'not-run','layer':'ada-host-observation','reason':'not opted in'})
                        continue
                    case=Path(tempfile.mkdtemp(prefix=stem+'-',dir=temporary))
                    args=expand_test_args(test,case)
                    invoke(repo+'-'+stem,[str(root/repo/'build/test-bin'/stem),*args],root/repo,'ada-'+test['tier'])
            if available and all(c['result']=='pass' for c in checks): report['ada_execution']='all-registered-tests-pass'
        elif a.mode=='proof':
            if shutil.which('gnatprove',path=env['PATH']) is None:
                checks.append({'name':'gnatprove','result':'not-run','layer':'proof','reason':'GNATprove unavailable'})
            else:
                for repo in eng.REPOS:
                    invoke(repo+'-flow',['make','flow'],root/repo,'proof')
                    invoke(repo+'-prove',['make','prove'],root/repo,'proof')
                report['formal_proof']='commands-passed-review-proof-boundary' if all(c['result']=='pass' for c in checks) else 'failed-or-incomplete'
        after=eng.source_subject(root); report['source_subject_after']=after
        if before!=after: raise eng.Invalid('sources changed while checks were running')
        code=0 if all(c['result']=='pass' for c in checks) else 1
        report['result']='pass-for-requested-layer-only' if code==0 else 'incomplete-or-failed'
    except (eng.Invalid,OSError,ValueError,KeyError) as exc:
        report.update(result='fail',error=str(exc))
    finally:
        # Never include test-generated private keys in a distribution. Keep only
        # hashes/counts in logs; the caller can deliberately run direct IO tests
        # in a separate isolated environment when forensic retention is needed.
        shutil.rmtree(temporary)
        report['temporary_io_tree_removed']=True
        report['ended_utc']=datetime.now(timezone.utc).isoformat()
        (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        manifest=''.join(hashlib.sha256(eng.read_regular(f,MAX_LOG)).hexdigest()+'  '+f.name+'\n' for f in sorted(output.iterdir()))
        (output/'evidence-manifest.sha256').write_text(manifest)
    print(output/'report.json')
    return code
if __name__=='__main__':
    raise SystemExit(main())
