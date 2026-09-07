-- SPDX-License-Identifier: MIT
-- Public synthetic qualification fixtures: never trust these keys in production.
with Ada.Command_Line; with Ada.Characters.Handling;
with MC_Types; use MC_Types; with MC_File_IO; with MC_Qualification; with MC_Qualification_Auth;
with MC_Contract_Profile; with MC_Release; with MC_SHA256;
with Test_Support; use Test_Support;
procedure Run_Qualification_Tests with SPARK_Mode => Off is
   package Q renames MC_Qualification; package A renames MC_Qualification_Auth;
   Dir : constant String := (if Ada.Command_Line.Argument_Count = 1 then
      Ada.Command_Line.Argument (1) else "fixtures/qualification-v1");
   P, Bad : Q.Policy; Raw, Broken : A.Raw_Claims; Signatures : A.Signatures;
   Claims : Q.Claims; Verified : Q.Signature_Results := (others => True);
   Verdict : Q.Assessment; Status : Outcome;
   function Read (Name : String; Limit : Positive) return Bytes is
     (MC_File_IO.Read_File (Dir & "/" & Name,Limit));
begin
   P.Source_Set := (others => 1); P.Binary_Set := (others => 2);
   P.Contract := MC_Contract_Profile.Fingerprint; P.Platform := (others => 3);
   P.Policy_ID := (others => 4); P.Trust_Epoch := 1; P.Max_Lifetime := 1000; P.Count := 3;
   for I in 1 .. 3 loop
      P.Keys (I).Principal := (others => Byte (I)); P.Keys (I).Domain := Counter (I);
      P.Keys (I).Duty := Q.Role'Val (I-1);
      P.Keys (I).Key := Read ((case I is when 1 => "builder.pub", when 2 => "reviewer.pub", when others => "operator.pub"),32);
   end loop;
   for I in MC_Release.Evidence_Item loop
      declare Name : constant String := Ada.Characters.Handling.To_Lower (MC_Release.Evidence_Item'Image (I)); begin
         Raw (I) := Read (Name & ".bin",320); Signatures (I) := Read (Name & ".sig",64);
      end;
      Q.Decode (Raw (I),Claims (I),Status); Expect (Status = OK,"qualification-frame-roundtrip");
   end loop;
   A.Verify (P,Raw,Signatures,100,Verdict,Status);
   Expect (Status = OK and then Verdict.Eligible,"all-current-signed-evidence");
   A.Verify (P,Raw,Signatures,1000,Verdict,Status);
   Expect (Status = Denied,"expired-release-evidence");
   Bad := P; Bad.Binary_Set := (others => 9);
   A.Verify (Bad,Raw,Signatures,100,Verdict,Status);
   Expect (Status = Denied,"other-binary-cannot-reuse-build-evidence");
   Bad := P; Bad.Keys (2).Domain := P.Keys (1).Domain;
   Verdict := Q.Evaluate (Bad,Claims,Verified,100);
   Expect (not Verdict.Eligible,"independent-review-domain-required");
   Broken := Raw; Broken (MC_Release.Compiler_Build) (280) := 1;
   Broken (MC_Release.Compiler_Build) (289..320) := MC_SHA256.Hash (Broken (MC_Release.Compiler_Build) (1..288));
   A.Verify (P,Broken,Signatures,100,Verdict,Status);
   Expect (Status = Denied,"rehashed-reserved-claim-refused");
   for I in MC_Release.Evidence_Item loop
      Verified (I) := False; Verdict := Q.Evaluate (P,Claims,Verified,100);
      Expect (not Verdict.Eligible,"no-required-evidence-may-be-skipped"); Verified (I) := True;
   end loop;
   Report;
end Run_Qualification_Tests;
