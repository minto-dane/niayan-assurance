#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Source-product coherence check, not binary verification or permission to run."""
from pathlib import Path
import argparse,json,re,sys
import importlib.util
import engineering as eng
import importlib.util

def audit(root):
    sys.path.insert(0,str(root/'distribution/tools'))
    from nia_policy import check_profile
    from nia_layout import check_layout
    from nia_xfs import check_policy as check_xfs_policy
    from nia_common import parse_json
    load=lambda p:parse_json(eng.read_regular(root/p))
    prof=root/'distribution/profiles'
    if sorted(p.name for p in prof.iterdir())!=['nia-os.json']:
        raise eng.Invalid('exactly one active product profile required')
    for p in prof.iterdir():
        if p.is_symlink() or not p.is_file():raise eng.Invalid('invalid active profile file')
    profile=load('distribution/profiles/nia-os.json');check_profile(profile)
    layout=load('distribution/contracts/state-domains.json');check_layout(layout)
    check_xfs_policy(load('distribution/contracts/xfs-policy.json'))
    text=eng.read_regular(root/'distribution/rootfs/usr/lib/os-release').decode()
    pairs={}
    for row in text.splitlines():
        if not row or row.startswith('#'):continue
        k,v=row.split('=',1)
        if k in pairs:raise eng.Invalid('duplicate os-release key')
        pairs[k]=v.strip('"')
    if pairs.get('ID')!='nia' or pairs.get('ID_LIKE')!='debian' or pairs.get('NAME')!='Nia OS':raise eng.Invalid('product identity mismatch')
    index=load('distribution/contracts/implementation-map.json')
    if index['production_qualified'] is not False:raise eng.Invalid('inflated implementation evidence')
    for row in index['entries']:
        for path in row['paths']:
            target=root/path
            if target.is_symlink() or not target.exists():raise eng.Invalid('missing implementation boundary: '+path)
    release=load('distribution/contracts/release-gates.json')
    # Use registered exact gate set, not the truthiness of supplied evidence.
    from nia_policy import GATES
    gates=release.get('required_gates',release.get('gates'))
    if isinstance(gates,list) and gates and isinstance(gates[0],dict):gates=[g['id'] for g in gates]
    if gates!=list(GATES) or release['production_qualified'] is not False:raise eng.Invalid('release requirements drift')
    spec=importlib.util.spec_from_file_location('nia_unified_audit',root/'assurance/ci/unified-audit.py')
    ua=importlib.util.module_from_spec(spec);spec.loader.exec_module(ua)
    packaging=ua.packaging(root)
    import configparser
    unit=configparser.ConfigParser(interpolation=None);unit.optionxform=str
    unit.read_string(eng.read_regular(root/'distribution/rootfs/usr/lib/systemd/system/nia-host-observer.service').decode())
    if unit['Service'].get('ExecStart')!='/usr/libexec/nia/hostctl inspect' or 'Install' in unit:raise eng.Invalid('observer deployment path/activation drift')
    if unit['Service'].get('NoNewPrivileges')!='yes' or unit['Service'].get('DynamicUser')!='yes':raise eng.Invalid('observer privilege regression')
    # Health services are non-repair definitions, not an implicit enrollment path.
    checks = {
        'nia-xfs-observe@.service': '/usr/sbin/xfs_healer --no-autofsck --everything %f',
        'nia-xfs-scrub@.service': '/usr/sbin/xfs_scrub -n -b -k %f',
    }
    for name, command in checks.items():
        cfg=configparser.ConfigParser(interpolation=None);cfg.optionxform=str
        cfg.read_string(eng.read_regular(root/'distribution/rootfs/usr/lib/systemd/system'/name).decode())
        if cfg['Service'].get('ExecStart')!=command or 'Install' in cfg:
            raise eng.Invalid('implicit/unknown filesystem operation in unit: '+name)
        if cfg['Service'].get('NoNewPrivileges')!='yes' or cfg['Service'].get('LimitCORE')!='0':
            raise eng.Invalid('XFS service safety constraints removed')
    old=root/'distribution/history/leap16' 
    if not (old/'ARCHIVED.ja.md').is_file():raise eng.Invalid('old product history lost')
    if not (root/'distribution/docs/continuation.ja.md').is_file():raise eng.Invalid('missing noncompletion scope')
    return {'schema':'org.niaos.product-audit/v1','result':'source-coherence-pass',
      'product':'Nia OS','upstream':'debian-forky','transport':'deb',
      'host_package_authority':'nia','native_db_handoff_required':False,
      'profiles':1,'state_domains':len(layout['entries']),'release_gates':len(GATES),
      'packaging':packaging,'execution_permit':False,'bootable_image':False,'formal_proof':False,
      'production_qualified':False,'source_subject':eng.source_subject(root)}

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);args=a.parse_args()
    try:print(json.dumps(audit(args.root.resolve()),ensure_ascii=False,indent=2));return 0
    except (ValueError,OSError,KeyError,TypeError) as exc:print('Nia product audit refused: '+str(exc),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
