# SPDX-License-Identifier: MIT
"""Real isolated Linux/runner probes plus explicitly labelled source regressions.
These do not execute Ada and are not a substitute for its tests or SPARK proof.
"""
from pathlib import Path
import ctypes
import importlib.util
import json
import os
import signal
import struct
import subprocess
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[3]
CI=ROOT/'assurance/ci'
if str(CI) not in sys.path: sys.path.insert(0,str(CI))
SPEC=importlib.util.spec_from_file_location('nia_final_check_runner',CI/'run-engineering-checks.py')
RUN=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(RUN)

# This harness owns ONLY its own children and reaps descendants. The fixture
# sleeps harmlessly, with a finite lifetime even if its controller were lost.
NATIVE_HARNESS=r'''
import ctypes,importlib.util,json,os,signal,sys,time
from pathlib import Path
ci=Path(sys.argv[1]);base=Path(sys.argv[2]);mode=sys.argv[3]
sys.path.insert(0,str(ci))
spec=importlib.util.spec_from_file_location('runner',ci/'run-engineering-checks.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
libc=ctypes.CDLL(None,use_errno=True)
if libc.prctl(36,1,0,0,0)!=0: raise OSError(ctypes.get_errno(),'test subreaper')
program='import os,time\np=os.fork()\nif p==0:\n'
if mode=='closed': program+=' os.close(1);os.close(2)\n'
program+=' time.sleep(5);os._exit(0)\nprint(p,flush=True)\nos._exit(0)\n'
log=base/'child.log';child=None;reaped=False
try:
 result=r.run_command([sys.executable,'-I','-S','-c',program],base,log,r.clean_env(base),0.35)
 child=int(log.read_text().strip());stop=time.monotonic()+2
 while time.monotonic()<stop:
  pid,status=os.waitpid(child,os.WNOHANG)
  if pid==child:reaped=True;break
  time.sleep(.01)
 if not reaped: raise AssertionError('fixture descendant survived group cleanup')
 if not os.WIFSIGNALED(status) or os.WTERMSIG(status)!=signal.SIGKILL:raise AssertionError('descendant was not killed')
 print(json.dumps({'result':result,'descendant_reaped':reaped}))
finally:
 if child is not None and not reaped:
  try:os.kill(child,signal.SIGKILL);os.waitpid(child,0)
  except ChildProcessError:pass
'''

