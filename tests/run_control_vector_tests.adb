-- SPDX-License-Identifier: MIT
with Ada.Command_Line; with Test_Support; use Test_Support;
with MC_Types; use MC_Types; with MC_Control; with MC_Control_Codec;
with MC_Authentic; with MC_File_IO; with MC_Runtime; with MC_SHA256;
procedure Run_Control_Vector_Tests with SPARK_Mode => Off is
   use type MC_Control.Mode;
   A : MC_Control.Authority; S, Next_S : MC_Control.State; P : MC_Control.Proposal;
   Status : Outcome; Votes : MC_Control.Verified_Set := (others => False);
   function Read (Name : String; Limit : Positive) return Bytes is
     (MC_File_IO.Read_File (Ada.Command_Line.Argument (1) & "/" & Name,Limit));
begin
   Expect (Ada.Command_Line.Argument_Count = 1,"public-vector-directory-required");
   MC_Runtime.Initialize (Status); Expect (Status = OK,"vector-crypto-init");
   declare
      AF : constant Bytes := Read ("authority.bin",1_024);
      BF : constant Bytes := Read ("before.bin",256);
      PF : constant Bytes := Read ("proposal.bin",320);
      Signatures : constant Bytes := Read ("signatures.bin",512);
   begin
      MC_Control_Codec.Decode (AF,A,Status); Expect (Status = OK,"independent-authority-decode");
      MC_Control_Codec.Decode (BF,S,Status); Expect (Status = OK,"independent-state-decode");
      MC_Control_Codec.Decode (PF,P,Status); Expect (Status = OK,"independent-proposal-decode");
      Expect (MC_Control_Codec.Encode (P) = PF,"independent-canonical-roundtrip");
      for I in 1..2 loop
         MC_Authentic.Verify ("MC-CONTROL-v1",PF,Signatures (1+(I-1)*64..I*64),A.Keys (I).Public_Key,Status);
         Expect (Status = OK,"independent-role-signature"); Votes (I) := Status = OK;
      end loop;
      MC_Control.Decide (A,MC_SHA256.Hash (AF),S,MC_SHA256.Hash (BF),False,
         P,Votes,P.Boot_ID,1_000,Next_S,Status);
      Expect (Status = OK and then Next_S.Current = MC_Control.Running,"independent-two-role-plan");
      MC_Authentic.Verify ("MC-CONTROL-v1",PF,Read ("wrong-domain.sig",64),A.Keys (1).Public_Key,Status);
      Expect (Status /= OK,"independent-wrong-domain-denied");
      MC_Control_Codec.Decode (Read ("reserved.bin",320),P,Status);
      Expect (Status /= OK,"independent-rehashed-reserved-denied");
      MC_Control_Codec.Decode (Read ("truncated.bin",320),P,Status);
      Expect (Status /= OK,"independent-truncated-denied");
   end;
   Report;
end Run_Control_Vector_Tests;
