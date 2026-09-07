# SPDX-License-Identifier: MIT
"""Independent finite reference model of E-RECOVERY-1, not compiled Ada execution.

These tests validate selected properties of this model, not the production
implementation or its filesystem assumptions. Real crash cases remain NOT_RUN
in the fault catalog. Frames use the documented MCLOG002 wire layout.
"""
from dataclasses import dataclass, replace
import hashlib
import itertools
import struct
import unittest

ZERO=bytes(32)
PLAN=hashlib.sha256(b'synthetic-plan').digest()
RECEIPT=hashlib.sha256(b'synthetic-authorization').digest()
MAX_COUNTER=2**63-1
class Rejected(ValueError):pass

@dataclass(frozen=True)
class Event:
    kind:int
    index:int=0
    object:bytes=PLAN

@dataclass(frozen=True)
class Image:
    count:int
    stage:str='new'
    cursor:int=1
    pending:int=0
    receipt:bytes=ZERO

def step(s:Image,e:Event)->Image:
    if not 1<=s.count<=1024 or not 0<=e.index<=s.count or len(e.object)!=32:raise Rejected()
    if s.stage=='new':
        if e!=Event(1):raise Rejected()
        return replace(s,stage='forward')
    if s.stage in ('committed','restored'):raise Rejected()
    if e.kind==10 and e.index==0 and e.object!=ZERO:return s
    if e.kind in (2,3,4):
        if s.stage!='forward' or e.object!=PLAN:raise Rejected()
        if e.kind==2 and e.index==s.cursor and e.index>0:return replace(s,pending=e.index)
        if e.kind==3 and e.index==s.cursor==s.pending and e.index>0:return replace(s,pending=0,cursor=s.cursor+1)
        if e.kind==4 and s.cursor==s.count+1 and s.pending==0 and e.index==0:return replace(s,stage='applied')
        raise Rejected()
    if e.kind==5:
        if s.stage not in ('applied','commit-pending') or e.index!=0 or e.object==ZERO:raise Rejected()
        if s.receipt not in (ZERO,e.object):raise Rejected()
        return replace(s,stage='commit-pending',receipt=e.object)
    if e.kind==6:
        if s.stage!='commit-pending' or e.index!=0 or e.object!=s.receipt:raise Rejected()
        return replace(s,stage='committed')
    if e.kind==7:
        if s.stage not in ('forward','applied','reverse') or e.index==0 or e.object==ZERO:raise Rejected()
        required=s.cursor if s.stage=='reverse' else s.count
        if e.index!=required or s.receipt not in (ZERO,e.object):raise Rejected()
        return replace(s,stage='reverse',cursor=required,pending=required,receipt=e.object)
    if e.kind==8:
        if s.stage!='reverse' or e.index!=s.cursor or s.pending!=e.index or e.index==0 or e.object!=s.receipt:raise Rejected()
        return replace(s,cursor=s.cursor-1,pending=0)
    if e.kind==9:
        if s.stage!='reverse' or s.cursor!=0 or s.pending!=0 or e.index!=0 or e.object!=s.receipt:raise Rejected()
        return replace(s,stage='restored')
    raise Rejected()

def images(s:Image,index:int)->set[str]:
    if index<1 or index>s.count or s.stage=='new':return set()
    if s.stage=='forward':
        if index<s.cursor:return {'after'}
        return {'before','after'} if index==s.pending else {'before'}
    if s.stage in ('applied','commit-pending','committed'):return {'after'}
    if s.stage=='reverse':return {'before'} if index>s.cursor else {'before','after'}
    if s.stage=='restored':return {'before'}
    raise Rejected()

def forward_events(n):
    return [Event(1),*[e for i in range(1,n+1) for e in (Event(2,i),Event(3,i))],Event(4),Event(5,object=RECEIPT),Event(6,object=RECEIPT)]

def fold(n,events):
    s=Image(n)
    for e in events:s=step(s,e)
    return s

