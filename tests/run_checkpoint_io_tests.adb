-- SPDX-License-Identifier: MIT
with Ada.Command_Line; with Test_Support; use Test_Support; with MC_Types; use MC_Types;
with MC_Checkpoint; with MC_Checkpoint_Store; with MC_Contract_Profile; with MC_SHA256;
with MC_Runtime;
procedure Run_Checkpoint_IO_Tests with SPARK_Mode => Off is
   Anchor : Digest := Zero_Digest;
   Lose_After_Anchor, Lose_Before_Anchor : Boolean := False;
   D, Next_D, Loaded : MC_Checkpoint.Descriptor; Status : Outcome; Used : Natural;
   Payload : Bytes (1..8) := (others => 1); Out_B : Bytes (1..8);
   Scope : constant Identity := (others => 1); Stream : constant Identity := (others => 2);
   procedure Authorize (Phase : String; Before, After : MC_Checkpoint.Descriptor; Status : out Outcome) is
   begin
      Status := Denied;
      if Phase in "checkpoint-stage" | "checkpoint-anchor" | "checkpoint-reconcile"
        and then MC_Checkpoint.Valid (After) and then After.Root_ID = Scope
        and then After.Stream_ID = Stream and then After.Generation > Before.Generation
      then Status := OK; end if;
   end Authorize;
   procedure Validate_State (D : MC_Checkpoint.Descriptor; Payload : Bytes; Status : out Outcome) is
   begin
      Status := (if D.Root_ID = Scope and then D.Stream_ID = Stream
        and then Payload'Length = 8 and then D.Payload = MC_SHA256.Hash (Payload)
        and then D.Quiescent then OK else Denied);
   end Validate_State;
   procedure Check_Anchor (D : MC_Checkpoint.Descriptor; Manifest : Digest; Status : out Outcome) is
   begin
      Status := (if D.Root_ID = Scope and then D.Stream_ID = Stream
        and then Manifest /= Zero_Digest and then Manifest = Anchor then OK else Stale);
   end Check_Anchor;
   procedure Advance_Anchor (Before : Digest; D : MC_Checkpoint.Descriptor; Manifest : Digest; Status : out Outcome) is
   begin
      Status := Conflict;
      if Before /= Anchor or else D.Root_ID /= Scope or else D.Stream_ID /= Stream then return; end if;
      if Lose_Before_Anchor then Status := Indeterminate; return; end if;
      Anchor := Manifest; Status := (if Lose_After_Anchor then Indeterminate else OK);
   end Advance_Anchor;
   package Store is new MC_Checkpoint_Store (Authorize,Validate_State,Check_Anchor,Advance_Anchor);
   -- Anchor is an in-process TEST DOUBLE, not production non-rollback storage.
   -- This test executes local file persistence and controlled response loss only.
begin
   Expect (Ada.Command_Line.Argument_Count = 1,"one-isolated-directory-required");
   MC_Runtime.Initialize (Status); Expect (Status = OK,"checkpoint-runtime-init");
   D.Root_ID := Scope; D.Stream_ID := Stream; D.Contract := MC_Contract_Profile.Fingerprint;
   D.Generation := 1; D.Trust_Epoch := 1; D.Payload_Size := 8; D.Payload := MC_SHA256.Hash (Payload);
   D.Audit_Receipt := (others => 3); D.Quiescent := True;
   Store.Publish (Ada.Command_Line.Argument (1),Zero_Digest,D,Payload,Status);
   Expect (Status = OK,"initial-checkpoint-published");
   Store.Load (Ada.Command_Line.Argument (1),Scope,Stream,Loaded,Out_B,Used,Status);
   Expect (Status = OK and then Used = 8 and then Out_B = Payload,"checkpoint-loaded-and-validated");
   Next_D := D; Next_D.Generation := 2; Next_D.Previous := Anchor;
   Payload := (others => 2); Next_D.Payload := MC_SHA256.Hash (Payload); Lose_After_Anchor := True;
   Store.Publish (Ada.Command_Line.Argument (1),Anchor,Next_D,Payload,Status);
   Expect (Status = Indeterminate,"lost-anchor-response-not-success");
   Store.Load (Ada.Command_Line.Argument (1),Scope,Stream,Loaded,Out_B,Used,Status);
   Expect (Status /= OK,"old-local-pointer-not-silently-used");
   Store.Reconcile (Ada.Command_Line.Argument (1),Scope,Stream,Status);
   Expect (Status = OK,"anchored-candidate-reconciled");
   Store.Load (Ada.Command_Line.Argument (1),Scope,Stream,Loaded,Out_B,Used,Status);
   Expect (Status = OK and then Loaded.Generation = 2 and then Out_B = Payload,"new-checkpoint-visible");
   D := Next_D; Next_D.Generation := 3; Next_D.Previous := Anchor;
   Payload := (others => 3); Next_D.Payload := MC_SHA256.Hash (Payload);
   Lose_After_Anchor := False; Lose_Before_Anchor := True;
   Store.Publish (Ada.Command_Line.Argument (1),Anchor,Next_D,Payload,Status);
   Expect (Status = Indeterminate,"lost-before-anchor");
   Store.Reconcile (Ada.Command_Line.Argument (1),Scope,Stream,Status);
   Expect (Status /= OK,"unanchored-pending-not-published");
   Store.Load (Ada.Command_Line.Argument (1),Scope,Stream,Loaded,Out_B,Used,Status);
   Expect (Status = OK and then Loaded.Generation = 2,"accepted-anchor-still-loadable");
   Report;
end Run_Checkpoint_IO_Tests;