class NativeRuntimeTests(unittest.TestCase):
    def test_runner_cleans_group_when_leader_exits_and_stdout_remains(self):
        with tempfile.TemporaryDirectory() as d:
            p=subprocess.run([sys.executable,'-I','-S','-c',NATIVE_HARNESS,str(CI),d,'held'],
              capture_output=True,text=True,timeout=8,env=RUN.clean_env(Path(d)))
            self.assertEqual(p.returncode,0,p.stderr)
            r=json.loads(p.stdout); self.assertEqual(r['result']['result'],'timeout')
            self.assertTrue(r['result']['leader_reaped']);self.assertTrue(r['descendant_reaped'])

    def test_runner_cleans_group_after_normal_leader_and_closed_stdout(self):
        with tempfile.TemporaryDirectory() as d:
            p=subprocess.run([sys.executable,'-I','-S','-c',NATIVE_HARNESS,str(CI),d,'closed'],
              capture_output=True,text=True,timeout=8,env=RUN.clean_env(Path(d)))
            self.assertEqual(p.returncode,0,p.stderr)
            r=json.loads(p.stdout);self.assertEqual(r['result']['result'],'pass')
            self.assertTrue(r['descendant_reaped'])

    def test_runner_closed_stdout_does_not_remove_deadline(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            r=RUN.run_command([sys.executable,'-I','-S','-c','import os,time;os.close(1);os.close(2);time.sleep(5)'],
                 root,root/'log',RUN.clean_env(root),0.2)
            self.assertEqual(r['result'],'timeout');self.assertTrue(r['leader_reaped'])
            self.assertLess(r['seconds'],3)

    def test_runner_output_bound_is_failure_not_truncated_success(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);old=RUN.MAX_LOG
            try:
                RUN.MAX_LOG=4096
                r=RUN.run_command([sys.executable,'-I','-S','-c','print("x"*32768)'],root,root/'log',RUN.clean_env(root),2)
            finally:RUN.MAX_LOG=old
            self.assertEqual(r['result'],'fail');self.assertEqual(r['reason'],'log-size-limit')
            self.assertEqual((root/'log').stat().st_size,4096)

    def test_runner_refuses_automatic_reaping(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);previous=signal.signal(signal.SIGCHLD,signal.SIG_IGN)
            try:
                with self.assertRaises(ValueError):
                    RUN.run_command([sys.executable,'-c','pass'],root,root/'log',RUN.clean_env(root),2)
            finally:signal.signal(signal.SIGCHLD,previous)
            self.assertFalse((root/'log').exists())

    def test_pidfd_observes_without_reaping(self):
        child=subprocess.Popen(['/usr/bin/true'],stdin=subprocess.DEVNULL,
          stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        pid=child.pid
        fd=-1;reaped=False
        try:
            fd=os.pidfd_open(pid);import select
            poll=select.poll();poll.register(fd,select.POLLIN)
            self.assertTrue(poll.poll(1000))
            v=os.waitid(os.P_PID,pid,os.WEXITED|os.WNOWAIT)
            self.assertEqual(v.si_pid,pid)
            self.assertEqual(child.wait(),0);reaped=True
        finally:
            if fd>=0:os.close(fd)
            if not reaped:child.wait()

    def test_statx_ctime_layout_matches_native_stat(self):
        libc=ctypes.CDLL(None,use_errno=True)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'f';p.write_bytes(b'abc')
            fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
            try:
                b=ctypes.create_string_buffer(256)
                self.assertEqual(libc.statx(fd,b'',0x1000,0x13df,b),0)
                mask=struct.unpack_from('<I',b,0)[0];self.assertEqual(mask&0x13df,0x13df)
                st=os.fstat(fd)
                self.assertEqual(struct.unpack_from('<q',b,96)[0]*10**9+struct.unpack_from('<I',b,104)[0],st.st_ctime_ns)
                self.assertEqual(struct.unpack_from('<q',b,112)[0]*10**9+struct.unpack_from('<I',b,120)[0],st.st_mtime_ns)
            finally:os.close(fd)

    def test_ctime_detects_inplace_change_with_restored_mtime(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'f';p.write_bytes(b'abc');a=p.stat();time.sleep(.005)
            p.write_bytes(b'xyz');os.utime(p,ns=(a.st_atime_ns,a.st_mtime_ns));b=p.stat()
            self.assertEqual((a.st_ino,a.st_size,a.st_mtime_ns),(b.st_ino,b.st_size,b.st_mtime_ns))
            self.assertNotEqual(a.st_ctime_ns,b.st_ctime_ns)

    def test_fd_and_path_differ_after_replacement(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'f';q=Path(d)/'q';p.write_bytes(b'abc');q.write_bytes(b'abc')
            fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
            try:os.replace(q,p);self.assertNotEqual(os.fstat(fd).st_ino,p.stat().st_ino)
            finally:os.close(fd)

class ExplicitSourceRegressions(unittest.TestCase):
    def text(self,path):return (ROOT/path).read_text()
    def test_ada_uses_pidfd_until_cleanup(self):
        s=self.text('assurance/runtime/mc_command.adb')
        self.assertIn('Pidfd_Open(Child,0)',s)
        outer=s[s.index('      Output_Open:=True;'):]
        self.assertNotIn('Waitpid(',outer)
        self.assertIn('Child_Exited and then not Output_Open',outer)
        self.assertIn('Terminate_Child;',outer)
        self.assertNotIn('Child_Done',s)
    def test_command_checks_executable_attributes_after_hash(self):
        s=self.text('assurance/runtime/mc_command.adb')
        self.assertLess(s.index('MC_FS.Hash(Executable'),s.index('MC_FS.Info(Executable,V_After'))
        self.assertIn('V_After/=V',s)

    def test_capture_checks_descriptor_and_final_path(self):
        s=self.text('pkgcore/runtime/pkg_file_engine.adb')
        s=s[s.index('   procedure Capture('):s.index('   end Capture;')]
        self.assertIn('Opened/=V',s);self.assertIn('Observed_After/=Opened',s)
        self.assertIn('Observed_After/=V',s)
    def test_existing_writer_lock_is_not_recreated(self):
        for path,token in [('pkgcore/runtime/pkg_file_engine.adb','C.Root_Lock,Status,Create_If_Missing=>False'),
                           ('pkgcore/runtime/pkg_scrubber.adb','Lock,Status,Create_If_Missing=>False')]:
            self.assertIn(token,self.text(path))
        s=self.text('statecore/runtime/state_network_controller.adb')
        self.assertNotIn('MC_FS.Open_Locked (R,"network.lock",L,Status);',s[s.index('   procedure Advance_And_Dispatch'):])
    def test_store_open_does_not_bootstrap(self):
        s=self.text('assurance/runtime/mc_store.adb')
        opened=s[s.index('   procedure Open (Path : String;'):s.index('   end Open;')]
        self.assertIn('Create_If_Missing=>False',opened)
        self.assertNotIn('Need_Directory(',opened)
        self.assertNotIn('Make_Directory(',opened)
        self.assertIn("MC_SHA256.Hash(Data(Data'First",s)
        init=s[s.index('   procedure Initialize'):s.index('   end Initialize;')]
        self.assertIn('Names.Count/=0',init)
        self.assertIn('MC_FS.Create_New',init)

    def test_record_budget_checked_before_request_intent(self):
        s=self.text('assurance/runtime/mc_gate.adb')
        self.assertLess(s.index('MC_Log.Can_Append'),s.index('MC_Log.Append'))
        self.assertIn('After_Tail_Repair=>True',s)
    def test_native_generation_is_not_membership_epoch(self):
        s=self.text('pkgcore/runtime/pkg_resolution_engine.adb')
        self.assertNotIn('Expected.Generation /= Epoch',s)
        self.assertIn('Check_Native (',s);self.assertIn('Recheck_Current (',s)
    def test_composed_engine_no_weak_instance_export(self):
        spec=self.text('pkgcore/runtime/pkg_managed_engine.ads')
        body=self.text('pkgcore/runtime/pkg_managed_engine.adb')
        self.assertNotIn('new Pkg_Quiescent_Engine',spec)
        self.assertIn('Pkg_Configuration_Engine(Stopped.Guard',body)
        self.assertIn('Pkg_Resolution_Engine(Configured.Guard',body)
    def test_admission_reserves_existing_workflow_results(self):
        s=self.text('controlcore/runtime/ctl_store.adb')
        self.assertIn('Completion_Reserve(C)',s);self.assertIn('Completion_Reserve(C,I,N)',s)
        self.assertIn('Exact repeated UNKNOWN observation is a no-op',s)

class ReferenceBudgetTests(unittest.TestCase):
    def test_bounded_arithmetic_matches_unbounded_reference(self):
        for limit in (0,1,2,8,32,2**63-1):
            points={0,1,2,8,max(0,limit-1),limit}
            for used in points:
                for pending in points:
                    for added in points:
                        fits=used<=limit and pending<=limit-used and added<=limit-used-pending
                        self.assertEqual(fits,used+pending+added<=limit)
    def test_intent_cannot_consume_completion_slot(self):
        for used in range(32):
            if used+8<=32:
                after=used+2
                self.assertGreaterEqual(32-after,6) # bounded recovery and repair reserve
    def test_manager_budget_all_stages(self):
        remaining={'waiting':3,'sent':2,'unknown':1,'completed':0,'failed':0}
        for before,after in [('waiting','sent'),('sent','unknown'),('sent','completed'),('unknown','failed')]:
            self.assertLessEqual(1+remaining[after],remaining[before])

if __name__=='__main__':unittest.main()
