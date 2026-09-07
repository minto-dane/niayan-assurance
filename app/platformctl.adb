-- SPDX-License-Identifier: MIT
with Ada.Command_Line; use Ada.Command_Line;
with Ada.Text_IO; use Ada.Text_IO;
with MC_Types; use MC_Types;
with MC_File_IO; with MC_Properties; with MC_Text; with MC_Hex; with MC_Numbers;
with MC_Platform_Profile;
procedure Platformctl with SPARK_Mode => Off is
   D : MC_Properties.Document; V : MC_Text.Value; O : Outcome := OK;
   F : MC_Platform_Profile.Facts; G : MC_Platform_Profile.Grade := MC_Platform_Profile.Development;
   Fields : constant String :=
     "policy,accepted-baseline,secure-boot,measured-boot,signed-kernel-modules,kernel-lockdown," &
     "integrity-appraisal,selinux-enforcing,audit-remote-sink,immutable-audit-receipt,kdump-ready," &
     "kdump-remote-copy,pstore-ready,hardware-watchdog,edac-ras,storage-health,storage-scrub-current," &
     "time-integrity,power-telemetry,recovery-environment,tested-backup-restore,offsite-backup," &
     "out-of-band-management,quorum,fencing,independent-fault-domains,cluster-nodes,fault-domains";
   procedure Get_Text(Name:String; S:out String; Used:out Natural) is
   begin
      S := (others=>Character'Val(0)); Used:=0; if O/=OK then return; end if;
      MC_Properties.Get(D,Name,V,O); if O=OK then
         declare X : constant String := MC_Text.Image(V); begin
            if X'Length>S'Length then O:=Invalid_Input; else Used:=X'Length; S(1..Used):=X; end if;
         end;
      end if;
   end Get_Text;
   procedure Get_Bool(Name:String; B:out Boolean) is
      S : String(1..16); N:Natural;
   begin
      B:=False; Get_Text(Name,S,N); if O/=OK then return; end if;
      if S(1..N)="true" then B:=True; elsif S(1..N)="false" then B:=False; else O:=Invalid_Input; end if;
   end Get_Bool;
   procedure Get_Counter(Name:String; C:out Counter) is
      S:String(1..64); N:Natural;
   begin C:=0; Get_Text(Name,S,N); if O=OK then MC_Numbers.Parse(S(1..N),C,O); end if; end Get_Counter;
   procedure Get_Digest(Name:String; X:out Digest) is
      S:String(1..128); N:Natural;
   begin X:=(others=>0); Get_Text(Name,S,N); if O=OK then MC_Hex.Decode(S(1..N),X,O); end if; end Get_Digest;
   C : Counter := 0;
begin
   if Argument_Count/=3 or else Argument(1)/="check" then
      Put_Line(Standard_Error,"platformctl check FACTS {development|single|cluster}"); Set_Exit_Status(Failure); return;
   end if;
   if Argument(3)="development" then G:=MC_Platform_Profile.Development;
   elsif Argument(3)="single" then G:=MC_Platform_Profile.Qualified_Single_Node;
   elsif Argument(3)="cluster" then G:=MC_Platform_Profile.Qualified_Cluster;
   else Put_Line(Standard_Error,"invalid platform grade"); Set_Exit_Status(Failure); return; end if;
   MC_Properties.Parse(MC_File_IO.Read_File(Argument(2),65_536),D,O);
   if O=OK and then not MC_Properties.Has_Exactly(D,Fields) then O:=Invalid_Input; end if;
   Get_Digest("policy",F.Policy); Get_Digest("accepted-baseline",F.Accepted_Baseline);
   Get_Bool("secure-boot",F.Secure_Boot); Get_Bool("measured-boot",F.Measured_Boot);
   Get_Bool("signed-kernel-modules",F.Signed_Kernel_Modules); Get_Bool("kernel-lockdown",F.Kernel_Lockdown);
   Get_Bool("integrity-appraisal",F.Integrity_Appraisal); Get_Bool("selinux-enforcing",F.SELinux_Enforcing);
   Get_Bool("audit-remote-sink",F.Audit_Remote_Sink); Get_Bool("immutable-audit-receipt",F.Immutable_Audit_Receipt);
   Get_Bool("kdump-ready",F.Kdump_Ready); Get_Bool("kdump-remote-copy",F.Kdump_Remote_Copy);
   Get_Bool("pstore-ready",F.Pstore_Ready); Get_Bool("hardware-watchdog",F.Hardware_Watchdog);
   Get_Bool("edac-ras",F.EDAC_RAS); Get_Bool("storage-health",F.Storage_Health);
   Get_Bool("storage-scrub-current",F.Storage_Scrub_Current); Get_Bool("time-integrity",F.Time_Integrity);
   Get_Bool("power-telemetry",F.Power_Telemetry); Get_Bool("recovery-environment",F.Recovery_Environment);
   Get_Bool("tested-backup-restore",F.Tested_Backup_Restore); Get_Bool("offsite-backup",F.Offsite_Backup);
   Get_Bool("out-of-band-management",F.Out_Of_Band_Management); Get_Bool("quorum",F.Quorum);
   Get_Bool("fencing",F.Fencing); Get_Bool("independent-fault-domains",F.Independent_Fault_Domains);
   Get_Counter("cluster-nodes",C); if O=OK and then C<=65_535 then F.Cluster_Nodes:=Natural(C); else O:=Invalid_Input; end if;
   Get_Counter("fault-domains",C); if O=OK and then C<=65_535 then F.Fault_Domains:=Natural(C); else O:=Invalid_Input; end if;
   if O/=OK then Put_Line("platform-facts=" & Outcome'Image(O)); Set_Exit_Status(Failure);
   elsif MC_Platform_Profile.Ready(F,G) then Put_Line("platform-ready=true grade=" & MC_Platform_Profile.Grade'Image(G));
   else Put_Line("platform-ready=false grade=" & MC_Platform_Profile.Grade'Image(G)); Set_Exit_Status(Failure); end if;
exception when others => Put_Line(Standard_Error,"platform check failed"); Set_Exit_Status(Failure);
end Platformctl;
