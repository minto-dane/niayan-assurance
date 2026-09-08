#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Cross-repository structural/traceability audit; not semantic proof or release approval."""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
import engineering as eng
LEVELS={'runtime-unvalidated','sdk-unvalidated','restored-model','tooling','not-implemented','not-promised'}
CAP_FIELDS={'id','name','level','code','implemented_scope','remaining'}

def capabilities(root:Path):
    data=eng.load_json(root/'assurance/engineering/capabilities.json')
    eng.fields(data,{'format','production_qualified','ada_executed','capabilities'},'capabilities')
    if type(data['format']) is not int or data['format']!=1 or data['production_qualified'] is not False or data['ada_executed'] is not False:
        raise eng.Invalid('capability source cannot confer qualification')
    seen=set()
    for row in data['capabilities']:
        eng.fields(row,CAP_FIELDS,'capability')
        if not re.fullmatch(r'CAP-\d{3}',row['id']) or row['id'] in seen:raise eng.Invalid('duplicate or invalid capability')
        seen.add(row['id'])
        if row['level'] not in LEVELS:raise eng.Invalid('unknown or inflated implementation status')
        if not row['name'] or not row['implemented_scope'] or not row['remaining']:raise eng.Invalid('scope or residual boundary absent')
        eng.strings(row['code'],'capability code',True)
        if row['level'] in {'runtime-unvalidated','sdk-unvalidated','restored-model','tooling'} and not row['code']:
            raise eng.Invalid('implementation claim without code')
        if row['level'] in {'not-implemented','not-promised'} and row['code']:
            raise eng.Invalid('ambiguous implementation/no-implementation claim')
        for ref in row['code']:eng.resolve_ref(root,ref)
    return data

def lineage(root:Path):
    # The restoration record is immutable history. Successors are explicit,
    # exact-byte amendments, not edits to the recorded original digest.
    data=eng.load_json(root/'assurance/engineering/lineage-merge.json');seen=set()
    changes=eng.load_json(root/'assurance/engineering/lineage-amendments.json')
    eng.fields(changes,{'format','production_qualification','independent_review','amendments'},'lineage amendments')
    if (type(changes['format']) is not int or changes['format']!=1
        or changes['production_qualification'] is not False
        or changes['independent_review']!='pending'):
        raise eng.Invalid('lineage amendment is not independent approval')
    if data['production_qualification'] is not False or data['ada_compile']!='not-run':
        raise eng.Invalid('lineage is not qualification')
    if not isinstance(changes['amendments'],list):raise eng.Invalid('amendment list required')
    current={row['path']:row['sha256'] for row in data['restored']}
    amended=set()
    for row in changes['amendments']:
        eng.fields(row,{'path','from_sha256','to_sha256','adr','scope','validation'},'lineage amendment')
        for field in ('from_sha256','to_sha256'):
            if not isinstance(row[field],str) or not re.fullmatch(r'[0-9a-f]{64}',row[field]):
                raise eng.Invalid('amendment digest syntax')
        path=row['path']
        if (path not in current or path in amended or current[path]!=row['from_sha256']
            or row['from_sha256']==row['to_sha256']):
            raise eng.Invalid('amendment must identify a unique exact original')
        if (not isinstance(row['scope'],str) or not row['scope'].strip()
            or row['validation'] not in ('source-inspected; ada-not-run; independent-review-pending',
                'source-inspected; native-validation-recorded-separately; independent-review-pending')
            or not isinstance(row['adr'],str)
            or not re.fullmatch(r'assurance/docs/engineering/adr/ADR-[0-9]{4}\.ja\.md',row['adr'])):
            raise eng.Invalid('amendment scope/review reference invalid')
        eng.resolve_ref(root,row['adr'])
        current[path]=row['to_sha256'];amended.add(path)
    for group in ('restored','retained_newer_conflicts'):
        for row in data[group]:
            if row['path'] in seen:raise eng.Invalid('duplicate lineage path')
            seen.add(row['path']);p,_=eng.resolve_ref(root,row['path'])
            if group=='restored' and hashlib.sha256(eng.read_regular(p)).hexdigest()!=current[row['path']]:
                raise eng.Invalid('restored code changed without exact lineage amendment: '+row['path'])
    for p in data['restored_docs']:eng.resolve_ref(root,p)
    return {'restored_files':len(data['restored']),'kept_newer_files':len(data['retained_newer_conflicts']),
            'restored_canonical_ada':sum('/tests/' not in x['path'] for x in data['restored']),
            'amended_restored_files':len(amended),'independent_review':'pending',
            'source_archive':data['source_archive'],'source_sha256':data['source_sha256']}

