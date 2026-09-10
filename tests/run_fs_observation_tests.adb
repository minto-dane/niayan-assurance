-- SPDX-License-Identifier: BSD-3-Clause
-- Private harness directory only; never accepts an existing data file.
with Ada.Command_Line;
with Interfaces.C;
with MC_Types; use MC_Types;
with MC_FS; with MC_Atomic; with MC_Runtime; with MC_Posix;
with Test_Support; use Test_Support;
procedure Run_FS_Observation_Tests with SPARK_Mode => Off is
   use type MC_Types.Wide;
   use type MC_Types.Word;
   R : MC_FS.Root; F : MC_FS.File; S : Outcome;
   First, Changed, Final : MC_FS.Entry_Info;
   Times : aliased MC_Posix.Timespec_Pair;
   RC : Interfaces.C.int;
   use type MC_FS.Entry_Info;
   use type Interfaces.C.int;
   procedure Need(N : String) is begin Expect(S=OK,N & Outcome'Image(S)); end;
begin
   Expect(Ada.Command_Line.Argument_Count=1,"fresh directory argument");
   MC_Runtime.Initialize(S); Need("runtime");
   MC_FS.Open_Root(Ada.Command_Line.Argument(1),R,S,Private_Only=>True); Need("private directory");
   MC_Atomic.Write(R,"observed",Bytes'(1,2,3,4),True,S); Need("initial file");
   MC_FS.Open_Locked(R,"observed",F,S,Create_If_Missing=>False); Need("existing file");
   MC_FS.Info(F,First,S); Need("first statx");
   delay 0.02;
   RC:=MC_Posix.Fchmod(Interfaces.C.int(MC_FS.Native(F)),8#640#);
   Expect(RC=0,"change fixture mode");
   RC:=MC_Posix.Fchmod(Interfaces.C.int(MC_FS.Native(F)),Interfaces.C.unsigned(First.Mode));
   Expect(RC=0,"restore fixture mode");
   Times(0):=(Sec=>0,Nsec=>1_073_741_822); -- UTIME_OMIT
   Times(1):=(Sec=>Interfaces.C.long(First.Mtime_Sec),Nsec=>Interfaces.C.long(First.Mtime_Nsec));
   RC:=MC_Posix.Futimens(Interfaces.C.int(MC_FS.Native(F)),Times'Address);
   Expect(RC=0,"restore fixture mtime, not ctime");
   MC_FS.Info(F,Changed,S); Need("changed statx");
   Expect(Changed.Mode=First.Mode and then Changed.Mtime_Sec=First.Mtime_Sec
     and then Changed.Mtime_Nsec=First.Mtime_Nsec,"old observed attributes restored");
   Expect(Changed.Ctime_Sec/=First.Ctime_Sec or else Changed.Ctime_Nsec/=First.Ctime_Nsec,
     "change detected despite restored mtime");
   MC_Atomic.Write(R,"replacement",Bytes'(1,2,3,4),True,S); Need("new inode");
   MC_FS.Rename(R,"replacement","observed",False,S); Need("replace path");
   MC_FS.Stat(R,"observed",Final,S); Need("path postimage");
   Expect(Final.Inode/=Changed.Inode,"opened descriptor and replaced pathname differ");
   MC_FS.Close(F); MC_FS.Close(R); Report;
exception when others => MC_FS.Close(F); MC_FS.Close(R); raise;
end Run_FS_Observation_Tests;
