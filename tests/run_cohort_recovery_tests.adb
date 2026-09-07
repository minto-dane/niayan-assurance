-- SPDX-License-Identifier: MIT
with MC_Types; use MC_Types;
with MC_Recovery_Cohort; use MC_Recovery_Cohort;
procedure Run_Cohort_Recovery_Tests is
   A : Anchor := (Node | Recovery_ID => (others => 1), Manifest | Catalog |
      Journal_Head | Pending_Set | Cohort => (others => 1),
      Generation => 7, Trust_Epoch => 2, Last_Sequence => 20, Expires => 200);
   E : Evidence := (Core_Suspect => False, Pending_External_Effects => 3,
      Current_Trust => 2, Minimum_Generation => 7, Now => 100, others => True);
   S : State; R : Outcome;
   W : Witnesses (1 .. 2) := (others => (Principal | Domain_ID => (others => 1),
      Anchor_Hash => (others => 1), others => True));
begin
   pragma Assert (not Quorum (W, A.Manifest, 2));
   W (2).Principal := (others => 2); W (2).Domain_ID := (others => 2); W (2).Recovery_Role := False;
   pragma Assert (Quorum (W, A.Manifest, 2));
   E.Exact_Anchor := False; Prepare (S, A, E, R); pragma Assert (R = Denied);
   E.Exact_Anchor := True; Prepare (S, A, E, R); pragma Assert (R = OK);
   E.Replay_Set_Preserved := False; Check_Candidate (S, E, R); pragma Assert (R = Denied);
   E.Replay_Set_Preserved := True; Check_Candidate (S, E, R); pragma Assert (R = OK);
   E.Now := 200; Publish (S, E, R); pragma Assert (R = Denied);
   E.Now := 101; Publish (S, E, R); pragma Assert (R = OK and S.Status = Reconciliation_Only);
   Accept_Operational (S, E, False, True, True, R); pragma Assert (R = Denied);
   Accept_Operational (S, E, True, True, True, R); pragma Assert (R = OK and S.Status = Operational);
   A.Generation := 6; pragma Assert (not Usable (A, E));
end Run_Cohort_Recovery_Tests;