def packaging(root:Path):
    checks=[]
    for repo in eng.REPOS:
        gpr=eng.read_regular(root/repo/(repo+'.gpr')).decode()
        manifest=eng.load_json(root/repo/'packaging/nia/artifact.json')
        eng.fields(manifest,{'schema','component','transport','origin','sources','executables',
          'dependency_derivation','dependency_set_qualified','automatic_hooks','native_database_writer','production_qualified'},'first-party artifact')
        if (manifest['schema']!='org.niaos.firstparty-artifact/v1' or manifest['component']!=repo
            or manifest['transport']!='deb' or manifest['origin']!='nia-firstparty'
            or manifest['sources']!=repo+'.gpr' or manifest['dependency_set_qualified'] is not False
            or manifest['production_qualified'] is not False or manifest['native_database_writer'] is not False
            or manifest['automatic_hooks']!=[]):raise eng.Invalid('unqualified artifact cannot confer authority')
        match=re.search(r'for Main use\s*\((.*?)\);',gpr,re.S)
        if not match:raise eng.Invalid('missing application main catalog')
        expected=set(re.findall(r'"([a-z0-9_]+)\.adb"',match.group(1)))
        declared=set();destinations=set()
        for row in manifest['executables']:
            eng.fields(row,{'source','destination','mode'},'executable')
            name=row['source'].removeprefix('build/bin/')
            target='usr/bin/nia' if repo=='controlcore' and name=='nia' else 'usr/libexec/nia/'+name
            if (name in declared or row['source']!='build/bin/'+name or row['destination']!=target
                or target in destinations or row['mode']!='0755'):raise eng.Invalid('artifact executable scope')
            declared.add(name);destinations.add(target);checks.append(repo+'/'+name)
        if declared!=expected:raise eng.Invalid('artifact inventory differs from GPR application mains: '+repo)
    return {'covered_application_mains':checks,'transport':'deb','package_build_executed':False,
            'native_dependencies_qualified':False,'legacy_rpm_recipes_active':False}

def documentation(root:Path):
    docs=[];links=[]
    for p,raw in eng.regular_tree(root):
        if p.suffix.lower() not in ('.md','.rst'):continue
        text=raw.decode('utf-8');name=p.relative_to(root).as_posix()
        mode=('active-nia-product-specification' if name.startswith(('distribution/docs/','assurance/docs/nia/'))
              else 'archived-not-product' if '/history/' in name
              else 'component-contract-check-nia-product-overlay')
        docs.append({'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'scope':mode,
                     'semantic_review':'selected-design-boundaries; full semantic equivalence not established'})
        for ref in re.findall(r'\]\(([^)]+)\)',text):
            if '://' in ref or ref.startswith(('#','mailto:')):continue
            path=ref.split('#',1)[0]
            # No external lookups, Markdown headings are not claimed to be checked.
            dest=(p.parent/path).resolve()
            valid=dest.is_relative_to(root) and dest.is_file()
            if valid:
                cur=p.parent/path
                valid=not cur.is_symlink()
            links.append({'source':name,'target':ref,'result':'pass' if valid else 'fail'})
    return {'documents':docs,'local_links':links,'failed_links':[l for l in links if l['result']!='pass']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);a=p.parse_args()
    try:
        root=a.root.resolve(strict=True)
        cap=capabilities(root);lin=lineage(root);pkg=packaging(root);doc=documentation(root)
        if doc['failed_links']:raise eng.Invalid('broken local documentation links: '+json.dumps(doc['failed_links'],ensure_ascii=False))
        result={'format':1,'result':'pass-source-structure-only','production_qualified':False,'formal_proof':False,
                'ada_execution':False,'capabilities':len(cap['capabilities']),'lineage':lin,
                'packaging':pkg,'documentation':doc,'source_subject':eng.source_subject(root)}
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (eng.Invalid,OSError,ValueError,KeyError,TypeError) as e:
        print('unified audit failed: '+str(e),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
