-- SPDX-License-Identifier: BSD-3-Clause
-- Private temporary root, synthetic policy only; no worker is started.
with Ada.Command_Line;
with MC_Types;use MC_Types;with MC_Runtime;with MC_FS;with MC_Atomic;
with MC_Contract_Profile;with MC_Site_Policy;with MC_Receiver_Ledger;
with Test_Support;use Test_Support;
procedure Run_Receiver_Ledger_Tests with SPARK_Mode=>Off is
   use type MC_FS.Entry_Kind;use type MC_Receiver_Ledger.Receipt_State;
   R,Policy_Root : MC_FS.Root;F : MC_FS.File;P : MC_Site_Policy.Policy;
   Receipt : MC_Receiver_Ledger.Receipt;Info : MC_FS.Entry_Info;S : Outcome;
   Root_ID : constant Identity:=(others=>9);
   procedure Need(Name : String) is begin Expect(S=OK,Name&Outcome'Image(S));end;
begin
   Expect(Ada.Command_Line.Argument_Count=1,"fresh private root");MC_Runtime.Initialize(S);Need("runtime");
   MC_FS.Open_Root(Ada.Command_Line.Argument(1),R,S,Private_Only=>True);Need("private root");
   MC_FS.Make_Directory(R,"policy",S);Need("private policy");
   MC_FS.Open_Root(Ada.Command_Line.Argument(1)&"/policy",Policy_Root,S,Private_Only=>True);Need("open policy");
   P.Root_ID:=Root_ID;P.Scope.Resource_ID:=Root_ID;P.Scope.Cluster_ID:=(others=>1);P.Scope.Node_ID:=(others=>2);
   P.Scope.Membership_Epoch:=1;P.Scope.Fence_Token:=1;P.Scope.Allowed:=(others=>True);
   P.Request_Key:=(others=>8);P.Observers:=(others=>(others=>7));P.Contract:=MC_Contract_Profile.Fingerprint;
   P.Serial:=1;P.Valid_Until:=Counter'Last;
   MC_Atomic.Write(Policy_Root,"policy.bin",MC_Site_Policy.Encode(P),True,S);Need("synthetic public policy");MC_FS.Close(Policy_Root);
   MC_Receiver_Ledger.Provision(Ada.Command_Line.Argument(1)&"/policy",Ada.Command_Line.Argument(1),"ledger",S);Need("explicit ledger provisioning");
   MC_Receiver_Ledger.Provision(Ada.Command_Line.Argument(1)&"/policy",Ada.Command_Line.Argument(1),"ledger",S);
   Expect(S=Conflict,"never reinitialize an existing ledger");
   MC_Receiver_Ledger.Observe(Ada.Command_Line.Argument(1)&"/ledger",Root_ID,Root_ID,(others=>2),Receipt,S);
   Need("genesis is not a request with the same ID");Expect(Receipt.State=MC_Receiver_Ledger.Not_Recorded,"not recorded is explicit");
   MC_FS.Rename(R,"ledger/requests.log","ledger/saved.log",True,S);Need("simulate missing ledger");
   MC_Receiver_Ledger.Observe(Ada.Command_Line.Argument(1)&"/ledger",Root_ID,(others=>3),(others=>2),Receipt,S);
   Expect(S/=OK,"missing ledger never means an absent request");MC_FS.Stat(R,"ledger/requests.log",Info,S);Need("stat");
   Expect(Info.Kind=MC_FS.Absent,"observer did not manufacture replacement history");
   MC_FS.Create_New(R,"ledger/requests.log",F,S);Need("empty corruption fixture");MC_FS.Sync(F,S);Need("sync fixture");MC_FS.Close(F);
   MC_Receiver_Ledger.Observe(Ada.Command_Line.Argument(1)&"/ledger",Root_ID,(others=>3),(others=>2),Receipt,S);
   Expect(S=Corrupt,"empty replacement ledger rejected");MC_FS.Close(R);Report;
exception when others=>MC_FS.Close(F);MC_FS.Close(R);MC_FS.Close(Policy_Root);raise;
end Run_Receiver_Ledger_Tests;
