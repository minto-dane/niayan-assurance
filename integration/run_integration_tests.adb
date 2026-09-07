-- SPDX-License-Identifier: MIT
with MC_Types; use MC_Types;
with MC_Requests; with MC_Protocol; with MC_SHA256;
with Pkg_Transactions; with State_Changes;
with Test_Support; use Test_Support;
procedure Run_Integration_Tests with SPARK_Mode => Off is
   use type MC_Requests.Request;
   use type Pkg_Transactions.Effect;
   use type Pkg_Transactions.Phase;
   use type State_Changes.Phase;
   use type State_Changes.Action;
   Request, Parsed : MC_Requests.Request;
   H : MC_Protocol.Header;
   Raw : MC_Requests.Request_Bytes;
   Status : Outcome;
   Tx : Pkg_Transactions.Transaction;
   PE : Pkg_Transactions.Evidence;
   PA : Pkg_Transactions.Effect;
   Change : State_Changes.Change;
   CE : State_Changes.Observation;
   CA : State_Changes.Action;
   procedure P (C : Pkg_Transactions.Command) is
   begin
      PE.Expected_Revision := Tx.Revision;
      Pkg_Transactions.Step(Tx,C,PE,PA,Status);
      Expect(Status=OK,"package-transition");
   end P;
   procedure C (E : State_Changes.Event) is
   begin
      CE.Expected_Revision := Change.Revision;
      State_Changes.Advance(Change,E,CE,CA,Status);
      Expect(Status=OK,"cluster-transition");
   end C;
begin
   Request := (Action=>MC_Requests.Apply,Transaction_ID=>(others=>1),Plan_Digest=>(others=>2),
     Contract_Digest=>(others=>3),Expected_Revision=>0,Base_Generation=>1,Stage_Set_Digest=>(others=>4),Evidence_Digest=>Zero_Digest);
   Raw := MC_Requests.Encode(Request); MC_Requests.Decode(Raw,Parsed,Status);
   Expect(Status=OK and then Parsed=Request,"request-roundtrip");
   H.Kind := MC_Protocol.Apply_Request; H.Body_Length := Raw'Length;
   H.Body_Digest := MC_SHA256.Hash(Raw);
   Expect(MC_Requests.Header_Binds(H,Parsed),"request-header-binding");
   H.Kind := MC_Protocol.Recover_Request;
   Expect(not MC_Requests.Header_Binds(H,Parsed),"cross-operation-confusion-rejected");
   Tx := (ID=>(others=>1),Plan_Digest=>(others=>2),Base_Generation=>1,
     Membership_Epoch=>1,Fence_Token=>7,others=><>);
   PE := (Expected_Revision=>0,Observed_Generation=>1,Membership_Epoch=>1,Fence_Token=>7,
     Now=>90,Lease_Deadline=>100,Bound_Plan=>Tx.Plan_Digest,others=>True);
   Change := (ID=>(others=>8),Cluster_ID=>(others=>2),Target_Node=>(others=>3),
     Resource_ID=>(others=>4),Plan_Digest=>Tx.Plan_Digest,Membership_Epoch=>1,Fence_Token=>7,
     others=><>);
   CE := (Expected_Revision=>0,Membership_Epoch=>1,Fence_Token=>7,Now=>90,Lease_Deadline=>100,
     Bound_Change=>Change.ID,Bound_Plan=>Change.Plan_Digest,others=>True);
   C(State_Changes.Request_Drain); C(State_Changes.Confirm_Drained);
   P(Pkg_Transactions.Validate_Plan); P(Pkg_Transactions.Record_Staged);
   P(Pkg_Transactions.Record_Quiesced);
   C(State_Changes.Confirm_Prepared); C(State_Changes.Request_Apply);
   Expect(CA=State_Changes.Ask_Package_Apply,"cluster-requests-package-change");
   P(Pkg_Transactions.Begin_Apply); Expect(PA=Pkg_Transactions.Apply_Files,"bounded-write-proposal");
   P(Pkg_Transactions.Record_Applied); P(Pkg_Transactions.Begin_Check);
   C(State_Changes.Confirm_Applied);
   CE.Package_Committed := False; CE.Expected_Revision := Change.Revision;
   State_Changes.Advance(Change,State_Changes.Confirm_Healthy,CE,CA,Status);
   Expect(Status/=OK and then Change.Current=State_Changes.Checking,"cannot-accept-uncommitted-package");
   P(Pkg_Transactions.Record_Verified); P(Pkg_Transactions.Begin_Commit);
   P(Pkg_Transactions.Record_Committed);
   CE.Package_Committed := Tx.Current=Pkg_Transactions.Committed;
   C(State_Changes.Confirm_Healthy); C(State_Changes.Request_Rejoin); C(State_Changes.Confirm_Rejoined);
   Expect(Change.Current=State_Changes.Completed,"coordinated-finish");
   Report;
end Run_Integration_Tests;
