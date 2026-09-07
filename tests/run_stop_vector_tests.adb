-- SPDX-License-Identifier: MIT
with Ada.Command_Line; with MC_Types; use MC_Types;
with MC_File_IO; with MC_Stop_Barrier; use MC_Stop_Barrier;
with MC_Stop_Barrier_Auth; with MC_Numbers; with MC_Signatures;
with MC_Contract_Profile; with Test_Support; use Test_Support;
procedure Run_Stop_Vector_Tests with SPARK_Mode => Off is
   Dir : constant String := (if Ada.Command_Line.Argument_Count = 1 then Ada.Command_Line.Argument (1) else "fixtures/stop-v1");
   P : Policy; S, Saved, Parsed : State; E : Evidence; Status : Outcome;
   function Read (Name : String; Limit : Positive) return Bytes is
     (MC_File_IO.Read_File (Dir & "/" & Name,Limit));
   procedure Verify (Name, Signature_Name : String) is
      Raw : constant Bytes := Read (Name,320);
      Sig : constant Bytes := Read (Signature_Name,64);
   begin
      if Sig'Length /= MC_Signatures.Signature'Length then Status := Invalid_Input; return; end if;
      MC_Stop_Barrier_Auth.Verify (P,Raw,Sig,E,Status);
   end Verify;
begin
   Decode (Read ("policy.bin",4_608),P,Status);
   Expect (Status = OK and then P.Contract = MC_Contract_Profile.Fingerprint,"fixture-current-profile");
   Initialize (P,S,Status); Expect (Status = OK,"fixture-initialize");
   for I in 1..3 loop
      Verify ("node-" & MC_Numbers.Image (Counter (I)) & ".bin", "node-" & MC_Numbers.Image (Counter (I)) & ".sig");
      Expect (Status = OK,"fixture-signature-against-roster-key");
      Observe (P,S,E,Status = OK,200,Status);
      Expect (Status = OK,"same-resource-distinct-node-not-overwritten");
   end loop;
   Seal (P,S,200,Status); Expect (Status = OK,"fixture-all-consumers-sealed");
   Expect (Encode (S) = Read ("sealed-state.bin",4_608),"independent-binary-state-golden-match");
   Decode (Read ("sealed-state.bin",4_608),Parsed,Status);
   Expect (Status = OK and then Parsed = S,"fixture-decode-roundtrip");
   Expect (Usable (P,S,200) and then not Usable (P,S,1_000),"fixture-not-authorization-without-freshness");
   Verify ("node-1.bin","wrong-domain.sig"); Expect (Status /= OK,"fixture-cross-domain-refused");
   Verify ("node-1.bin","wrong-role.sig"); Expect (Status /= OK,"fixture-fence-key-cannot-self-drain");
   Verify ("fence-1.bin","fence-1.sig"); Expect (Status = OK,"fixture-independent-fence-key");
   Verify ("evidence-reserved.bin","evidence-reserved.bin.sig"); Expect (Status /= OK,"signed-rehashed-reserved-refused");
   Verify ("evidence-boolean.bin","evidence-boolean.bin.sig"); Expect (Status /= OK,"signed-rehashed-boolean-refused");
   Verify ("truncated-evidence.bin","node-1.sig"); Expect (Status /= OK,"fixture-truncation-refused");
   Saved := S;
   Verify ("old-guard-evidence.bin","old-guard-evidence.sig"); Expect (Status = OK,"old-guard-is-authentic-not-authorized");
   Observe (P,S,E,True,201,Status);
   Expect (Status = Denied and then S = Saved,"old-guard-authentic-frame-does-not-change-state");
   Report;
end Run_Stop_Vector_Tests;
