-- SPDX-License-Identifier: BSD-3-Clause
with MC_Types; use MC_Types;
with MC_Codec; with MC_Hex; with MC_SHA256; with MC_Protocol;
with MC_Replay; with MC_Paths; with MC_Compatibility; with MC_Release;
with Test_Support; use Test_Support;
procedure Run_Contract_Tests with SPARK_Mode => Off is
   use type Byte; use type Word; use type Wide;
   use type MC_Replay.Decision;
   use type MC_Replay.Window;
   use type MC_Protocol.Header;
   function B (S : String) return Bytes is
      Result : Bytes(1..S'Length);
   begin
      for J in S'Range loop Result(J-S'First+1) := Character'Pos(S(J)); end loop;
      return Result;
   end B;
   H, Parsed : MC_Protocol.Header;
   Raw : MC_Protocol.Frame_Header;
   Status : Outcome;
   W, Saved : MC_Replay.Window;
   D : MC_Replay.Decision;
   A,Peer : MC_Compatibility.Contract_Descriptor;
   Evidence : MC_Release.Evidence_Set := (others => MC_Release.Passed);
   Buffer : Bytes(1..16) := (others => 0);
   Hash_Context : MC_SHA256.Context := MC_SHA256.Initialize;
   Chunk : constant Bytes(1..1_000) := (others => Character'Pos('a'));
begin
   Expect(MC_Hex.Encode(MC_SHA256.Hash(B(""))) =
     "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","sha-empty");
   Expect(MC_Hex.Encode(MC_SHA256.Hash(B("abc"))) =
     "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad","sha-abc");
   for J in 1..1_000 loop MC_SHA256.Update(Hash_Context,Chunk); end loop;
   Expect(MC_Hex.Encode(MC_SHA256.Finish(Hash_Context)) =
     "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0","sha-million-a");
   MC_Codec.Put16(Buffer,1,65_535); Expect(MC_Codec.U16(Buffer,1)=65_535,"codec-u16");
   MC_Codec.Put32(Buffer,3,Word'Last); Expect(MC_Codec.U32(Buffer,3)=Word'Last,"codec-u32");
   MC_Codec.Put64(Buffer,7,Wide'Last); Expect(MC_Codec.U64(Buffer,7)=Wide'Last,"codec-u64");
   H.Request_ID := (others=>1); H.Cluster_ID := (others=>2); H.Node_ID := (others=>3);
   H.Resource_ID := (others=>4); H.Boot_ID := (others=>5);
   H.Membership_Epoch := 1; H.Fence_Token := 7; H.Sequence_Number := 1; H.Deadline := 100;
   H.Body_Digest := MC_SHA256.Hash(B(""));
   for K in MC_Protocol.Message_Kind loop
      H.Kind := K; Raw := MC_Protocol.Encode(H);
      MC_Protocol.Decode(Raw,Parsed,Status);
      Expect(Status=OK and then Parsed=H,"protocol-roundtrip");
   end loop;
   for Length in 0..159 loop
      MC_Protocol.Decode(Raw(1..Length),Parsed,Status);
      Expect(Status/=OK,"protocol-truncation");
   end loop;
   Raw := MC_Protocol.Encode(H); Raw(10) := 1;
   MC_Protocol.Decode(Raw,Parsed,Status); Expect(Status/=OK,"reserved-flags");
   Raw := MC_Protocol.Encode(H); Raw(6) := 1;
   MC_Protocol.Decode(Raw,Parsed,Status); Expect(Status=Unsupported,"version-major");
   Raw := MC_Protocol.Encode(H); Raw(8) := 1;
   MC_Protocol.Decode(Raw,Parsed,Status); Expect(Status=Unsupported,"version-minor");
   Raw := MC_Protocol.Encode(H); MC_Codec.Put64(Raw,81,Wide'Last);
   MC_Protocol.Decode(Raw,Parsed,Status); Expect(Status/=OK,"counter-overflow");
   for K in 0..255 loop
      Raw := MC_Protocol.Encode(H); Raw(9) := Byte(K);
      MC_Protocol.Decode(Raw,Parsed,Status);
      Expect((Status=OK)=(K in 1..MC_Protocol.Message_Kind'Pos(MC_Protocol.Message_Kind'Last)+1),"kind-enumeration");
   end loop;
   MC_Replay.Record_Request(W,1,1,1,(others=>1),(others=>2),D);
   Expect(D=MC_Replay.Fresh,"first-request"); Saved := W;
   MC_Replay.Record_Request(W,1,1,1,(others=>1),(others=>2),D);
   Expect(D=MC_Replay.Exact_Retry and then W=Saved,"exact-retry-no-change");
   MC_Replay.Record_Request(W,1,1,1,(others=>1),(others=>3),D);
   Expect(D=MC_Replay.Reject_Conflict and then W=Saved,"request-id-content-conflict");
   MC_Replay.Record_Request(W,2,1,1,(others=>4),(others=>3),D);
   Expect(D=MC_Replay.Reject_Stale and then W=Saved,"epoch-without-new-token");
   MC_Replay.Record_Request(W,2,2,1,(others=>4),(others=>3),D);
   Expect(D=MC_Replay.Fresh,"fresh-epoch-and-token");
   Expect(MC_Paths.Safe_Relative("usr/lib64/libc.so.6"),"safe-path");
   Expect(not MC_Paths.Safe_Relative("../etc/shadow"),"traversal");
   Expect(not MC_Paths.Safe_Relative("usr//lib"),"empty-component");
   Expect(not MC_Paths.Safe_Relative("/usr/lib"),"absolute-path");
   Expect(not MC_Paths.Safe_Relative("usr/./lib"),"dot-component");
   Expect(not MC_Paths.Safe_Component("name" & ASCII.NUL),"nul-component");
   A.Schema_Digest := (others=>1); Peer := A;
   Expect(MC_Compatibility.Compatible(A,Peer),"same-contract");
   Peer.Schema_Digest(1) := 2;
   Expect(not MC_Compatibility.Compatible(A,Peer),"schema-drift");
   Peer := A; A.Requires_Features := 4;
   Expect(not MC_Compatibility.Compatible(A,Peer),"missing-required-feature");
   Peer.Supports := 4; Expect(MC_Compatibility.Compatible(A,Peer),"required-feature");
   Expect(MC_Release.Qualified(Evidence),"complete-evidence-policy");
   for Item in MC_Release.Evidence_Item loop
      Evidence(Item) := MC_Release.Missing;
      Expect(not MC_Release.Qualified(Evidence),"missing-evidence-denied");
      Evidence(Item) := MC_Release.Passed;
   end loop;
   Expect(not MC_Release.Build_Qualified,"archive-is-not-production-qualified");
   Report;
end Run_Contract_Tests;
