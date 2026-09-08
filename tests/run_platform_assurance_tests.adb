-- SPDX-License-Identifier: MIT
with Test_Support; use Test_Support;
with MC_Types; use MC_Types;
with MC_Faults; with MC_Incidents; with MC_Attestation; with MC_Platform_Profile; with MC_Maintenance;
with MC_Commissioning; with MC_Breakglass; with MC_Diagnostic_Bundle;
with MC_System_Baseline; with MC_Generation; with MC_Accounting;
procedure Run_Platform_Assurance_Tests with SPARK_Mode => Off is
   use type mc_attestation.Trust;
   use type mc_faults.Disposition;
   use type mc_generation.Phase;
   use type mc_incidents.Phase;
   use type mc_system_baseline.Assessment;
   F : MC_Faults.Fault;
   I : MC_Incidents.State; X : MC_Incidents.Evidence; S : Outcome;
   AP : MC_Attestation.Policy; AE : MC_Attestation.Evidence;
   PF : MC_Platform_Profile.Facts;
   H : MC_Maintenance.Hold; W : MC_Maintenance.Window;
   CS : MC_Commissioning.State; CE : MC_Commissioning.Evidence;
   BR : MC_Breakglass.Request; DB : MC_Diagnostic_Bundle.Bundle;
   BL : MC_System_Baseline.Baseline; BF : MC_System_Baseline.Running_Facts;
   GS : MC_Generation.State; GE : MC_Generation.Evidence; AC : MC_Accounting.Event;
