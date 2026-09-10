# SPDX-License-Identifier: BSD-3-Clause
import copy,json,os,shutil,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import nia_recovery as r
class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.source=self.root/'source';self.source.mkdir(mode=0o700)
        self.original={'catalog.bin':b'catalog generation 9','checkpoint.bin':b'all replay and reservation states',
          'journal.bin':b'intent req1\nunknown req1\n','core.bin':b'A'*r.CHUNK+b'B'*r.CHUNK+b'C'*12}
        for p,b in self.original.items():
            f=self.source/p;f.write_bytes(b);f.chmod(0o600)
        spec={'node':'node1','cohort':'c'*64,'generation':9,'trust_epoch':4,
         'catalog_path':'catalog.bin','checkpoint_path':'checkpoint.bin','pending':['req1'],
         'objects':[{'path':p,'mode':0o600,'kind':{'catalog.bin':'catalog','checkpoint.bin':'checkpoint','journal.bin':'journal'}.get(p,'managed-file')} for p in self.original]}
        self.spec=spec
        self.mirrors=[self.root/'mirror1',self.root/'mirror2'];self.mirrors[0].mkdir(mode=0o700)
        with r.Directory(self.source) as src,r.Directory(self.mirrors[0]) as dst:self.manifest=r.export(src,spec,dst)
        shutil.copytree(self.mirrors[0],self.mirrors[1]);self.raw=r.canonical(self.manifest)
        self.keys=[Ed25519PrivateKey.from_private_bytes(bytes([i])*32) for i in (1,2)]
        self.trust={'format':'nia-recovery-trust-v1','node':'node1','trust_epoch':4,'min_generation':9,'threshold':2,'max_anchor_lifetime':1000,
          'keys':[{'id':f'k{i}','domain':f'd{i}','role':role,'public_key':key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw).hex(),'revoked':False} for i,(role,key) in enumerate(zip(('recovery','witness'),self.keys))]}
        self.anchor={'format':'nia-recovery-anchor-v1','node':'node1','generation':9,'trust_epoch':4,
          'manifest_sha256':r.sha(self.raw),'pending_sha256':r.sha(r.canonical(['req1'])),'issued':100,'expires':500,'nonce':'recovery1'};self.sign()
    def tearDown(self):self.tmp.cleanup()
    def sign(self):
        self.encoded=r.canonical({'anchor':self.anchor,'signatures':[{'key':f'k{i}','signature':k.sign(r.DOMAIN+r.canonical(self.anchor)).hex()} for i,k in enumerate(self.keys)]});self.expected=r.sha(r.canonical(self.anchor))
    def recover(self,output=True,fault=lambda _:None):
        from contextlib import ExitStack
        with ExitStack() as s:
            mirrors=[s.enter_context(r.Directory(p)) for p in self.mirrors];dst=None
            if output:
                p=self.root/'candidate';p.mkdir(mode=0o700,exist_ok=True);dst=s.enter_context(r.Directory(p,True))
            return r.reconstruct(self.raw,self.encoded,self.trust,self.expected,200,mirrors,dst,fault)
    def inspect(self):
        with r.Directory(self.source) as d:return r.inspect_original(self.raw,self.encoded,self.trust,self.expected,200,d)
    def test_exact_reconstruction(self):
        out=self.recover();self.assertTrue(out['complete']);self.assertFalse(out['execution_permit']);self.assertFalse(out['native_state_verified']);self.assertEqual(out['pending'],['req1'])
        for p,b in self.original.items():self.assertEqual((self.root/'candidate/payload'/p).read_bytes(),b)
    def test_different_damaged_chunks_combined(self):
        i=next(i for i in self.manifest['objects'] if i['path']=='core.bin')
        (self.mirrors[0]/'objects'/i['chunks'][0]).write_bytes(b'bad');(self.mirrors[1]/'objects'/i['chunks'][1]).unlink()
        out=self.recover();self.assertTrue(out['complete']);self.assertGreaterEqual(out['bad_replica_count'],2)
        self.assertEqual((self.root/'candidate/payload/core.bin').read_bytes(),self.original['core.bin'])
        self.assertEqual((self.mirrors[0]/'objects'/i['chunks'][0]).read_bytes(),b'bad')
        self.assertTrue((self.root/'candidate/evidence'/r.sha(b'bad')).exists())
    def test_all_copies_missing_no_ready_marker(self):
        h=self.manifest['objects'][0]['chunks'][0]
        for p in self.mirrors:(p/'objects'/h).unlink()
        self.assertFalse(self.recover()['complete']);self.assertFalse((self.root/'candidate/candidate-ready.json').exists())
    def test_all_copies_corrupt(self):
        h=self.manifest['objects'][0]['chunks'][0]
        for p in self.mirrors:(p/'objects'/h).write_bytes(b'bad')
        self.assertFalse(self.recover(False)['complete'])
    def test_entire_replica_lost(self):
        shutil.rmtree(self.mirrors[0]/'objects');self.assertTrue(self.recover()['complete'])
    def test_manifest_loss_and_corruption_fallback(self):
        (self.mirrors[0]/'manifest.json').write_bytes(b'damaged')
        with r.Directory(self.mirrors[0]) as a,r.Directory(self.mirrors[1]) as b:self.assertEqual(r.find_manifest([a,b],self.encoded),self.raw)
    def test_manifest_all_lost(self):
        for d in self.mirrors:(d/'manifest.json').unlink()
        with r.Directory(self.mirrors[0]) as a,r.Directory(self.mirrors[1]) as b:
            with self.assertRaises(r.Incomplete):r.find_manifest([a,b],self.encoded)
    def test_old_anchor_even_with_valid_signatures(self):
        self.anchor['generation']=8;self.sign()
        with self.assertRaises(r.Invalid):self.recover()
    def test_replaced_anchor(self):
        self.expected='a'*64
        with self.assertRaises(r.Invalid):self.recover()
    def test_manifest_substitution(self):
        self.raw+=b' '
        with self.assertRaises(r.Invalid):self.recover()
    def test_pending_set_not_erased(self):
        self.manifest['pending']=[];self.raw=r.canonical(self.manifest);self.anchor['manifest_sha256']=r.sha(self.raw);self.sign()
        with self.assertRaises(r.Invalid):self.recover()
    def test_expiry(self):
        self.anchor['expires']=200;self.sign()
        with self.assertRaises(r.Invalid):self.recover()
    def test_future_time(self):
        self.anchor['issued']=201;self.sign()
        with self.assertRaises(r.Invalid):self.recover()
    def test_wrong_node(self):
        self.trust['node']='other'
        with self.assertRaises(r.Invalid):self.recover()
    def test_trust_floor(self):
        self.trust['trust_epoch']=5
        with self.assertRaises(r.Invalid):self.recover()
    def test_minimum_generation(self):
        self.trust['min_generation']=10
        with self.assertRaises(r.Invalid):self.recover()
    def test_revoked_key(self):
        self.trust['keys'][1]['revoked']=True
        with self.assertRaises(r.Invalid):self.recover()
    def test_same_domain(self):
        self.trust['keys'][1]['domain']='d0'
        with self.assertRaises(r.Invalid):self.recover()
    def test_same_key_under_alias(self):
        self.trust['keys'][1]['public_key']=self.trust['keys'][0]['public_key']
        with self.assertRaises(r.Invalid):self.recover()
    def test_wrong_roles(self):
        self.trust['keys'][1]['role']='recovery'
        with self.assertRaises(r.Invalid):self.recover()
    def test_forged_signature(self):
        e=r.decode(self.encoded);e['signatures'][0]['signature']='0'*128;self.encoded=r.canonical(e)
        with self.assertRaises(r.Invalid):self.recover()
    def test_one_signature_not_enough(self):
        e=r.decode(self.encoded);e['signatures']=e['signatures'][:1];self.encoded=r.canonical(e)
        with self.assertRaises(r.Invalid):self.recover()
    def test_boolean_generation(self):
        self.manifest['generation']=True
        with self.assertRaises(r.Invalid):r.validate_manifest(self.manifest)
    def test_duplicate_json(self):
        with self.assertRaises(r.Invalid):r.decode(b'{"a":1,"a":2}')
    def test_duplicate_path(self):
        self.manifest['objects'].append(self.manifest['objects'][0])
        with self.assertRaises(r.Invalid):r.validate_manifest(self.manifest)
    def test_traversal(self):
        self.manifest['objects'][0]['path']='../host'
        with self.assertRaises(r.Invalid):r.validate_manifest(self.manifest)
    def test_business_data_not_generic_restore(self):
        self.manifest['objects'][0]['kind']='business-data'
        with self.assertRaises(r.Invalid):r.validate_manifest(self.manifest)
    def test_journal_mandatory(self):
        self.manifest['objects']=[i for i in self.manifest['objects'] if i['kind']!='journal']
        with self.assertRaises(r.Invalid):r.validate_manifest(self.manifest)
    def test_symlink_object(self):
        h=self.manifest['objects'][0]['chunks'][0]
        for p in self.mirrors:
            f=p/'objects'/h;f.unlink();f.symlink_to(self.source/'catalog.bin')
        self.assertFalse(self.recover()['complete'])
    def test_fifo_no_block(self):
        h=self.manifest['objects'][0]['chunks'][0]
        for p in self.mirrors:
            f=p/'objects'/h;f.unlink();os.mkfifo(f)
        self.assertFalse(self.recover()['complete'])
    def test_parent_symlink(self):
        link=self.root/'alias';link.symlink_to(self.mirrors[0],target_is_directory=True)
        with self.assertRaises(OSError):r.Directory(link/'objects')
    def test_no_overwrite_of_candidate(self):
        self.recover()
        with self.assertRaises(r.Invalid):self.recover()
    def test_capacity(self):
        class Full:f_bavail=0;f_frsize=4096
        with patch.object(r.os,'fstatvfs',return_value=Full()):
            with self.assertRaises(r.Invalid):self.recover()
        self.assertEqual(list((self.root/'candidate').iterdir()),[])
    def test_each_interruption_keeps_originals(self):
        for point in ('after-intent','after-chunk','after-object','after-report','after-ready'):
            def fault(p):
                if p==point:raise OSError('injected interruption')
            with self.assertRaises(OSError):self.recover(fault=fault)
            for p,b in self.original.items():self.assertEqual((self.source/p).read_bytes(),b)
            if point!='after-ready':self.assertFalse((self.root/'candidate/candidate-ready.json').exists())
            with self.assertRaises(r.Invalid):self.recover()
            shutil.rmtree(self.root/'candidate')
    def test_chunk_coverage(self):
        self.manifest['objects'][0]['chunks']=[]
        with self.assertRaises(r.Invalid):r.validate_manifest(self.manifest)
    def test_verify_is_read_only(self):
        self.assertTrue(self.recover(False)['complete']);self.assertFalse((self.root/'candidate').exists())
    def test_live_inventory_detects_corruption(self):
        self.assertTrue(self.inspect()['complete']);(self.source/'core.bin').write_bytes(b'bad')
        self.assertFalse(self.inspect()['complete'])
    def test_live_inventory_detects_missing_history(self):
        (self.source/'journal.bin').unlink();self.assertFalse(self.inspect()['complete']);self.assertFalse((self.source/'journal.bin').exists())
    def test_live_inventory_detects_wrong_mode(self):
        (self.source/'catalog.bin').chmod(0o666);self.assertFalse(self.inspect()['complete'])
    def test_live_inventory_detects_injected_file(self):
        (self.source/'injected.so').write_bytes(b'unknown executable');self.assertFalse(self.inspect()['complete'])
    def test_live_inventory_detects_xattr_change(self):
        os.setxattr(self.source/'core.bin','user.changed',b'value');self.assertFalse(self.inspect()['complete'])
    def test_live_inventory_detects_unlisted_directory(self):
        (self.source/'injected').mkdir();self.assertFalse(self.inspect()['complete'])
    def test_empty_content_digest(self):
        i=next(i for i in self.manifest['objects'] if i['path']=='core.bin');i.update(size=0,chunks=[],sha256=r.sha(b''));self.raw=r.canonical(self.manifest);self.anchor['manifest_sha256']=r.sha(self.raw);self.sign()
        self.assertTrue(self.recover()['complete']);self.assertEqual((self.root/'candidate/payload/core.bin').read_bytes(),b'')
    def test_evidence_io_error_is_not_swallowed(self):
        h=self.manifest['objects'][0]['chunks'][0]
        (self.mirrors[0]/'objects'/h).write_bytes(b'bad')
        original=r.Directory.write_new
        def fail(d,path,b):
            if path.startswith('evidence/'):raise OSError('quarantine disk error')
            return original(d,path,b)
        with patch.object(r.Directory,'write_new',fail):
            with self.assertRaises(OSError):self.recover()
        self.assertFalse((self.root/'candidate/candidate-ready.json').exists())
    def test_export_never_writes_into_source(self):
        with r.Directory(self.source) as src:
            with self.assertRaises(r.Invalid):r.export(src,self.spec,src)
        self.assertFalse((self.source/'objects').exists())
    def test_export_rejects_unlisted_input_before_writing(self):
        (self.source/'unlisted').write_bytes(b'injected')
        out=self.root/'new-export';out.mkdir(mode=0o700)
        with r.Directory(self.source) as src,r.Directory(out) as dst:
            with self.assertRaises(r.Invalid):r.export(src,self.spec,dst)
        self.assertEqual(list(out.iterdir()),[])

    def test_root_directory_permissions_detected(self):
        self.source.chmod(0o777)
        self.assertFalse(self.inspect()['complete'])
    def test_root_xattrs_detected(self):
        os.setxattr(self.source,'user.unexpected',b'drift')
        self.assertFalse(self.inspect()['complete'])
    def test_file_setid_never_ignored(self):
        (self.source/'catalog.bin').chmod(0o4600)
        self.assertFalse(self.inspect()['complete'])
    def test_directory_ancestor_must_be_declared(self):
        self.manifest['objects'][0]['path']='missing/child'
        with self.assertRaises(r.Invalid):r.validate_manifest(self.manifest)

if __name__=='__main__':unittest.main()
