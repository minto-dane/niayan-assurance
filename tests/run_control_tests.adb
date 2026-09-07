-- SPDX-License-Identifier: MIT
with Test_Support; use Test_Support;
with MC_Types; use MC_Types; with MC_Control; use MC_Control;
with MC_Control_Codec; with MC_SHA256; with MC_Checkpoint;
procedure Run_Control_Tests with SPARK_Mode => Off is
   A, Bad_A : Authority; P : Proposal; S, T : State;
   V : Verified_Set := (others => False); Status : Outcome;
   AH, SH : Digest; Raw : MC_Control_Codec.State_Frame;
   PR : MC_Control_Codec.Proposal_Frame; Parsed_P : Proposal;
   AR : MC_Control_Codec.Authority_Frame; Parsed_A : Authority;
   CP, Next_CP, Parsed_CP : MC_Checkpoint.Descriptor;
   CR : MC_Checkpoint.Frame;
   Boot : constant Identity := (others => 9);
begin
   A.Scope := (others => 1); A.Contract := (others => 2); A.Serial := 1; A.Count := 3;
   for I in 1..3 loop
      A.Keys (I).Public_Key := (others => Byte (10+I)); A.Keys (I).Principal := (others => Byte (20+I));
      A.Keys (I).Domain := I; A.Keys (I).Duty := (if I = 2 then Security else Operations);
   end loop;
   Expect (Valid (A),"authority-valid"); AH := MC_SHA256.Hash (MC_Control_Codec.Encode (A));
   P.Scope := A.Scope; P.Contract := A.Contract; P.Authority_Digest := AH;
   P.Boot_ID := Boot; P.Request_ID := (others => 3); P.Reason := (others => 4);
   P.New_Trust_Epoch := 1; P.Not_Before := 100; P.Expires := 10_000; P.Desired := Quarantined;
   V (1) := True;
   Decide (A,AH,S,Zero_Digest,True,P,V,Boot,200,T,Status);
   Expect (Status = OK and then T.Current = Quarantined and then T.Revision = 1,"signed-genesis-is-quarantined"); S := T;
   Expect (not Permits (S.Current,Activate_Service) and then Permits (S.Current,Contain),"quarantine-blocks-activation");
   SH := MC_SHA256.Hash (MC_Control_Codec.Encode (S));
   P.Desired := Running; P.Expected_Revision := 1; P.Expected_State := SH;
   P.Request_ID := (others => 5); P.New_Trust_Epoch := 2; P.Recovery_Receipt := (others => 6);
   Decide (A,AH,S,SH,False,P,V,Boot,200,T,Status);
   Expect (Status = Denied and then T = S,"one-operator-cannot-resume");
   V (3) := True; Decide (A,AH,S,SH,False,P,V,Boot,200,T,Status);
   Expect (Status = Denied,"two-operations-keys-not-two-roles"); V (3) := False; V (2) := True;
   Bad_A := A; Bad_A.Keys (2).Domain := 1;
   Decide (Bad_A,AH,S,SH,False,P,V,Boot,200,T,Status);
   Expect (Status = Denied,"same-domain-resume-denied");
   P.New_Trust_Epoch := 1; Decide (A,AH,S,SH,False,P,V,Boot,200,T,Status);
   Expect (Status = Denied,"resume-needs-new-trust-epoch"); P.New_Trust_Epoch := 2;
   P.Recovery_Receipt := Zero_Digest; Decide (A,AH,S,SH,False,P,V,Boot,200,T,Status);
   Expect (Status = Denied,"resume-needs-bound-recovery-receipt"); P.Recovery_Receipt := (others => 6);
   Decide (A,AH,S,SH,False,P,V,(others => 8),200,T,Status);
   Expect (Status = Denied,"other-boot-request-denied");
   Decide (A,AH,S,SH,False,P,V,Boot,10_000,T,Status); Expect (Status = Denied,"expiry-is-exclusive");
   Decide (A,AH,S,SH,False,P,V,Boot,200,T,Status);
   Expect (Status = OK and then T.Current = Running and then T.Revision = 2,"independent-roles-resume"); S := T;
   SH := MC_SHA256.Hash (MC_Control_Codec.Encode (S));
   P.Desired := Changes_Held; P.Expected_Revision := 2; P.Expected_State := SH; P.Request_ID := (others => 7);
   V (2) := False; Decide (A,AH,S,SH,False,P,V,Boot,300,T,Status);
   Expect (Status = OK and then not Permits (T.Current,Change_Files)
      and then Permits (T.Current,Repair_Records),"tighten-without-unlocking-recovery-policy");
   Bad_A := A; Bad_A.Keys (2).Principal := Bad_A.Keys (1).Principal;
   Expect (not Valid (Bad_A),"one-principal-not-two-votes");
   AR := MC_Control_Codec.Encode (A); MC_Control_Codec.Decode (AR,Parsed_A,Status);
   Expect (Status = OK and then Parsed_A = A,"authority-canonical-roundtrip");
   AR (90) := 1; AR (993..1_024) := MC_SHA256.Hash (AR (1..992));
   MC_Control_Codec.Decode (AR,Parsed_A,Status); Expect (Status /= OK,"reserved-authority-byte-rejected");
   PR := MC_Control_Codec.Encode (P); MC_Control_Codec.Decode (PR,Parsed_P,Status);
   Expect (Status = OK and then Parsed_P = P,"proposal-canonical-roundtrip");
   PR (258) := 1; PR (289..320) := MC_SHA256.Hash (PR (1..288));
   MC_Control_Codec.Decode (PR,Parsed_P,Status); Expect (Status /= OK,"reserved-proposal-byte-rejected");
   Raw := MC_Control_Codec.Encode (S); MC_Control_Codec.Decode (Raw,T,Status);
   Expect (Status = OK and then T = S,"control-canonical-roundtrip");
   Raw (224) := 1; Raw (225..256) := MC_SHA256.Hash (Raw (1..224));
   MC_Control_Codec.Decode (Raw,T,Status); Expect (Status /= OK,"reserved-control-byte-rejected");
   for M in Mode loop
      for O in Operation loop
         Expect (Permits (M,O) = (M = Running or else O in Inspect | Contain
            or else (M = Changes_Held and then O = Repair_Records)),"interlock-action-matrix");
      end loop;
   end loop;
   CP.Root_ID := (others => 1); CP.Stream_ID := (others => 2); CP.Contract := (others => 3);
   CP.Payload := (others => 4); CP.Generation := 1; CP.Trust_Epoch := 2;
   CP.Payload_Size := 1; CP.Audit_Receipt := (others => 5); CP.Quiescent := True;
   CP.Replay_Epoch := 3; CP.Replay_Token := 4; CP.Replay_Sequence := 5;
   Expect (MC_Checkpoint.Valid (CP),"complete-checkpoint-descriptor");
   CR := MC_Checkpoint.Encode (CP); MC_Checkpoint.Decode (CR,Parsed_CP,Status);
   Expect (Status = OK and then MC_Checkpoint.Encode (Parsed_CP) = CR,"checkpoint-roundtrip");
   Next_CP := CP; Next_CP.Generation := 2; Next_CP.Previous := MC_SHA256.Hash (CR);
   Expect (MC_Checkpoint.Follows (CP,Next_CP,MC_SHA256.Hash (CR)),"checkpoint-follows-parent");
   Next_CP.Replay_Sequence := 4;
   Expect (not MC_Checkpoint.Follows (CP,Next_CP,MC_SHA256.Hash (CR)),"checkpoint-does-not-reset-replay-window");
   Next_CP := CP; Next_CP.Generation := 2; Next_CP.Previous := MC_SHA256.Hash (CR); Next_CP.Trust_Epoch := 1;
   Expect (not MC_Checkpoint.Follows (CP,Next_CP,MC_SHA256.Hash (CR)),"checkpoint-does-not-roll-back-trust");
   CR (258) := 1; CR (289..320) := MC_SHA256.Hash (CR (1..288));
   MC_Checkpoint.Decode (CR,Parsed_CP,Status); Expect (Status /= OK,"checkpoint-unknown-fields-denied");
   Report;
end Run_Control_Tests;