begin
   F.Cluster_ID := (others=>1); F.Node_ID := (others=>2); F.Resource_ID := (others=>3); F.Boot_ID := (others=>4);
   F.Policy := (others=>5); F.Syndrome := (others=>6); F.Sequence := 1; F.Observed_At := 100; F.Expires_At := 200;
   F.Occurrences := 1; F.Kind := MC_Faults.Memory; F.Level := MC_Faults.Uncorrectable;
   F.Nature := MC_Faults.Persistent; F.Quality := MC_Faults.Corroborated; F.Execution_At_Risk := True;
   Expect(MC_Faults.Valid(F),"fault-valid");
   Expect(MC_Faults.Isolation_Required(F),"uncorrectable-fault-isolates");
   Expect(MC_Faults.Automatic_Disposition(F)=MC_Faults.Drain_Node,"hardware-fault-drains-before-repair");
   F.Quality:=MC_Faults.Untrusted; F.Level:=MC_Faults.Informational; F.Execution_At_Risk:=False;
   Expect(MC_Faults.Automatic_Disposition(F)=MC_Faults.Escalate_Operator,"untrusted-source-does-not-autoheal");

   I.Incident_ID:=(others=>7); I.Cluster_ID:=(others=>1); I.Resource_ID:=(others=>3); I.Policy:=(others=>5);
   I.Revision:=1; I.First_Observed:=100; I.Last_Observed:=100; I.Current:=MC_Incidents.Open;
   F.Quality:=MC_Faults.Corroborated; F.Level:=MC_Faults.Uncorrectable; F.Execution_At_Risk:=True;
   X.Expected_Revision:=1; X.Now:=101; X.Authenticated:=True; X.Fault:=F; X.Correlation:=(others=>8);
   MC_Incidents.Step(I,MC_Incidents.Observe_Fault,X,S);
   Expect(S=OK and then I.Current=MC_Incidents.Containment_Required,"incident-requires-containment");
   X.Expected_Revision:=I.Revision; X.Now:=102; X.Containment:=(others=>9); X.Ownership_Safe:=True;
   MC_Incidents.Step(I,MC_Incidents.Confirm_Containment,X,S); Expect(S=OK and then I.Current=MC_Incidents.Contained,"containment-recorded");
   X.Expected_Revision:=I.Revision; X.Now:=103; X.Repair:=(others=>10);
   MC_Incidents.Step(I,MC_Incidents.Begin_Repair,X,S); Expect(S=OK and then I.Current=MC_Incidents.Repairing,"repair-started");
   X.Expected_Revision:=I.Revision; X.Now:=104;
   MC_Incidents.Step(I,MC_Incidents.Record_Repair,X,S); Expect(S=OK and then I.Current=MC_Incidents.Verifying,"repair-needs-verification");
   for N in 1..3 loop
      X.Expected_Revision:=I.Revision; X.Now:=104+Counter(N); X.Data_Consistent:=True; X.Dependencies_Healthy:=True;
      X.Ownership_Safe:=True; X.No_Open_Severe_Faults:=True; X.Stable_For_Ms:=Counter(N)*10_000; X.Required_Stable_Ms:=30_000;
      MC_Incidents.Step(I,MC_Incidents.Observe_Healthy,X,S); Expect(S=OK,"healthy-sample");
   end loop;
   X.Expected_Revision:=I.Revision; X.Now:=110; X.Stable_For_Ms:=30_000;
   MC_Incidents.Step(I,MC_Incidents.Close_Incident,X,S); Expect(S=OK and then I.Current=MC_Incidents.Closed,"incident-closes-only-after-stable-evidence");

   AP.Cluster_ID:=(others=>1); AP.Node_ID:=(others=>2); AP.Policy_Digest:=(others=>11);
   AP.Allowed_Boot_Profile:=(others=>12); AP.Allowed_Runtime_Profile:=(others=>13); AP.Minimum_Trust_Epoch:=5;
   AE.Cluster_ID:=AP.Cluster_ID; AE.Node_ID:=AP.Node_ID; AE.Boot_ID:=(others=>14); AE.Policy_Digest:=AP.Policy_Digest;
   AE.Boot_Profile:=AP.Allowed_Boot_Profile; AE.Runtime_Profile:=AP.Allowed_Runtime_Profile; AE.Quote_Digest:=(others=>15);
   AE.Trust_Epoch:=5; AE.Sequence:=1; AE.Observed_At:=100; AE.Expires_At:=10_000;
   AE.Quote_Verified:=True; AE.Nonce_Bound:=True; AE.Event_Log_Consistent:=True; AE.Secure_Boot:=True; AE.Measured_Boot:=True;
   AE.IMA_Appraisal:=True; AE.Module_Signing:=True; AE.Lockdown:=True;
   Expect(MC_Attestation.Evaluate(AP,AE,200)=MC_Attestation.Trusted,"fully-attested-node-trusted");
   AE.IMA_Appraisal:=False; Expect(MC_Attestation.Evaluate(AP,AE,200)=MC_Attestation.Restricted,"missing-runtime-integrity-restricts");

   PF.Policy:=(others=>1); PF.Accepted_Baseline:=(others=>2); PF.Secure_Boot:=True; PF.Measured_Boot:=True;
   PF.Signed_Kernel_Modules:=True; PF.Kernel_Lockdown:=True; PF.Integrity_Appraisal:=True; PF.SELinux_Enforcing:=True;
   PF.Audit_Remote_Sink:=True; PF.Immutable_Audit_Receipt:=True; PF.Kdump_Ready:=True; PF.Kdump_Remote_Copy:=True;
   PF.Pstore_Ready:=True; PF.Hardware_Watchdog:=True; PF.EDAC_RAS:=True; PF.Storage_Health:=True; PF.Storage_Scrub_Current:=True;
   PF.Time_Integrity:=True; PF.Power_Telemetry:=True; PF.Recovery_Environment:=True; PF.Tested_Backup_Restore:=True;
   PF.Offsite_Backup:=True; PF.Out_Of_Band_Management:=True;
   Expect(MC_Platform_Profile.Ready(PF,MC_Platform_Profile.Qualified_Single_Node),"single-node-platform-gate");
   PF.Quorum:=True; PF.Fencing:=True; PF.Independent_Fault_Domains:=True; PF.Cluster_Nodes:=3; PF.Fault_Domains:=3;
   Expect(MC_Platform_Profile.Ready(PF,MC_Platform_Profile.Qualified_Cluster),"cluster-platform-gate");

   H.Scope:=(others=>1); H.Hold_ID:=(others=>2); H.Policy:=(others=>3); H.Subject:=(others=>4); H.Reason:=(others=>5);
   H.Serial:=1; H.Published_At:=100; H.Kind:=MC_Maintenance.Security_Hold;
   Expect(MC_Maintenance.Blocks(H,H.Subject,True,False,False),"security-hold-blocks-apply");
   W.Scope:=H.Scope; W.Window_ID:=(others=>6); W.Policy:=H.Policy; W.Change_Set:=(others=>7); W.Not_Before:=100; W.Expires_At:=200;
   W.Maximum_Impact:=MC_Maintenance.Node_Reboot;
   Expect(MC_Maintenance.Permits(W,150,MC_Maintenance.Service_Restart),"window-allows-bounded-impact");
   W.Emergency:=True; Expect(not MC_Maintenance.Valid(W),"emergency-needs-dual-approval");
   W.Operations_Approved:=True; W.Security_Approved:=True; Expect(MC_Maintenance.Valid(W),"dual-approved-emergency-window");

   CE.Expected_Revision:=0; CE.Node_ID:=(others=>1); CE.Boot_ID:=(others=>2); CE.Hardware:=(others=>3); CE.Policy:=(others=>4);
   MC_Commissioning.Step(CS,MC_Commissioning.Record_Hardware,CE,S); Expect(S=OK,"commission-hardware-bound");
   CE.Expected_Revision:=CS.Revision; CE.Firmware:=(others=>5); CE.Firmware_Authenticated:=True; CE.Secure_Boot:=True;
   MC_Commissioning.Step(CS,MC_Commissioning.Record_Firmware,CE,S); Expect(S=OK,"commission-secure-firmware");
   CE.Expected_Revision:=CS.Revision; CE.Trust_Root:=(others=>6); CE.TPM_Owned:=True; CE.New_Trust_Epoch:=1;
   MC_Commissioning.Step(CS,MC_Commissioning.Enroll_Trust,CE,S); Expect(S=OK,"commission-trust-enrolled");

   BR.Request_ID:=(others=>1); BR.Scope:=(others=>2); BR.Reason:=(others=>3); BR.Evidence:=(others=>4); BR.Trust_Epoch:=5;
   BR.Not_Before:=100; BR.Expires_At:=200; BR.Operations_Approved:=True; BR.Security_Approved:=True; BR.Independent_Approvers:=True; BR.Audit_Sink_Reachable:=True;
   BR.Requested:=MC_Breakglass.Isolate_Node; Expect(MC_Breakglass.Permitted(BR,150,5),"breakglass-containment-dual-approved");
   BR.Requested:=MC_Breakglass.Disable_Audit; Expect(not MC_Breakglass.Permitted(BR,150,5),"breakglass-cannot-disable-audit");

   DB.Incident_ID:=(others=>1); DB.Node_ID:=(others=>2); DB.Boot_ID:=(others=>3); DB.Manifest:=(others=>4); DB.Policy:=(others=>5);
   DB.Captured_At:=100; DB.Expires_At:=1_000; DB.Authenticated:=True; DB.Redaction_Policy_Applied:=True; DB.Encrypted_At_Rest:=True; DB.Preserved_Remotely:=True; DB.Immutable_Receipt:=True;
   DB.Classes(MC_Diagnostic_Bundle.Audit):=True; DB.Classes(MC_Diagnostic_Bundle.Kernel_Log):=True; DB.Classes(MC_Diagnostic_Bundle.Pstore):=True;
   DB.Classes(MC_Diagnostic_Bundle.Hardware_RAS):=True; DB.Classes(MC_Diagnostic_Bundle.Attestation):=True;
   Expect(MC_Diagnostic_Bundle.Sufficient_For_Kernel_Incident(DB,200),"kernel-incident-evidence-preserved");

   BL.ID:=(others=>1); BL.Distribution:=(others=>2); BL.Repository_Snapshot:=(others=>3); BL.Package_Incorporation:=(others=>4);
   BL.Kernel:=(others=>5); BL.Initramfs:=(others=>6); BL.Boot_Chain:=(others=>7); BL.Systemd_Profile:=(others=>8); BL.SELinux_Policy:=(others=>9); BL.Integrity_Policy:=(others=>10); BL.Configuration_Policy:=(others=>11);
   BL.Recovery_Image:=(others=>12); BL.Backup_Policy:=(others=>13); BL.Cluster_Policy:=(others=>14); BL.Trust_Roots:=(others=>15); BL.Repository_Epoch:=2; BL.Trust_Epoch:=3; BL.Security_Epoch:=4; BL.Signed:=True; BL.Independently_Approved:=True; BL.Recovery_Verified:=True;
   BF.Installed_Baseline:=BL.ID; BF.Running_Kernel:=BL.Kernel; BF.Boot_Chain:=BL.Boot_Chain; BF.Systemd_Profile:=BL.Systemd_Profile; BF.SELinux_Policy:=BL.SELinux_Policy; BF.Integrity_Policy:=BL.Integrity_Policy; BF.Configuration_Policy:=BL.Configuration_Policy; BF.Repository_Epoch:=2; BF.Trust_Epoch:=3; BF.Security_Epoch:=4; BF.Attestation_Trusted:=True; BF.Package_Set_Exact:=True; BF.Recovery_Pinned:=True;
   Expect(MC_System_Baseline.Assess(BL,BF)=MC_System_Baseline.Conformant,"system-baseline-binds-boot-package-policy-and-recovery");

   GS.Generation_ID:=(others=>1); GS.Previous_ID:=(others=>2); GS.Baseline:=BL.ID; GS.Recovery:=BL.Recovery_Image; GS.Sequence:=1; GS.Entered_At:=100;
   GE.Baseline:=GS.Baseline; GE.Recovery:=GS.Recovery; GE.Recovery_Pinned:=True; GE.Stage_Verified:=True; GE.Incidents_Clear:=True; GE.Expected_Revision:=0; GE.Now:=101;
   MC_Generation.Step(GS,MC_Generation.Record_Staged,GE,S); Expect(S=OK,"system-generation-staged");
   GE.Expected_Revision:=GS.Revision; GE.Now:=102; MC_Generation.Step(GS,MC_Generation.Begin_Canary,GE,S); Expect(S=OK,"system-generation-canary");
   for N in 1..3 loop GE.Expected_Revision:=GS.Revision; GE.Now:=102+Counter(N)*10; GE.Canary_Healthy:=True; GE.Cluster_Healthy:=True; GE.Minimum_Soak_Ms:=20; MC_Generation.Step(GS,MC_Generation.Observe_Healthy,GE,S); Expect(S=OK,"generation-soak-sample"); end loop;
   Expect(GS.Current=MC_Generation.Verified,"generation-needs-soak-before-accept");

   AC.Event_ID:=(others=>1); AC.Scope:=(others=>2); AC.Object_ID:=(others=>3); AC.Actor:=(others=>4); AC.Correlation_ID:=(others=>5); AC.Payload:=(others=>6); AC.Policy:=(others=>7); AC.Sequence:=1; AC.Observed_At:=100; AC.Trust_Epoch:=1; AC.Authenticated:=True; AC.Kind:=MC_Accounting.Node_Fenced; AC.Level:=MC_Accounting.Critical;
   Expect(MC_Accounting.Valid(AC) and then MC_Accounting.Required_Remote_Preservation(AC),"critical-accounting-event-needs-remote-preservation");
   Report;
end Run_Platform_Assurance_Tests;
