-- SPDX-License-Identifier: BSD-3-Clause
-- Runs only itself and its freshly forked harmless sleeping children. Never
-- targets services, pre-existing PIDs or production files. Private test process.
with Ada.Command_Line; with Ada.Directories; with Ada.Text_IO;
with Interfaces.C;
with MC_Types; use MC_Types;
with MC_Posix; with MC_Runtime; with MC_Command; with MC_FS; with MC_Clock; with MC_Text;
with Test_Support; use Test_Support;
procedure Run_Command_Lifecycle_Tests with SPARK_Mode => Off is
   use Interfaces.C;
   use type MC_Command.Completion;
   function Dup2(A,B : int) return int with Import,Convention=>C,External_Name=>"dup2";
   type Saved_Descriptors is array(0..2) of int;
   Saved : Saved_Descriptors := (others=>-1);
   function Fork return int with Import,Convention=>C,External_Name=>"fork";
   function Prctl(Opt : int; A,B,C,D : unsigned_long) return int
     with Import,Convention=>C,External_Name=>"prctl";
   function Close_FD(D : int) return int with Import,Convention=>C,External_Name=>"close";
   function Sleep_Us(N : unsigned) return int with Import,Convention=>C,External_Name=>"usleep";
   function Waitpid(P : int; Status : access int; Flags : int) return int
     with Import,Convention=>C,External_Name=>"waitpid";
   procedure Child_Exit(Code : int) with Import,Convention=>C,External_Name=>"_exit",No_Return;
   R : MC_FS.Root; F : MC_FS.File; S : Outcome; D : Digest; Size, Now : Counter;
   Command : MC_Command.Invocation; Result : MC_Command.Result;
   Child, RC : int; WS : aliased int := 0;
   Input : Bytes(1..0);
   procedure Need(Label_Text : String) is begin Expect(S=OK,Label_Text & Outcome'Image(S)); end;
   procedure Restore_Standard_Streams is
   begin
      for I in Saved'Range loop
         if Saved(I)>=0 then RC:=Dup2(Saved(I),int(I)); RC:=Close_FD(Saved(I)); Saved(I):=-1; end if;
      end loop;
   end Restore_Standard_Streams;
begin
   Expect(Ada.Command_Line.Argument_Count=1,"one private directory or internal helper mode");
   if Ada.Command_Line.Argument(1) in "helper-hold" | "helper-close" then
      Child:=Fork;
      if Child<0 then Child_Exit(126); end if;
      if Child=0 then
         if Ada.Command_Line.Argument(1)="helper-close" then
            RC:=Close_FD(1); RC:=Close_FD(2);
         end if;
         RC:=Sleep_Us(5_000_000); Child_Exit(0);
      end if;
      Ada.Text_IO.Put_Line(int'Image(Child)); Ada.Text_IO.Flush;
      Child_Exit(0);
   end if;
   MC_Runtime.Initialize(S); Need("runtime");
   RC:=Prctl(36,1,0,0,0); Expect(RC=0,"test-only subreaper");
   declare
      Path : constant String := Ada.Directories.Full_Name(Ada.Command_Line.Command_Name);
   begin
      MC_FS.Open_Root(Ada.Directories.Containing_Directory(Path),R,S); Need("executable directory");
      MC_FS.Open_Read(R,Ada.Directories.Simple_Name(Path),F,S); Need("self executable");
      MC_FS.Hash(F,512*1024*1024,D,Size,S); Need("self digest");
      MC_FS.Close(F); MC_FS.Close(R);
      MC_Text.Set(Command.Executable,Path,S); Need("executable path");
   end;
   Command.Executable_Digest:=D; Command.Count:=1;
   for Mode in 1..3 loop
      MC_Text.Set(Command.Arguments(1),(if Mode=1 then "helper-hold" else "helper-close"),S); Need("mode");
      MC_Clock.Boottime_Milliseconds(Now,S); Need("clock"); Command.Deadline:=Now+500;
      if Mode=3 then
         for I in Saved'Range loop
            Saved(I):=MC_Posix.Dup(int(I),1030,64);
            Expect(Saved(I)>=64,"save standard descriptor before private test");
         end loop;
         for I in Saved'Range loop RC:=Close_FD(int(I)); end loop;
      end if;
      MC_Command.Run(Command,Input,Result,S);
      Restore_Standard_Streams;
      if Mode=1 then Expect(Result.State=MC_Command.Timed_Out,"inherited stdout bounded after leader exit");
      else
         Expect((Result.State=MC_Command.Exited and then S=OK),"normal leader cleanup");
      end if;
      Expect(Result.Used>0 and then Result.Used<32,"single child pid result");
      declare Text : String(1..Result.Used); Reaped : Boolean:=False; begin
         for I in Text'Range loop Text(I):=Character'Val(Result.Output(I)); end loop;
         Expect(Text'Length>1 and then Text(Text'Last)=ASCII.LF,"child pid line");
         Child:=int'Value(Text(Text'First..Text'Last-1)); Expect(Child>0,"known test descendant");
         for Attempt in 1..200 loop
            RC:=Waitpid(Child,WS'Access,1);
            if RC=Child then Reaped:=True; exit; end if;
            RC:=Sleep_Us(10_000);
         end loop;
         Expect(Reaped and then WS mod 128=9,"known descendant terminated, not leaked");
      end;
   end loop;
   Report;
exception when others => Restore_Standard_Streams; MC_FS.Close(F); MC_FS.Close(R); raise;
end Run_Command_Lifecycle_Tests;
