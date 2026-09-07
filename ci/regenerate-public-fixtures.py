#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""BUILD/TEST ONLY. Regenerate publicly known synthetic signature fixtures.
No input key, trust-store path, deployment target or real report is accepted.
The deterministic test key material is public, never a production credential.
"""
from pathlib import Path
import argparse,hashlib,json,re,stat
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--public-test-only',action='store_true',required=True)
p.parse_args()
A=Path(__file__).resolve().parents[1]
sha=lambda x:hashlib.sha256(x).digest()
profile=bytes.fromhex((A/'contract-profile.hex').read_text().strip())
if len(profile)!=32:raise ValueError('invalid profile')
for parent in (A/'fixtures',A/'fixtures/stop-v1',A/'fixtures/qualification-v1'):
 if parent.is_symlink() or not parent.is_dir():raise ValueError('unsafe fixture directory')
 for f in parent.iterdir():
  if parent.name in ('stop-v1','qualification-v1') and not stat.S_ISREG(f.lstat().st_mode):raise ValueError('non-regular fixture')
policy=(A/'fixtures/stop-v1/policy.bin').read_bytes()
if len(policy)!=4608 or policy[:8]!=b'MCBARP01' or policy[208]!=3:raise ValueError('unexpected stop fixture layout')
# Deterministic synthetic keys are local build inputs, NOT shipped as private keys.
def key(label):return Ed25519PrivateKey.from_private_bytes(sha(b'PUBLIC-TEST-ONLY:mission-core-distro-foundation:'+label.encode()))
def pub(k):return k.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)
def sign(k,domain,b):return k.sign(len(domain).to_bytes(2,'big')+domain+b)
def hashed(b):b=bytearray(b);b[-32:]=sha(b[:-32]);return bytes(b)
F=A/'fixtures/stop-v1';p=bytearray((F/'policy.bin').read_bytes());p[56:88]=profile
keys={};fk=key('stop-fence')
for i in range(p[208]):
 o=256+i*128;node=bytes(p[o:o+16]);nk=keys.setdefault(node,key('stop-node-'+node.hex()))
 p[o+48:o+80]=pub(nk);p[o+80:o+112]=pub(fk)
p=hashed(p);(F/'policy.bin').write_bytes(p);ph=sha(p)
domain=b'MISSION-CORE-STOP-ACK-v1'
for name in ('node-1','node-2','node-3','fence-1','old-guard-evidence'):
 b=bytearray((F/(name+'.bin')).read_bytes());b[8:40]=ph;b=hashed(b)
 (F/(name+'.bin')).write_bytes(b);k=fk if b[245]==1 else keys[b[104:120]]
 (F/(name+'.sig')).write_bytes(sign(k,domain,b))
state=bytearray((F/'sealed-state.bin').read_bytes());state[8:40]=ph
for i in range(p[208]):
 state[256+i*128+40:256+i*128+72]=sha((F/f'node-{i+1}.bin').read_bytes())
state=hashed(state);(F/'sealed-state.bin').write_bytes(state)
bad=bytearray(p);bad[4500]=1;(F/'policy-reserved.bin').write_bytes(hashed(bad))
bad=bytearray(state);bad[4500]=1;(F/'state-reserved.bin').write_bytes(hashed(bad))
good=(F/'node-1.bin').read_bytes();nk=keys[good[104:120]]
for name,pos,value in [('evidence-reserved.bin',280,1),('evidence-boolean.bin',246,2)]:
 b=bytearray(good);b[pos]=value;b=hashed(b);(F/name).write_bytes(b);(F/(name+'.sig')).write_bytes(sign(nk,domain,b))
(F/'truncated-evidence.bin').write_bytes(good[:-1]);(F/'wrong-domain.sig').write_bytes(sign(nk,b'MISSION-CORE-NOT-STOP-v1',good));(F/'wrong-role.sig').write_bytes(sign(fk,domain,good))
v=json.loads((F/'vectors.json').read_text());v.update(profile=profile.hex(),edition='distro-foundation');v['files']={f.name:sha(f.read_bytes()).hex() for f in sorted(F.iterdir()) if f.suffix in ('.bin','.sig')};(F/'vectors.json').write_text(json.dumps(v,indent=2)+'\n')
Q=A/'fixtures/qualification-v1';Q.mkdir(exist_ok=True)
roles=['builder','reviewer','operator'];qkeys=[key('qualification-'+r) for r in roles]
for r,k in zip(roles,qkeys):(Q/(r+'.pub')).write_bytes(pub(k))
s=(A/'src/mc_release.ads').read_text();items=[x.strip() for x in re.search(r'type Evidence_Item is\s*\((.*?)\);',s,re.S).group(1).split(',')]
for i,name in enumerate(items):
 r=1 if name=='Independent_Review' else 2 if name=='Operational_Approval' else 0;k=qkeys[r]
 b=bytearray(320);b[:8]=b'MCQUAL01';b[8]=i;b[9]=2;b[16:48]=pub(k)
 for offset,data in [(48,b'\x01'*32),(80,b'\x02'*32),(112,profile),(144,b'\x03'*32),(176,sha(b'SYNTHETIC-NOT-A-QUALIFICATION-REPORT:'+name.encode())),(208,b'\x04'*32)]:b[offset:offset+32]=data
 for offset,n in [(240,10),(248,1000),(256,1)]:b[offset:offset+8]=n.to_bytes(8,'big')
 b=hashed(b);(Q/(name.lower()+'.bin')).write_bytes(b);(Q/(name.lower()+'.sig')).write_bytes(sign(k,b'MISSION-CORE-QUALIFICATION-v1',b))
qmeta={'format':1,'artificial_fixture':True,'production_qualification':False,'private_keys_included':False,'contract_profile':profile.hex(),'subjects':{'source':'01'*32,'binary':'02'*32,'platform':'03'*32,'policy':'04'*32,'trust_epoch':1},'valid_now':100,'expires_exclusive':1000,'items':items,'authorities':dict(zip(roles,[pub(k).hex() for k in qkeys])),'files':{f.name:sha(f.read_bytes()).hex() for f in sorted(Q.iterdir()) if f.suffix in ('.bin','.sig','.pub')}}
(Q/'vectors.json').write_text(json.dumps(qmeta,indent=2)+'\n');(Q/'README.ja.md').write_text('''# 人工的な資格証拠fixture

全Passedの値は署名・形式・対象一致の試験用です。本ソースや実クラスタの合格証拠ではありません。
source=01*32、binary=02*32等の人工値です。実ビルド・GNATproveは未実行です。
公開鍵は本番trust storeへ登録しないでください。秘密鍵ファイルは収録しません。
''')
print('Synthetic fixtures regenerated; production_qualified=false; never deploy these public test keys.')
