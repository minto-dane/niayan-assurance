# SPDX-License-Identifier: MIT
"""Bounded non-privileged file IO. No live-system changes or implicit initialization.
Caller supplies a trusted mount namespace and exclusively owned output directory.
"""
from __future__ import annotations
import hashlib,json,os,re,stat
from pathlib import Path
LIMIT=8*1024*1024
class Invalid(ValueError):pass

def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(o):return json.dumps(o,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def decode(b):
    if len(b)>LIMIT:raise Invalid('metadata size')
    def unique(ps):
        d={}
        for k,v in ps:
            if k in d:raise Invalid('duplicate key')
            d[k]=v
        return d
    try:return json.loads(b.decode('utf-8'),object_pairs_hook=unique,parse_constant=lambda _: (_ for _ in ()).throw(Invalid('nonfinite')))
    except (UnicodeError,json.JSONDecodeError,RecursionError) as e:raise Invalid('JSON') from e

def fields(d,s):
    if not isinstance(d,dict) or set(d)!=set(s.split()):raise Invalid('schema')
def integer(n,low=0,high=2**63-1):
    if type(n)is not int or not low<=n<=high:raise Invalid('integer')
    return n

def digest(s):
    if not isinstance(s,str) or not re.fullmatch(r'[0-9a-f]{64}',s):raise Invalid('digest')
    return s

def ident(s):
    if not isinstance(s,str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,95}',s):raise Invalid('identifier')
    return s

def relative(s):
    if not isinstance(s,str) or not s or len(s)>1024 or '\\' in s or '\0' in s:raise Invalid('path')
    ps=s.split('/')
    if len(ps)>32 or any(p in ('','.','..') or not re.fullmatch(r'[a-zA-Z0-9_.+@-]{1,160}',p) for p in ps):raise Invalid('path traversal/encoding')
    return s

def snapshot(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode,s.st_uid,s.st_gid)
def mountid(fd):
    # Fixed procfs path; this value is observation, not authentication.
    with open(f'/proc/self/fdinfo/{fd}',encoding='ascii') as f:
        for line in f:
            if line.startswith('mnt_id:'):return int(line.split(':')[1])
    raise Invalid('mount ID unavailable')

def write_all(fd,b):
    v=memoryview(b)
    while v:
        n=os.write(fd,v)
        if n<=0:raise OSError('short write')
        v=v[n:]

class Directory:
    def __init__(self,path,private=False):
        self.path=Path(path).absolute();self.fd=-1
        if self.path==Path('/') or '..' in self.path.parts:raise Invalid('host root/path traversal')
        fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC)
        try:
            for part in self.path.parts[1:]:
                n=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd)
                os.close(fd);fd=n
            s=os.fstat(fd)
            if private and (s.st_uid!=os.geteuid() or s.st_mode&0o077):raise Invalid('private output required')
            self.dev=s.st_dev;self.mount=mountid(fd);self.fd=fd
        except BaseException:os.close(fd);raise
    def close(self):
        if self.fd>=0:os.close(self.fd);self.fd=-1
    def __enter__(self):return self
    def __exit__(self,*a):self.close()
    def parent(self,path,create=False):
        ps=relative(path).split('/');fd=os.dup(self.fd)
        try:
            for part in ps[:-1]:
                if create:
                    try:os.mkdir(part,0o700,dir_fd=fd);os.fsync(fd)
                    except FileExistsError:pass
                n=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd)
                if os.fstat(n).st_dev!=self.dev or mountid(n)!=self.mount:os.close(n);raise Invalid('mount crossing')
                os.close(fd);fd=n
            return fd,ps[-1]
        except BaseException:os.close(fd);raise
    def open_file(self,path,limit):
        p,n=self.parent(path);fd=-1
        try:
            s=os.stat(n,dir_fd=p,follow_symlinks=False)
            if not stat.S_ISREG(s.st_mode) or s.st_size>limit or s.st_dev!=self.dev:raise Invalid('not bounded regular file')
            fd=os.open(n,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=p)
            if snapshot(s)!=snapshot(os.fstat(fd)) or mountid(fd)!=self.mount:raise Invalid('file changed/mount crossing')
            return fd,p,n,s
        except BaseException:
            if fd>=0:os.close(fd)
            os.close(p);raise
    def read(self,path,limit=LIMIT):
        fd,p,n,s=self.open_file(path,limit)
        try:
            out=bytearray()
            while len(out)<=limit:
                b=os.read(fd,min(65536,limit+1-len(out)))
                if not b:break
                out.extend(b)
            if len(out)>limit or snapshot(s)!=snapshot(os.fstat(fd)) or snapshot(s)!=snapshot(os.stat(n,dir_fd=p,follow_symlinks=False)):raise Invalid('changed during read')
            return bytes(out)
        finally:os.close(fd);os.close(p)
    def create(self,path):
        p,n=self.parent(path,True)
        try:return os.open(n,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=p),p
        except BaseException:os.close(p);raise
    def write_new(self,path,b):
        fd,p=self.create(path)
        try:write_all(fd,b);os.fsync(fd);os.fsync(p)
        finally:os.close(fd);os.close(p)

def argument_file(path):
    f=Path(path).absolute()
    with Directory(f.parent) as d:return d.read(f.name)
