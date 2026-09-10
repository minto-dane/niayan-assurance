-- SPDX-License-Identifier: BSD-3-Clause
with Ada.Command_Line; with Test_Support; use Test_Support;
with MC_Types; use MC_Types; with MC_Control; with MC_Control_Codec; with MC_Control_IO;
with MC_FS; with MC_Atomic; with MC_Runtime; with MC_Keys; with MC_Signatures;
with MC_Clock; with MC_Contract_Profile; with MC_SHA256; with MC_Codec;
procedure Run_Control_IO_Tests with SPARK_Mode => Off is
   use type MC_Control.Mode; use type Byte;
   R : MC_FS.Root; A : MC_Control.Authority; P : MC_Control.Proposal; S : MC_Control.State;
   Bundle : MC_Control_IO.Signature_Bundle := (others => 0); Status : Outcome;
   H, AH : Digest; Boot : Identity; Now : Counter; PK : MC_Signatures.Public_Key;
   Sig : MC_Signatures.Signature; Domain : constant String := "MC-CONTROL-v1";
   procedure Sign (Slot : MC_Control.Signer_Index; Key_Directory : String) is
      B : MC_Control_Codec.Proposal_Frame := MC_Control_Codec.Encode (P);
      Message : Bytes (1..2+Domain'Length+B'Length);
   begin
      MC_Codec.Put16 (Message,1,Domain'Length);
      for I in Domain'Range loop Message (2+I) := Byte (Character'Pos (Domain (I))); end loop;
      Message (3+Domain'Length..Message'Last) := B;
      MC_Keys.Sign (Key_Directory,Message,PK,Sig,Status);
      Expect (Status = OK and then PK = A.Keys (Slot).Public_Key,"test-signature");
      Bundle (1+(Slot-1)*64..Slot*64) := Sig;
   end Sign;
   procedure Read_Current is
   begin
      MC_Control_IO.Read_State (R,A.Scope,S,H,Status); Expect (Status = OK,"read-current-control-state");
   end Read_Current;
begin
   Expect (Ada.Command_Line.Argument_Count = 3,"three-isolated-directories-required");
   MC_Runtime.Initialize (Status); Expect (Status = OK,"runtime-init");
   MC_Keys.Generate (Ada.Command_Line.Argument (2),A.Keys (1).Public_Key,Status); Expect (Status = OK,"ephemeral-ops-key");
   MC_Keys.Generate (Ada.Command_Line.Argument (3),A.Keys (2).Public_Key,Status); Expect (Status = OK,"ephemeral-security-key");
   A.Scope := (others => 1); A.Contract := MC_Contract_Profile.Fingerprint; A.Serial := 1; A.Count := 2;
   A.Keys (1).Principal := (others => 2); A.Keys (1).Domain := 1; A.Keys (1).Duty := MC_Control.Operations;
   A.Keys (2).Principal := (others => 3); A.Keys (2).Domain := 2; A.Keys (2).Duty := MC_Control.Security;
   MC_FS.Open_Root (Ada.Command_Line.Argument (1),R,Status,Private_Only => True); Expect (Status = OK,"open-private-policy");
   MC_Atomic.Write (R,"control-authorities.bin",MC_Control_Codec.Encode (A),True,Status);
   Expect (Status = OK,"provision-test-authorities"); AH := MC_SHA256.Hash (MC_Control_Codec.Encode (A));
   MC_Control_IO.Check (R,A.Scope,MC_Control.Activate_Service,Status); Expect (Status /= OK,"missing-control-does-not-fall-back");
   MC_Clock.Read_Boot_ID (Boot,Status); Expect (Status = OK,"receiver-boot");
   MC_Clock.Boottime_Milliseconds (Now,Status); Expect (Status = OK,"receiver-clock");
   P.Scope := A.Scope; P.Contract := A.Contract; P.Authority_Digest := AH; P.Boot_ID := Boot;
   P.Request_ID := (others => 4); P.Reason := (others => 5); P.New_Trust_Epoch := 1;
   P.Not_Before := Now; P.Expires := Now+60_000; P.Desired := MC_Control.Quarantined;
   Sign (1,Ada.Command_Line.Argument (2));
   MC_Control_IO.Submit (Ada.Command_Line.Argument (1),A.Scope,MC_Control_Codec.Encode (P),Bundle,Status);
   Expect (Status = OK,"signed-quarantine-published"); Read_Current;
   Expect (S.Current = MC_Control.Quarantined and then S.Revision = 1,"quarantined-persistence");
   MC_Control_IO.Check (R,A.Scope,MC_Control.Inspect,Status); Expect (Status = OK,"inspection-still-possible");
   MC_Control_IO.Check (R,A.Scope,MC_Control.Activate_Service,Status); Expect (Status = Denied,"activation-interlocked");
   P.Desired := MC_Control.Running; P.Expected_Revision := S.Revision; P.Expected_State := H;
   P.New_Trust_Epoch := 2; P.Request_ID := (others => 6); P.Recovery_Receipt := (others => 7);
   Bundle := (others => 0); Sign (1,Ada.Command_Line.Argument (2));
   MC_Control_IO.Submit (Ada.Command_Line.Argument (1),A.Scope,MC_Control_Codec.Encode (P),Bundle,Status);
   Expect (Status = Denied,"single-signature-cannot-resume");
   Sign (2,Ada.Command_Line.Argument (3));
   MC_Control_IO.Submit (Ada.Command_Line.Argument (1),A.Scope,MC_Control_Codec.Encode (P),Bundle,Status);
   Expect (Status = OK,"two-role-resume-persisted"); Read_Current;
   Expect (S.Current = MC_Control.Running and then S.Revision = 2,"running-after-independent-approval");
   MC_Control_IO.Submit (Ada.Command_Line.Argument (1),A.Scope,MC_Control_Codec.Encode (P),Bundle,Status);
   Expect (Status = OK,"exact-acknowledged-retry-no-new-revision"); Read_Current;
   Expect (S.Revision = 2,"retry-did-not-increment");
   Bundle (1) := Bundle (1) xor 1;
   MC_Control_IO.Submit (Ada.Command_Line.Argument (1),A.Scope,MC_Control_Codec.Encode (P),Bundle,Status);
   Expect (Status /= OK,"altered-signature-rejected");
   A.Serial := 2; MC_Atomic.Write (R,"control-authorities.bin",MC_Control_Codec.Encode (A),False,Status);
   Expect (Status = OK,"test-authority-replacement");
   MC_Control_IO.Check (R,A.Scope,MC_Control.Change_Files,Status);
   Expect (Status /= OK,"authority-change-not-an-implicit-rotation");
   MC_FS.Close (R); Report;
exception when others => MC_FS.Close (R); raise;
end Run_Control_IO_Tests;