def frame(sequence,event,previous=ZERO,epoch=1,token=2,generation=3):
    b=bytearray(256);b[:8]=b'MCLOG002'
    struct.pack_into('>QH',b,8,sequence,event.kind);b[18]=0
    b[24:40]=bytes([1])*16;b[40:56]=bytes([2])*16
    for off,value in [(56,epoch),(64,token),(72,event.index),(80,generation)]:struct.pack_into('>Q',b,off,value)
    b[88:120]=event.object;b[120:152]=previous;b[224:]=hashlib.sha256(b[:224]).digest()
    return bytes(b)

def decode(raw):
    if len(raw)!=256 or raw[:8]!=b'MCLOG002' or raw[224:]!=hashlib.sha256(raw[:224]).digest():raise Rejected()
    if any(raw[19:24]) or any(raw[152:224]) or raw[18]!=0:raise Rejected()
    numbers=[struct.unpack_from('>Q',raw,o)[0] for o in (8,56,64,72,80)]
    if any(n>MAX_COUNTER for n in numbers) or numbers[0]==0:raise Rejected()
    if raw[24:40]==bytes(16) or raw[40:56]==bytes(16):raise Rejected()
    return numbers,Event(struct.unpack_from('>H',raw,16)[0],numbers[3],raw[88:120]),raw[120:152]

def journal(raw,n):
    s=Image(n);head=ZERO;full=len(raw)//256
    for k in range(full):
        f=raw[k*256:(k+1)*256];nums,e,prev=decode(f)
        if nums[0]!=k+1 or prev!=head or nums[1]!=1 or nums[2]!=2 or nums[4]!=3:raise Rejected()
        if f[24:40]!=bytes([1])*16 or f[40:56]!=bytes([2])*16:raise Rejected()
        s=step(s,e);head=hashlib.sha256(f).digest()
    return s,raw[full*256:]

def encode_journal(events):
    data=b'';prev=ZERO
    for seq,e in enumerate(events,1):
        f=frame(seq,e,prev);data+=f;prev=hashlib.sha256(f).digest()
    return data

