#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Authenticated recovery COHORT reconstruction into a separate private candidate.
Never repairs a live root, resets history, restores trust floors or executes code.
The pinned anchor/trust policy must arrive through an independent rescue channel.
This non-privileged Python tool is NOT the formally verified recovery executor.
"""
from __future__ import annotations
import argparse,contextlib,hashlib,json,os,re,stat,sys,time
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from recovery_io import (Directory,Invalid,LIMIT,sha,canonical,decode,fields,integer,digest,
                         ident,relative,snapshot,write_all,argument_file)
CHUNK=65536
MAX_CHUNKS=65536
MAX_OBJECTS=16384
MAX_TOTAL=CHUNK*MAX_CHUNKS
DOMAIN=b'NIA-RECOVERY-ANCHOR-v1\0'
KINDS={'managed-file','catalog','checkpoint','journal','audit'}
class Incomplete(Invalid):pass

def validate_xattrs(attrs):
    if not isinstance(attrs,list) or len(attrs)>256:raise Invalid('xattr count')
    names=[];total=0
    for a in attrs:
        fields(a,'name value')
        if not isinstance(a['name'],str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,255}',a['name']):raise Invalid('xattr name')
        if not isinstance(a['value'],str) or len(a['value'])%2 or not re.fullmatch(r'[0-9a-f]*',a['value']):raise Invalid('xattr value')
        total+=len(a['value'])//2
        if total>131072:raise Invalid('xattr bytes')
        names.append(a['name'])
    if names!=sorted(set(names)):raise Invalid('duplicate/unsorted xattrs')

def read_xattrs(fd):
    names=sorted(os.listxattr(fd));out=[];total=0
    if len(names)>256:raise Invalid('xattr count')
    for n in names:
        b=os.getxattr(fd,n);total+=len(b)
        if total>131072:raise Invalid('xattr bytes')
        out.append({'name':n,'value':b.hex()})
    if names!=sorted(os.listxattr(fd)):raise Invalid('xattr set changed')
    validate_xattrs(out);return out

def closed_inventory(root):
    # A cohort is an explicitly closed source directory, not an arbitrary /.
    # Directory nodes are inferred from file paths; unlisted empty dirs count as
    # drift too. Special files/links are observed but never followed.
    files=[];directories=[];count=0
    def walk(fd,prefix,depth):
        nonlocal count
        if depth>32:raise Invalid('inventory depth')
        before=os.fstat(fd);names=sorted(os.listdir(fd))
        for name in names:
            count+=1
            if count>2*MAX_OBJECTS:raise Invalid('inventory count')
            path=relative(prefix+name);s=os.stat(name,dir_fd=fd,follow_symlinks=False)
            if stat.S_ISDIR(s.st_mode):
                p,n=root.parent(path);child=-1
                try:
                    child=os.open(n,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=p)
                    from recovery_io import mountid
                    if snapshot(s)!=snapshot(os.fstat(child)) or mountid(child)!=root.mount:raise Invalid('inventory race/mount')
                    directories.append(path);walk(child,path+'/',depth+1)
                finally:
                    if child>=0:os.close(child)
                    os.close(p)
            else:files.append(path)
        if names!=sorted(os.listdir(fd)) or snapshot(before)!=snapshot(os.fstat(fd)):raise Invalid('inventory changed')
    walk(root.fd,'',0);return sorted(files),sorted(directories)

def expected_directories(m):
    return [d['path'] for d in m['directories']]

def directory_attributes(root,path=None):
    fd=parent=-1
    try:
        if path is None:fd=os.dup(root.fd)
        else:
            parent,name=root.parent(path)
            fd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
        from recovery_io import mountid
        st=os.fstat(fd)
        if st.st_dev!=root.dev or mountid(fd)!=root.mount:raise Invalid('directory mount changed')
        attrs=read_xattrs(fd)
        if snapshot(st)!=snapshot(os.fstat(fd)):raise Invalid('directory metadata changed')
        return {'mode':st.st_mode&0o7777,'uid':st.st_uid,'gid':st.st_gid,'xattrs':attrs}
    finally:
        if fd>=0:os.close(fd)
        if parent>=0:os.close(parent)

def validate_directory_attributes(d):
    fields(d,'mode uid gid xattrs')
    integer(d['mode'],0,0o7777);integer(d['uid'],0,2**32-1);integer(d['gid'],0,2**32-1)
    validate_xattrs(d['xattrs'])

def validate_manifest(m):
    fields(m,'format node cohort generation trust_epoch catalog_path checkpoint_path pending root_attributes directories objects')
    if m['format']!='nia-recovery-manifest-v1':raise Invalid('manifest version')
    ident(m['node']);digest(m['cohort']);integer(m['generation'],1);integer(m['trust_epoch'],1)
    relative(m['catalog_path']);relative(m['checkpoint_path'])
    if not isinstance(m['pending'],list) or len(m['pending'])>4096 or any(not isinstance(x,str) for x in m['pending']) or m['pending']!=sorted(set(m['pending'])):raise Invalid('pending set')
    for x in m['pending']:ident(x)
    if not isinstance(m['objects'],list) or not 1<=len(m['objects'])<=MAX_OBJECTS:raise Invalid('object count')
    validate_directory_attributes(m['root_attributes'])
    if not isinstance(m['directories'],list) or len(m['directories'])>MAX_OBJECTS:raise Invalid('directory count')
    dirs=[]
    for d in m['directories']:
        fields(d,'path attributes');dirs.append(relative(d['path']));validate_directory_attributes(d['attributes'])
    if dirs!=sorted(set(dirs)):raise Invalid('duplicate/unsorted directories')
    objects={};total=chunks=0
    for i in m['objects']:
        fields(i,'path kind mode uid gid xattrs size sha256 chunks');p=relative(i['path'])
        if p in objects or not isinstance(i['kind'],str) or i['kind'] not in KINDS:raise Invalid('duplicate path/state class')
        integer(i['mode'],0,0o777);integer(i['uid'],0,2**32-1);integer(i['gid'],0,2**32-1)
        validate_xattrs(i['xattrs']);integer(i['size'],0,MAX_TOTAL);digest(i['sha256'])
        if not isinstance(i['chunks'],list) or len(i['chunks'])!=(i['size']+CHUNK-1)//CHUNK:raise Invalid('chunk coverage')
        for c in i['chunks']:digest(c)
        total+=i['size'];chunks+=len(i['chunks']);objects[p]=i
        if total>MAX_TOTAL or chunks>MAX_CHUNKS:raise Invalid('cohort size')
    if list(objects)!=sorted(objects):raise Invalid('noncanonical object order')
    if set(dirs)&set(objects):raise Invalid('file/directory collision')
    for path in list(objects)+dirs:
        if any('/'.join(path.split('/')[:n]) not in dirs for n in range(1,len(path.split('/')))):raise Invalid('missing ancestor directory')
    for p in objects:
        if any('/'.join(p.split('/')[:j]) in objects for j in range(1,len(p.split('/')))):raise Invalid('file ancestor collision')
    for k,kind in [('catalog_path','catalog'),('checkpoint_path','checkpoint')]:
        if m[k] not in objects or objects[m[k]]['kind']!=kind:raise Invalid('mandatory state absent')
    if not any(i['kind']=='journal' for i in m['objects']):raise Invalid('journal closure absent')
    return total

def validate_trust(t):
    fields(t,'format node trust_epoch min_generation threshold max_anchor_lifetime keys')
    if t['format']!='nia-recovery-trust-v1':raise Invalid('trust version')
    ident(t['node']);integer(t['trust_epoch'],1);integer(t['min_generation'],1)
    integer(t['threshold'],2,32);integer(t['max_anchor_lifetime'],1,86400)
    if not isinstance(t['keys'],list) or not t['threshold']<=len(t['keys'])<=32:raise Invalid('key count')
    ids=set();pubs=set()
    for k in t['keys']:
        fields(k,'id domain role public_key revoked');ident(k['id']);ident(k['domain']);digest(k['public_key'])
        if k['role'] not in ('recovery','witness') or type(k['revoked'])is not bool:raise Invalid('key role')
        if k['id'] in ids or k['public_key'] in pubs:raise Invalid('duplicate signing identity')
        ids.add(k['id']);pubs.add(k['public_key'])

def authenticate(mraw,eraw,trust,expected,now):
    validate_trust(trust);digest(expected);integer(now)
    m=decode(mraw);validate_manifest(m)
    if canonical(m)!=mraw:raise Invalid('noncanonical manifest')
    e=decode(eraw);fields(e,'anchor signatures');a=e['anchor']
    fields(a,'format node generation trust_epoch manifest_sha256 pending_sha256 issued expires nonce')
    if a['format']!='nia-recovery-anchor-v1':raise Invalid('anchor version')
    ident(a['node']);ident(a['nonce'])
    for k in ('generation','trust_epoch','issued','expires'):integer(a[k])
    digest(a['manifest_sha256']);digest(a['pending_sha256']);raw=canonical(a)
    if sha(raw)!=expected:raise Invalid('not independently pinned committed anchor')
    if a['node']!=trust['node'] or a['node']!=m['node'] or a['generation']!=m['generation'] or a['generation']<trust['min_generation'] or a['trust_epoch']!=trust['trust_epoch'] or a['trust_epoch']!=m['trust_epoch']:raise Invalid('node/generation/trust floor')
    if not a['issued']<=now<a['expires'] or a['expires']-a['issued']>trust['max_anchor_lifetime']:raise Invalid('anchor freshness')
    if a['manifest_sha256']!=sha(mraw) or a['pending_sha256']!=sha(canonical(m['pending'])):raise Invalid('manifest/pending changed')
    if not isinstance(e['signatures'],list) or not trust['threshold']<=len(e['signatures'])<=32:raise Invalid('signature count')
    registry={k['id']:k for k in trust['keys']};seen=set();domains=set();roles=set()
    for s in e['signatures']:
        fields(s,'key signature');ident(s['key'])
        if s['key'] not in registry or s['key'] in seen:raise Invalid('unknown/duplicate witness')
        k=registry[s['key']]
        if k['revoked'] or k['domain'] in domains or not isinstance(s['signature'],str) or not re.fullmatch(r'[0-9a-f]{128}',s['signature']):raise Invalid('revoked/dependent/invalid witness')
        try:Ed25519PublicKey.from_public_bytes(bytes.fromhex(k['public_key'])).verify(bytes.fromhex(s['signature']),DOMAIN+raw)
        except (ValueError,InvalidSignature) as exc:raise Invalid('bad signature') from exc
        seen.add(k['id']);domains.add(k['domain']);roles.add(k['role'])
    if roles!={'recovery','witness'}:raise Invalid('recovery and witness roles required')
    return m,a

def export(source,spec,out):
    """Unsigned offline exporter. Caller quiesces and validates native state.
    Streaming copy avoids loading complete files; source effects are not executed.
    """
    if out.path==source.path or out.path in source.path.parents or source.path in out.path.parents:
        raise Invalid('export output/source overlap')
    if os.listdir(out.fd):raise Invalid('export output must be empty')
    fields(spec,'node cohort generation trust_epoch catalog_path checkpoint_path pending objects')
    ident(spec['node']);digest(spec['cohort']);integer(spec['generation'],1);integer(spec['trust_epoch'],1)
    if not isinstance(spec['objects'],list) or not 1<=len(spec['objects'])<=MAX_OBJECTS:raise Invalid('export count')
    paths=[]
    for i in spec['objects']:
        fields(i,'path kind mode');paths.append(relative(i['path']));integer(i['mode'],0,0o777)
        if i['kind'] not in KINDS:raise Invalid('export class')
    if len(paths)!=len(set(paths)):raise Invalid('duplicate export')
    m={k:v for k,v in spec.items() if k!='objects'};m.update(format='nia-recovery-manifest-v1',objects=[])
    before_inventory=closed_inventory(source)
    if before_inventory[0]!=sorted(paths):raise Invalid('export input not closed before copying')
    m['root_attributes']=directory_attributes(source)
    m['directories']=[{'path':d,'attributes':directory_attributes(source,d)} for d in before_inventory[1]]
    total=0
    for i in sorted(spec['objects'],key=lambda x:x['path']):
        fd,p,n,s=source.open_file(i['path'],MAX_TOTAL-total)
        try:
            if s.st_mode&0o7777!=i['mode']:raise Invalid('source mode differs from intended inventory')
            count=0;h=hashlib.sha256();chunks=[];attrs=read_xattrs(fd)
            while count<s.st_size:
                b=bytearray();goal=min(CHUNK,s.st_size-count)
                while len(b)<goal:
                    x=os.read(fd,goal-len(b))
                    if not x:raise Invalid('export truncated')
                    b.extend(x)
                b=bytes(b);ch=sha(b);h.update(b);count+=len(b);chunks.append(ch)
                try:out.write_new('objects/'+ch,b)
                except FileExistsError:
                    if out.read('objects/'+ch,CHUNK)!=b:raise Invalid('existing object mismatch')
            if os.read(fd,1) or snapshot(s)!=snapshot(os.fstat(fd)) or snapshot(s)!=snapshot(os.stat(n,dir_fd=p,follow_symlinks=False)):raise Invalid('export modified')
            if attrs!=read_xattrs(fd):raise Invalid('xattrs changed')
            total+=count;m['objects'].append(dict(i,uid=s.st_uid,gid=s.st_gid,xattrs=attrs,size=count,sha256=h.hexdigest(),chunks=chunks))
        finally:os.close(fd);os.close(p)
    validate_manifest(m)
    if before_inventory!=closed_inventory(source) or before_inventory!=([i['path'] for i in m['objects']],expected_directories(m)):raise Invalid('export inventory not complete/stable')
    if m['root_attributes']!=directory_attributes(source) or any(d['attributes']!=directory_attributes(source,d['path']) for d in m['directories']):raise Invalid('directory metadata changed during export')
    raw=canonical(m)
    if len(raw)>LIMIT:raise Invalid('manifest size')
    out.write_new('manifest.json',raw);return m

def find_manifest(replicas,eraw,explicit=None):
    # Selection by an untrusted hash is safe only because authenticate runs before
    # any output creation. This function alone grants no trust.
    e=decode(eraw);fields(e,'anchor signatures');h=digest(e['anchor'].get('manifest_sha256'))
    if explicit is not None and sha(explicit)==h:return explicit
    for d in replicas:
        try:
            b=d.read('manifest.json')
            if sha(b)==h:return b
        except (OSError,Invalid):pass
    raise Incomplete('no intact copy of anchored manifest')

def reconstruct(mraw,eraw,trust,expected,now,replicas,out=None,fault=lambda _:None):
    m,a=authenticate(mraw,eraw,trust,expected,now)
    if not 1<=len(replicas)<=16:raise Invalid('replica count')
    if out:
        for r in replicas:
            if out.path==r.path or out.path in r.path.parents or r.path in out.path.parents:raise Invalid('candidate/source overlap')
        if os.listdir(out.fd):raise Invalid('candidate must be empty; incomplete candidates require separate review')
        v=os.fstatvfs(out.fd)
        if v.f_bavail*v.f_frsize<validate_manifest(m)+4*LIMIT:raise Invalid('candidate/evidence capacity')
        out.write_new('intent.json',canonical({'anchor':expected,'execution_permit':False}));fault('after-intent')
        out.write_new('manifest.json',mraw);out.write_new('anchor.json',eraw)
    report={'format':'nia-recovery-report-v1','anchor':expected,'node':m['node'],'generation':m['generation'],
      'complete':True,'execution_permit':False,'native_state_verified':False,'attributes_applied':False,'pending':m['pending'],
      'objects':[],'bad_replica_count':0,'bad_replicas':[]}
    evidence=0
    for i in m['objects']:
        h=hashlib.sha256();size=0;good_object=True;fd=parent=-1
        if out:fd,parent=out.create('payload/'+i['path'])
        try:
            for number,ch in enumerate(i['chunks']):
                expected_size=min(CHUNK,i['size']-number*CHUNK);selected=None
                for ri,r in enumerate(replicas):
                    try:b=r.read('objects/'+ch,CHUNK)
                    except (OSError,Invalid) as exc:
                        report['bad_replica_count']+=1
                        if len(report['bad_replicas'])<256:report['bad_replicas'].append({'replica':ri,'chunk':ch,'error':type(exc).__name__})
                        continue
                    if len(b)!=expected_size or sha(b)!=ch:
                        # A quarantine-output error is NOT a replica-input error.
                        # Propagate it: no READY marker without preserved evidence.
                        if out:
                            if evidence+len(b)>2*LIMIT:raise Incomplete('evidence capacity exhausted')
                            try:out.write_new('evidence/'+sha(b),b);evidence+=len(b)
                            except FileExistsError:
                                if out.read('evidence/'+sha(b),CHUNK)!=b:raise Incomplete('evidence collision')
                        report['bad_replica_count']+=1
                        if len(report['bad_replicas'])<256:report['bad_replicas'].append({'replica':ri,'chunk':ch,'error':'digest-or-length'})
                        continue
                    if selected is None:selected=b
                if selected is None:good_object=False;break
                h.update(selected);size+=len(selected)
                if out:write_all(fd,selected);fault('after-chunk')
            good_object=good_object and size==i['size'] and h.hexdigest()==i['sha256']
            if out:os.fsync(fd);os.fsync(parent);fault('after-object')
        finally:
            if fd>=0:os.close(fd);os.close(parent)
        report['objects'].append({'path':i['path'],'verified':good_object});report['complete'] &= good_object
    if out:
        out.write_new('report.json',canonical(report));fault('after-report')
        if report['complete']:
            out.write_new('candidate-ready.json',canonical({'anchor':expected,'report_sha256':sha(canonical(report)),
                'state':'reconciliation-required','execution_permit':False}));fault('after-ready')
    return report

def inspect_original(mraw,eraw,trust,expected,now,source):
    """Exact anchored inventory comparison; never calls missing state 'empty'.
    Not a full live-host audit: inventories/ownership must be complete and fresh.
    """
    m,_=authenticate(mraw,eraw,trust,expected,now);items=[]
    try:inventory_before=closed_inventory(source)
    except (OSError,Invalid):inventory_before=None
    for i in m['objects']:
        fd=p=-1
        try:
            fd,p,n,s=source.open_file(i['path'],i['size']);h=hashlib.sha256();length=0
            while length<=i['size']:
                b=os.read(fd,min(CHUNK,i['size']+1-length))
                if not b:break
                h.update(b);length+=len(b)
            consistent=(length==i['size'] and h.hexdigest()==i['sha256'] and
                s.st_mode&0o7777==i['mode'] and s.st_uid==i['uid'] and s.st_gid==i['gid'] and read_xattrs(fd)==i['xattrs'] and snapshot(s)==snapshot(os.fstat(fd)) and
                snapshot(s)==snapshot(os.stat(n,dir_fd=p,follow_symlinks=False)))
            result='matched' if consistent else 'mismatch'
        except (OSError,Invalid):result='missing-unreadable-or-unsafe'
        finally:
            if fd>=0:os.close(fd);os.close(p)
        items.append({'path':i['path'],'result':result})
    try:inventory_after=closed_inventory(source)
    except (OSError,Invalid):inventory_after=None
    try:
        attrs_exact=(directory_attributes(source)==m['root_attributes'] and all(directory_attributes(source,d['path'])==d['attributes'] for d in m['directories']))
    except (OSError,Invalid):attrs_exact=False
    exact=(inventory_before==inventory_after==([i['path'] for i in m['objects']],expected_directories(m))) and attrs_exact
    return {'objects':items,'complete':exact and all(i['result']=='matched' for i in items),
      'inventory_exact':exact,'execution_permit':False,'inventory_scope_only':True}

def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    for mode in ('verify','reconstruct','inspect'):
        q=s.add_parser(mode)
        for k in ('anchor','trust','expected-anchor'):q.add_argument('--'+k,required=True)
        q.add_argument('--manifest');q.add_argument('--replica',action='append',required=True)
        if mode=='reconstruct':q.add_argument('--candidate',required=True)
        if mode=='inspect':q.add_argument('--state-root',required=True)
    a=p.parse_args()
    if os.geteuid()==0:p.error('dedicated unprivileged recovery identity required')
    with contextlib.ExitStack() as st:
        replicas=[st.enter_context(Directory(x)) for x in a.replica]
        eraw=argument_file(a.anchor);trust=decode(argument_file(a.trust));explicit=None
        if a.manifest:
            try:explicit=argument_file(a.manifest)
            except OSError:pass
        raw=find_manifest(replicas,eraw,explicit)
        if a.command=='inspect':out=inspect_original(raw,eraw,trust,a.expected_anchor,int(time.time()),st.enter_context(Directory(a.state_root)))
        else:
            candidate=st.enter_context(Directory(a.candidate,True)) if a.command=='reconstruct' else None
            out=reconstruct(raw,eraw,trust,a.expected_anchor,int(time.time()),replicas,candidate)
        print(json.dumps(out,sort_keys=True));return 0 if out['complete'] else 2
if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError) as e:
        print(json.dumps({'error':str(e),'execution_permit':False}),file=sys.stderr);raise SystemExit(2)
