-- SPDX-License-Identifier: BSD-3-Clause
with Test_Support; use Test_Support; with MC_Types; use MC_Types;
with MC_Backups; use MC_Backups; with Recovery_Fixtures;
procedure Run_Backup_Contract_Tests with SPARK_Mode => Off is
   P : Policy; C, Saved : Catalog; Members : Selection; H : Digest; Status : Outcome; Pick : Natural;
begin
   Recovery_Fixtures.Make (P,C,Status); Expect (Status = OK,"backup-fixture"); Saved := C;
   Choose (P,C,4,Pick,Members,Status); Expect (Status = OK and then Pick = 4,"highest-recoverable-position");
   C (4).Locations (2).Domain_ID := 1;
   Restore_Set (P,C,4,4,Members,Status); Expect (Status /= OK,"same-domain-copies-insufficient"); C := Saved;
   C (4).Key_Available := False;
   Restore_Set (P,C,4,4,Members,Status); Expect (Status /= OK,"encrypted-but-key-unavailable"); C := Saved;
   C (4).Key_Revoked := True;
   Restore_Set (P,C,4,4,Members,Status); Expect (Status /= OK,"revoked-backup-refused"); C := Saved;
   P.Required_Position := 41; Choose (P,C,4,Pick,Members,Status);
   Expect (Status /= OK and then Pick = 0,"no-implicit-data-loss"); P.Required_Position := 10;
   C (4).Full := False; C (4).Parent := C (3).Manifest; C (4).From_Position := C (3).Through_Position;
   Chain (C,4,4,Members,H,Status); Expect (Status = OK and then Members (3) and then Members (4),"incremental-parent-closure");
   Restore_Set (P,C,4,4,Members,Status); Expect (Status /= OK,"old-restore-test-does-not-cover-new-chain");
   C (4).Restore_Test_Chain := H; Restore_Set (P,C,4,4,Members,Status);
   Expect (Status = OK,"tested-whole-chain"); C (4).From_Position := 31;
   Restore_Set (P,C,4,4,Members,Status); Expect (Status /= OK,"incremental-gap-denied");
   C := Saved; C (4).Full := False; C (4).Parent := C (4).Manifest; C (4).From_Position := C (4).Through_Position;
   Chain (C,4,4,Members,H,Status); Expect (Status /= OK,"backup-cycle-denied"); C := Saved;
   C (4).Tested_At := 1_001; Restore_Set (P,C,4,4,Members,Status);
   Expect (Status /= OK,"future-restore-receipt-denied"); C := Saved;
   P.Now_Lower := 999; P.Now_Upper := 2_000; Restore_Set (P,C,4,4,Members,Status);
   Expect (Status /= OK,"clock-uncertainty-cannot-extend-expiry");
   Report;
end Run_Backup_Contract_Tests;