class ReplayReferenceTests(unittest.TestCase):
    def test_all_forward_crash_prefixes(self):
        for n in range(1,5):
            events=forward_events(n)
            for i in range(len(events)+1):
                expected=fold(n,events[:i]);got,tail=journal(encode_journal(events[:i]),n)
                self.assertEqual(expected,got);self.assertFalse(tail)
    def test_reverse_from_every_predecision_prefix(self):
        for n in range(1,5):
            events=forward_events(n)[:-2]
            for cut in range(1,len(events)+1):
                s=fold(n,events[:cut])
                for i in range(n,0,-1):
                    s=step(s,Event(7,i,RECEIPT));s=step(s,Event(8,i,RECEIPT))
                s=step(s,Event(9,object=RECEIPT))
                self.assertEqual(s.stage,'restored')
                self.assertTrue(all(images(s,i)=={'before'} for i in range(1,n+1)))
    def test_completion_without_intent_rejected(self):
        s=step(Image(2),Event(1))
        with self.assertRaises(Rejected):step(s,Event(3,1))
    def test_intent_retry_idempotent(self):
        s=fold(2,[Event(1),Event(2,1)])
        self.assertEqual(step(s,Event(2,1)),s)
    def test_no_out_of_order_completion(self):
        with self.assertRaises(Rejected):fold(2,[Event(1),Event(2,1),Event(3,2)])
    def test_unknown_contents_never_allowed(self):
        for n in (1,3):
            ev=forward_events(n)
            for c in range(len(ev)+1):
                s=fold(n,ev[:c])
                self.assertTrue(all('unknown' not in images(s,i) for i in range(1,n+1)))
    def test_future_change_is_not_silently_accepted(self):
        s=fold(3,[Event(1),Event(2,1)])
        self.assertEqual(images(s,1),{'before','after'})
        self.assertEqual(images(s,2),{'before'})
    def test_completed_prefix_must_be_after(self):
        s=fold(2,[Event(1),Event(2,1),Event(3,1)])
        self.assertEqual(images(s,1),{'after'});self.assertEqual(images(s,2),{'before'})
    def test_restored_suffix_must_be_before(self):
        s=fold(2,[Event(1),Event(7,2,RECEIPT),Event(8,2,RECEIPT)])
        self.assertEqual(images(s,2),{'before'})
    def test_commit_receipt_cannot_change(self):
        s=fold(1,forward_events(1)[:-1])
        self.assertEqual(step(s,Event(5,object=RECEIPT)),s)
        with self.assertRaises(Rejected):step(s,Event(5,object=PLAN))
    def test_reverse_receipt_cannot_change(self):
        s=fold(1,[Event(1),Event(7,1,RECEIPT)])
        with self.assertRaises(Rejected):step(s,Event(7,1,PLAN))
    def test_commit_decision_cannot_switch_to_reverse(self):
        s=fold(1,forward_events(1)[:-1])
        with self.assertRaises(Rejected):step(s,Event(7,1,RECEIPT))
    def test_reverse_cannot_switch_to_commit(self):
        s=fold(1,[Event(1),Event(7,1,RECEIPT)])
        with self.assertRaises(Rejected):step(s,Event(5,object=RECEIPT))
    def test_terminal_states_are_absorbing(self):
        states=[fold(1,forward_events(1)),fold(1,[Event(1),Event(7,1,RECEIPT),Event(8,1,RECEIPT),Event(9,object=RECEIPT)])]
        for s,k,idx,obj in itertools.product(states,range(1,12),range(2),(PLAN,RECEIPT)):
            with self.assertRaises(Rejected):step(s,Event(k,idx,obj))
    def test_all_partial_suffix_lengths_not_decisions(self):
        prior=encode_journal(forward_events(1)[:-1]);last=encode_journal(forward_events(1))[-256:]
        for length in range(1,256):
            s,tail=journal(prior+last[:length],1)
            self.assertEqual(s.stage,'commit-pending');self.assertEqual(len(tail),length)
    def test_full_corrupt_record_never_treated_as_tail(self):
        raw=bytearray(encode_journal(forward_events(1)));raw[-12]^=1
        with self.assertRaises(Rejected):journal(bytes(raw),1)
    def test_recomputed_checksum_does_not_authorize_reserved_bits(self):
        raw=bytearray(frame(1,Event(1)));raw[160]=1;raw[224:]=hashlib.sha256(raw[:224]).digest()
        with self.assertRaises(Rejected):decode(bytes(raw))
    def test_wrong_chain_sequence_epoch_and_token_rejected(self):
        first=frame(1,Event(1));head=hashlib.sha256(first).digest()
        for second in (frame(3,Event(2,1),head),frame(2,Event(2,1),ZERO),
                       frame(2,Event(2,1),head,epoch=2),frame(2,Event(2,1),head,token=3)):
            with self.assertRaises(Rejected):journal(first+second,1)
    def test_signed_counter_limit(self):
        raw=frame(2**63,Event(1))
        with self.assertRaises(Rejected):decode(raw)
    def test_wrong_plan_bound_root_and_operation(self):
        for offset in (24,40):
            raw=bytearray(frame(1,Event(1)));raw[offset]^=1;raw[224:]=hashlib.sha256(raw[:224]).digest()
            with self.assertRaises(Rejected):journal(bytes(raw),1)
    def test_torn_tail_is_not_an_authorized_execution(self):
        s,tail=journal(encode_journal([Event(1)])+b'partial',1)
        self.assertEqual(s.stage,'forward');self.assertTrue(tail)
        # The reference only returns a pending suffix, not a truncation/write action.
    def test_hash_chain_is_not_authentication(self):
        raw=frame(1,Event(1))
        self.assertEqual(decode(raw)[1],Event(1))
        # There is intentionally no signature claim in the checksum or this model.

if __name__=='__main__':unittest.main()
