#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
"""BUILD-TIME only: explicit incompatible shared-source lock refresh.
No deployment, production signing, runtime authorization or proof.
Use on a trusted unprivileged worktree. An interrupted multi-file publication
must fail the normal source-lock checks; it does not authorize old policies.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,stat,tempfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--write',action='store_true');p.add_argument('--acknowledge-interface-change',action='store_true')
p.add_argument('--sync-sibling-vendors',action='store_true')
a=p.parse_args()
if a.write and not a.acknowledge_interface_change:p.error('--write requires --acknowledge-interface-change')
if a.sync_sibling_vendors and not a.write:p.error('--sync-sibling-vendors requires --write')
A=Path(__file__).resolve().parents[1];sha=lambda b:hashlib.sha256(b).hexdigest()
def regular(f):
 s=f.lstat()
 if not stat.S_ISREG(s.st_mode):raise ValueError('non-regular source/target: '+str(f))
def atomic(f,b):
 f.parent.mkdir(parents=True,exist_ok=True)
 if f.exists() or f.is_symlink():regular(f)
 fd,tmp=tempfile.mkstemp(prefix='.contract-source-',dir=f.parent)
 try:
  os.fchmod(fd,0o644)
  with os.fdopen(fd,'wb') as o:o.write(b);o.flush();os.fsync(o.fileno())
  os.replace(tmp,f)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
files=[]
for name in ('src','runtime'):
 d=A/name
 if d.is_symlink() or not d.is_dir():raise ValueError('source directory not ordinary')
 for f in sorted(d.iterdir()):
  regular(f)
  if not re.fullmatch(r'[a-z0-9_]+\.(ads|adb)',f.name):raise ValueError('unexpected shared source '+str(f))
  files.append(f)
for f in (A/'contracts.lock.json',A/'contract-profile.json'):regular(f)
items=sorted((f.relative_to(A).as_posix(),sha(f.read_bytes())) for f in files if f.name!='mc_contract_profile.ads')
manifest=''.join(f'{h}  {n}\n' for n,h in items).encode();profile=sha(b'MISSION-CORE-SHARED-SOURCE-PROFILE-v1\n'+manifest)
print('candidate_shared_profile='+profile)
if not a.write:
 print('source_only_check=true; runtime_or_proof_qualification=false')
 raise SystemExit(0 if (A/'contract-profile.hex').read_text().strip()==profile else 1)
# Check all output parents before any writes; no following source/vendor links.
for d in (A/'app',A/'src',A/'runtime'):
 if d.is_symlink() or not d.is_dir():raise ValueError('unsafe output directory')
vendors=[]
if a.sync_sibling_vendors:
 for repo in ('pkgcore','statecore','controlcore','configcore','resolvercore','capsulecore'):
  d=A.parent/repo/'vendor/contracts'
  for x in (A.parent/repo,A.parent/repo/'vendor',d,d/'src',d/'runtime'):
   if x.is_symlink() or not x.is_dir():raise ValueError('missing/unsafe vendor '+str(x))
  for n in ('src','runtime'):
   for f in (d/n).iterdir():regular(f)
  vendors.append(d)
atomic(A/'contract-profile.source.sha256',manifest);atomic(A/'contract-profile.hex',(profile+'\n').encode())
generated=('''-- SPDX-License-Identifier: BSD-3-Clause
-- Generated from contract-profile.source.sha256; not a signature or a proof.
with MC_Types; use MC_Types;
package MC_Contract_Profile with SPARK_Mode, Pure is
   Fingerprint : constant Digest :=
     ('''+', '.join('16#'+profile[i:i+2]+'#' for i in range(0,64,2))+''');
end MC_Contract_Profile;
''').encode();atomic(A/'src/mc_contract_profile.ads',generated)
meta=json.loads((A/'contract-profile.json').read_text());meta['profile']=profile;atomic(A/'contract-profile.json',(json.dumps(meta,indent=2)+'\n').encode())
items=sorted((f.relative_to(A).as_posix(),sha(f.read_bytes())) for f in files)
manifest=''.join(f'{h}  {n}\n' for n,h in items).encode();atomic(A/'contracts.source.sha256',manifest)
lock=json.loads((A/'contracts.lock.json').read_text());lock.update(bundle_sha256=sha(manifest),runtime_source_profile=profile,files=[dict(path=n,sha256=h) for n,h in items]);atomic(A/'contracts.lock.json',(json.dumps(lock,indent=2)+'\n').encode())
atomic(A/'app/contract_lock.ads',('''-- SPDX-License-Identifier: BSD-3-Clause
package Contract_Lock with SPARK_Mode => Off is
   Count : constant := '''+str(len(items))+''';
   subtype Item_Index is Positive range 1 .. Count;
   function Name (Index : Item_Index) return String;
   function Expected (Index : Item_Index) return String;
end Contract_Lock;
''').encode())
s='-- SPDX-License-Identifier: BSD-3-Clause\npackage body Contract_Lock with SPARK_Mode => Off is\n'
for fn,pos in [('Name',0),('Expected',1)]:
 s+=f'   function {fn} (Index : Item_Index) return String is\n   begin\n      case Index is\n'
 s+=''.join(f'         when {i} => return "{v[pos]}";\n' for i,v in enumerate(items,1));s+=f'      end case;\n   end {fn};\n'
s+='end Contract_Lock;\n';atomic(A/'app/contract_lock.adb',s.encode())
for d in vendors:
 for n in ('src','runtime'):
  for f in (d/n).iterdir():
   if not (A/n/f.name).is_file():f.unlink()
 for f in files:atomic(d/f.relative_to(A),f.read_bytes())
 for name in ('contracts.source.sha256','contracts.lock.json','contract-profile.source.sha256','contract-profile.hex','contract-profile.json'):atomic(d/name,(A/name).read_bytes())
 for name in ('LICENSE','LICENSING.md','LICENSES/MIT-legacy.txt'):
  regular(A/name);atomic(d/name,(A/name).read_bytes())
print('Updated source locks only. Regenerate public test fixtures; independently review and sign any production migration. No proof or production authorization created.')
