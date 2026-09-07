-- SPDX-License-Identifier: MIT
-- PRIVATE TEST ROOTS ONLY. Synthetic records; no production credentials or services.
with Ada.Command_Line; with Ada.Directories;
with MC_Types; use MC_Types;
with MC_Runtime; with MC_FS; with MC_Log; with MC_Log_Format;
with MC_Atomic; with MC_SHA256; with MC_Store;
with Test_Support; use Test_Support;
procedure Run_Recovery_Storage_Tests with SPARK_Mode => Off is
   R : MC_FS.Root; F : MC_FS.File; J : MC_Log.Journal; Store,Other_Store : MC_Store.Store;
   S : Outcome; I : MC_FS.Entry_Info;
   Root_ID : constant Identity := (others => 21);
   E : MC_Log_Format.Log_Entry := (Kind=>1,Root_ID=>Root_ID,Operation_ID=>(others=>22),others=><>);
   D, Wrong : Digest;
   B : Bytes(1..256); Used : Natural;
   Search : Ada.Directories.Search_Type; File_Entry : Ada.Directories.Directory_Entry_Type;
   Files : Natural := 0;
   procedure Need (Name : String) is begin Expect(S=OK,Name & Outcome'Image(S)); end;
   use type MC_FS.Entry_Kind;
begin
   Expect(Ada.Command_Line.Argument_Count=2,"two fresh private directories");
   MC_Runtime.Initialize(S); Need("runtime");
   MC_FS.Open_Root(Ada.Command_Line.Argument(1),R,S,Private_Only=>True); Need("private root");
   MC_Log.Open(R,"lost.log",Root_ID,J,S,Create_If_Missing=>False);
   Expect(S=Corrupt,"missing recovery journal refused");
   MC_FS.Stat(R,"lost.log",I,S); Need("missing stat");
   Expect(I.Kind=MC_FS.Absent,"refusal did not create a journal");
   MC_Log.Close(J);
   MC_Log.Open(R,"active.log",Root_ID,J,S); Need("initial provisioning");
   MC_Log.Append(J,E,S); Need("durable record"); MC_Log.Close(J);
   MC_FS.Open_Locked(R,"active.log",F,S,Create_If_Missing=>False); Need("existing only");
   MC_FS.Append_Durable(F,256,Bytes'(1,2,3,4,5),S); Need("test partial suffix"); MC_FS.Close(F);
   MC_Log.Open(R,"active.log",Root_ID,J,S,Create_If_Missing=>False);
   Expect(S=Indeterminate and then MC_Log.Has_Torn_Tail(J),"partial tail quarantined");
   MC_Log.Export_Tail(J,B,Used,S); Need("export suffix");
   D:=MC_SHA256.Hash(B(1..Used)); Wrong:=(others=>1);
   MC_Log.Repair_Tail(J,Wrong,S); Expect(S=Denied,"wrong preservation digest denied");
   MC_Atomic.Write(R,"preserved-tail.bin",B(1..Used),True,S); Need("preserve before repair");
   MC_Log.Repair_Tail(J,D,S); Need("authorized tail primitive"); MC_Log.Close(J);
   MC_FS.Open_Locked(R,"active.log",F,S,Create_If_Missing=>False); Need("open for corruption fixture");
   B:=(others=>0); MC_FS.Append_Durable(F,256,B,S); Need("full bad frame fixture"); MC_FS.Close(F);
   MC_Log.Open(R,"active.log",Root_ID,J,S,Create_If_Missing=>False);
   Expect(S=Corrupt,"full bad frame never repaired implicitly"); MC_Log.Close(J);
   MC_FS.Stat(R,"active.log",I,S); Need("preserved record stat");
   Expect(I.Size=512,"corrupt record preserved"); MC_FS.Close(R);
   MC_Store.Open(Ada.Command_Line.Argument(2),Store,S);
   Expect(S=Corrupt,"missing store does not bootstrap in Open");
   MC_FS.Open_Root(Ada.Command_Line.Argument(2),R,S,Private_Only=>True); Need("store fixture directory");
   MC_FS.Stat(R,"store.lock",I,S); Need("missing store lock stat");
   Expect(I.Kind=MC_FS.Absent,"ordinary Open did not create a lock");
   MC_Store.Initialize(Ada.Command_Line.Argument(2),Store,S); Need("explicit store initialize");
   MC_Store.Initialize(Ada.Command_Line.Argument(2),Other_Store,S);
   Expect(S=Conflict,"cannot reinitialize existing store");
   MC_FS.Rename(R,"store.lock","preserved-store.lock",True,S); Need("test missing lock");
   MC_Store.Open(Ada.Command_Line.Argument(2),Other_Store,S);
   Expect(S=Corrupt,"cannot split writer authority by recreating lock");
   MC_FS.Stat(R,"store.lock",I,S); Need("no replacement lock stat");
   Expect(I.Kind=MC_FS.Absent,"no new lock while old descriptor still held");
   MC_FS.Rename(R,"preserved-store.lock","store.lock",True,S); Need("restore same lock inode");
   MC_Store.Put(Store,Bytes'(9,8,7),D,S); Need("object");
   for N in 1..20 loop
      MC_Store.Pin(Store,Root_ID,D,S); Need("same pin replay" & Natural'Image(N));
   end loop;
   MC_Store.Close(Store);
   MC_FS.Rename(R,"pins","preserved-pins",True,S); Need("test missing pin directory");
   MC_Store.Open(Ada.Command_Line.Argument(2),Other_Store,S);
   Expect(S=Corrupt,"missing pins directory is not empty pins");
   MC_FS.Stat(R,"pins",I,S); Need("missing pins stat");
   Expect(I.Kind=MC_FS.Absent,"Open did not recreate pins");
   MC_FS.Rename(R,"preserved-pins","pins",True,S); Need("restore same pins");
   MC_Store.Open(Ada.Command_Line.Argument(2),Other_Store,S); Need("ordinary reopen");
   MC_Store.Read_Object(Other_Store,D,B,Used,S); Need("rehash exact consumed bytes");
   Expect(Used=3 and then B(1..3)=Bytes'(9,8,7),"read expected object");
   MC_Store.Close(Other_Store); MC_FS.Close(R);
   Ada.Directories.Start_Search(Search,Ada.Command_Line.Argument(2)&"/incoming","*",
      (Ada.Directories.Ordinary_File=>True,others=>False));
   while Ada.Directories.More_Entries(Search) loop
      Ada.Directories.Get_Next_Entry(Search,File_Entry);
      Expect(Ada.Directories.Simple_Name(File_Entry)'Length>0,"ordinary file name"); Files:=Files+1;
   end loop;
   Ada.Directories.End_Search(Search);
   Expect(Files=0,"pin retries do not leak staging files");
   Report;
exception when others =>
   MC_FS.Close(F); MC_FS.Close(R); MC_Log.Close(J); MC_Store.Close(Store); MC_Store.Close(Other_Store); raise;
end Run_Recovery_Storage_Tests;
