-- SPDX-License-Identifier: BSD-3-Clause
with MC_Types; use MC_Types;
with MC_File_IO; with MC_Signatures; with MC_Protocol; with MC_Ingress;
with MC_Authorization; with MC_Replay; with MC_Requests;
with Test_Support; use Test_Support;
procedure Run_Ingress_Tests with SPARK_Mode => Off is
   use type Byte; use type MC_Replay.Decision; use type MC_Replay.Window;
   Raw : Bytes := MC_File_IO.Read_File("fixtures/request-header.bin",160);
   Body_Data : Bytes := MC_File_IO.Read_File("fixtures/request-body.bin",192);
   Sig : constant MC_Signatures.Signature := MC_File_IO.Read_File("fixtures/request.sig",64);
   Key : constant MC_Signatures.Public_Key := MC_File_IO.Read_File("fixtures/test-authority.pub",32);
   Scope, Bad_Scope : MC_Authorization.Scope;
   Expected_Contract : constant Digest := (others=>8);
   Previous, Candidate, Saved : MC_Replay.Window;
   Request : MC_Requests.Request;
   Class : MC_Replay.Decision;
   Status : Outcome;
begin
   Scope := (Cluster_ID=>(others=>2),Node_ID=>(others=>3),Resource_ID=>(others=>4),
     Boot_ID=>(others=>5),Membership_Epoch=>1,Fence_Token=>7,
     Allowed=>(MC_Protocol.Apply_Request=>True,others=>False),Maximum_Local_Lease=>1_000);
   MC_Ingress.Check_Request(Raw,Body_Data,Sig,Key,Scope,Expected_Contract,90,Previous,Candidate,Request,Class,Status);
   Expect(Status=OK and then Class=MC_Replay.Fresh,"authenticated-scoped-request");
   Saved := Candidate;
   MC_Ingress.Check_Request(Raw,Body_Data,Sig,Key,Scope,Expected_Contract,90,Saved,Candidate,Request,Class,Status);
   Expect(Status=OK and then Class=MC_Replay.Exact_Retry and then Candidate=Saved,"retry-inspect-not-reexecute");
   MC_Ingress.Check_Request(Raw,Body_Data,Sig,Key,Scope,Expected_Contract,100,Previous,Candidate,Request,Class,Status);
   Expect(Status/=OK and then Candidate=Previous,"lease-expiration-boundary");
   Bad_Scope := Scope; Bad_Scope.Fence_Token := 8;
   MC_Ingress.Check_Request(Raw,Body_Data,Sig,Key,Bad_Scope,Expected_Contract,90,Previous,Candidate,Request,Class,Status);
   Expect(Status/=OK and then Candidate=Previous,"old-fence-ingress");
   Bad_Scope := Scope; Bad_Scope.Boot_ID := (others=>6);
   MC_Ingress.Check_Request(Raw,Body_Data,Sig,Key,Bad_Scope,Expected_Contract,90,Previous,Candidate,Request,Class,Status);
   Expect(Status/=OK and then Candidate=Previous,"receiver-reboot-invalidates-lease");
   MC_Ingress.Check_Request(Raw,Body_Data,Sig,Key,Scope,(others=>4),90,Previous,Candidate,Request,Class,Status);
   Expect(Status/=OK and then Candidate=Previous,"signed-but-unknown-contract-denied");
   for J in Raw'Range loop
      Raw(J) := Raw(J) xor 1;
      MC_Ingress.Check_Request(Raw,Body_Data,Sig,Key,Scope,Expected_Contract,90,Previous,Candidate,Request,Class,Status);
      Expect(Status/=OK and then Candidate=Previous,"signed-header-tamper");
      Raw(J) := Raw(J) xor 1;
   end loop;
   for J in Body_Data'Range loop
      Body_Data(J) := Body_Data(J) xor 1;
      MC_Ingress.Check_Request(Raw,Body_Data,Sig,Key,Scope,Expected_Contract,90,Previous,Candidate,Request,Class,Status);
      Expect(Status/=OK and then Candidate=Previous,"body-tamper");
      Body_Data(J) := Body_Data(J) xor 1;
   end loop;
   Report;
end Run_Ingress_Tests;
