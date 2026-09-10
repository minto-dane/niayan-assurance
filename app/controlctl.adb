-- SPDX-License-Identifier: BSD-3-Clause
with Ada.Command_Line; use Ada.Command_Line;
with Ada.Text_IO; use Ada.Text_IO;
with MC_Types; use MC_Types; with MC_Control; with MC_Control_Codec; with MC_Control_IO;
with MC_Runtime; with MC_FS; with MC_Atomic; with MC_Properties; with MC_Text;
with MC_File_IO; with MC_Clock; with MC_Contract_Profile; with MC_SHA256;
with MC_Hex; with MC_Numbers; with MC_Keys; with MC_Signatures; with MC_Authentic; with MC_Codec;
procedure Controlctl with SPARK_Mode => Off is
   use type MC_FS.Entry_Kind;
   R, Out_R : MC_FS.Root; Status : Outcome; Doc : MC_Properties.Document; V : MC_Text.Value;
   A : MC_Control.Authority; P : MC_Control.Proposal; S : MC_Control.State;
   Scope, Boot : Identity; H : Digest; Now, TTL, N : Counter := 0; Used : Natural;
   AF : MC_Control_Codec.Authority_Frame; PF : MC_Control_Codec.Proposal_Frame;
   Bundle : MC_Control_IO.Signature_Bundle := (others => 0);
   PK : MC_Signatures.Public_Key; Sig : MC_Signatures.Signature; Info : MC_FS.Entry_Info;
   Domain : constant String := "MC-CONTROL-v1";
   procedure Hex_Field (Name : String; Value : out Bytes) is
   begin
      Value := (others => 0); if Status /= OK then return; end if;
      MC_Properties.Get (Doc,Name,V,Status);
      if Status = OK then MC_Hex.Decode (MC_Text.Image (V),Value,Status); end if;
   end Hex_Field;
   procedure Num_Field (Name : String; Value : out Counter) is
   begin
      Value := 0; if Status /= OK then return; end if;
      MC_Properties.Get (Doc,Name,V,Status);
      if Status = OK then MC_Numbers.Parse (MC_Text.Image (V),Value,Status); end if;
   end Num_Field;
   procedure Load_Spec (Name, Fields : String) is
   begin
      MC_Properties.Parse (MC_File_IO.Read_File (Name,32_768),Doc,Status);
      if Status = OK and then not MC_Properties.Has_Exactly (Doc,Fields) then Status := Invalid_Input; end if;
   end Load_Spec;
   procedure Load_Authority (Directory : String) is
   begin
      MC_FS.Open_Root (Directory,R,Status,Private_Only => True); if Status /= OK then return; end if;
      MC_Atomic.Read (R,"control-authorities.bin",AF,Used,Status);
      if Status = OK and then Used /= AF'Length then Status := Corrupt; end if;
      if Status = OK then MC_Control_Codec.Decode (AF,A,Status); end if;
      if Status = OK and then A.Contract /= MC_Contract_Profile.Fingerprint then Status := Unsupported; end if;
   end Load_Authority;
   procedure Load_Proposal (Name : String) is
      B : constant Bytes := MC_File_IO.Read_File (Name,320);
   begin
      MC_Control_Codec.Decode (B,P,Status); if Status = OK then PF := B; end if;
   end Load_Proposal;
   procedure Result is
   begin
      MC_FS.Close (R); MC_FS.Close (Out_R);
      Put_Line ("control-operation=" & Outcome'Image (Status));
      if Status /= OK then Set_Exit_Status (Failure); end if;
   end Result;
begin
   MC_Runtime.Initialize (Status); if Status /= OK then Result; return; end if;
   if Argument_Count = 3 and then Argument (1) = "make-authorities" then
      Load_Spec (Argument (2),"scope,serial,operations-key,operations-principal,operations-domain,security-key,security-principal,security-domain");
      Hex_Field ("scope",A.Scope); A.Contract := MC_Contract_Profile.Fingerprint; A.Count := 2;
      Num_Field ("serial",A.Serial); Hex_Field ("operations-key",A.Keys (1).Public_Key);
      Hex_Field ("operations-principal",A.Keys (1).Principal); Num_Field ("operations-domain",N);
      if Status = OK and then N in 1..65_535 then A.Keys (1).Domain := Natural (N); else Status := Invalid_Input; end if;
      A.Keys (1).Duty := MC_Control.Operations;
      Hex_Field ("security-key",A.Keys (2).Public_Key); Hex_Field ("security-principal",A.Keys (2).Principal);
      Num_Field ("security-domain",N);
      if Status = OK and then N in 1..65_535 then A.Keys (2).Domain := Natural (N); else Status := Invalid_Input; end if;
      A.Keys (2).Duty := MC_Control.Security;
      if Status = OK and then (not MC_Control.Valid (A) or else A.Keys (1).Domain = A.Keys (2).Domain)
      then Status := Denied; end if;
      if Status = OK then MC_FS.Open_Root (Argument (3),Out_R,Status,Private_Only => True); end if;
      if Status = OK then MC_Atomic.Write (Out_R,"control-authorities.bin",MC_Control_Codec.Encode (A),True,Status); end if;
   elsif Argument_Count = 4 and then Argument (1) = "make-proposal" then
      Load_Spec (Argument (2),"scope,mode,trust-epoch,request-id,reason,recovery-receipt,ttl-ms");
      Hex_Field ("scope",P.Scope); Num_Field ("trust-epoch",P.New_Trust_Epoch);
      Hex_Field ("request-id",P.Request_ID); Hex_Field ("reason",P.Reason);
      Hex_Field ("recovery-receipt",P.Recovery_Receipt); Num_Field ("ttl-ms",TTL);
      if Status = OK then MC_Properties.Get (Doc,"mode",V,Status); end if;
      if Status = OK then
         if MC_Text.Image (V) = "running" then P.Desired := MC_Control.Running;
         elsif MC_Text.Image (V) = "hold" then P.Desired := MC_Control.Changes_Held;
         elsif MC_Text.Image (V) = "quarantine" then P.Desired := MC_Control.Quarantined;
         else Status := Invalid_Input; end if;
      end if;
      if Status = OK then Load_Authority (Argument (3)); end if;
      if Status = OK and then P.Scope /= A.Scope then Status := Denied; end if;
      if Status = OK then MC_FS.Stat (R,"control-state.bin",Info,Status); end if;
      if Status = OK and then Info.Kind /= MC_FS.Absent then
         MC_Control_IO.Read_State (R,A.Scope,S,H,Status);
         if Status = OK then P.Expected_State := H; P.Expected_Revision := S.Revision; end if;
      end if;
      if Status = OK then MC_Clock.Read_Boot_ID (Boot,Status); end if;
      if Status = OK then MC_Clock.Boottime_Milliseconds (Now,Status); end if;
      if Status = OK and then (TTL = 0 or else TTL > 300_000 or else TTL > Counter'Last-Now) then Status := Invalid_Input; end if;
      if Status = OK then
         P.Boot_ID := Boot; P.Not_Before := Now; P.Expires := Now+TTL;
         P.Contract := A.Contract; P.Authority_Digest := MC_SHA256.Hash (AF);
         MC_FS.Open_Root (Argument (4),Out_R,Status,Private_Only => True);
         if Status = OK then MC_Atomic.Write (Out_R,"control-proposal.bin",MC_Control_Codec.Encode (P),True,Status); end if;
      end if;
   elsif Argument_Count = 4 and then Argument (1) = "sign-proposal" then
      Load_Proposal (Argument (2));
      if Status = OK and then P.Contract /= MC_Contract_Profile.Fingerprint then Status := Unsupported; end if;
      if Status = OK then
         declare Signed : Bytes (1..2+Domain'Length+PF'Length); begin
            MC_Codec.Put16 (Signed,1,Domain'Length);
            for I in Domain'Range loop Signed (2+I) := Byte (Character'Pos (Domain (I))); end loop;
            Signed (3+Domain'Length..Signed'Last) := PF;
            MC_Keys.Sign (Argument (3),Signed,PK,Sig,Status);
         end;
      end if;
      if Status = OK then MC_FS.Open_Root (Argument (4),Out_R,Status,Private_Only => True); end if;
      if Status = OK then MC_Atomic.Write (Out_R,"control-signature-" & MC_Hex.Encode (PK) & ".bin",Sig,True,Status); end if;
   elsif Argument_Count = 5 and then Argument (1) = "bundle" then
      Load_Authority (Argument (2)); if Status = OK then Load_Proposal (Argument (3)); end if;
      if Status = OK and then (P.Scope /= A.Scope or else P.Authority_Digest /= MC_SHA256.Hash (AF)) then Status := Denied; end if;
      MC_FS.Close (R);
      if Status = OK then MC_FS.Open_Root (Argument (4),R,Status,Private_Only => True); end if;
      if Status = OK then
         for I in 1..A.Count loop
            declare Name : constant String := "control-signature-" & MC_Hex.Encode (A.Keys (I).Public_Key) & ".bin"; begin
               MC_FS.Stat (R,Name,Info,Status); exit when Status /= OK;
               if Info.Kind /= MC_FS.Absent then
                  MC_Atomic.Read (R,Name,Sig,Used,Status); exit when Status /= OK;
                  if Used /= Sig'Length then Status := Corrupt; exit; end if;
                  MC_Authentic.Verify (Domain,PF,Sig,A.Keys (I).Public_Key,Status); exit when Status /= OK;
                  Bundle (1+(I-1)*64..I*64) := Sig;
               end if;
            end;
         end loop;
      end if;
      if Status = OK then MC_FS.Open_Root (Argument (5),Out_R,Status,Private_Only => True); end if;
      if Status = OK then MC_Atomic.Write (Out_R,"control-signatures.bin",Bundle,True,Status); end if;
   elsif Argument_Count = 5 and then Argument (1) = "submit" then
      MC_Hex.Decode (Argument (3),Scope,Status);
      if Status = OK then
         declare B : constant Bytes := MC_File_IO.Read_File (Argument (4),320);
                 G : constant Bytes := MC_File_IO.Read_File (Argument (5),512); begin
            if G'Length /= 512 then Status := Invalid_Input;
            else MC_Control_IO.Submit (Argument (2),Scope,B,G,Status); end if;
         end;
      end if;
   elsif Argument_Count = 3 and then Argument (1) = "status" then
      MC_Hex.Decode (Argument (3),Scope,Status);
      if Status = OK then MC_FS.Open_Root (Argument (2),R,Status,Private_Only => True); end if;
      if Status = OK then MC_Control_IO.Read_State (R,Scope,S,H,Status); end if;
      if Status = OK then
         Put_Line ("mode=" & MC_Control.Mode'Image (S.Current)); Put_Line ("revision=" & MC_Numbers.Image (S.Revision));
         Put_Line ("trust-epoch=" & MC_Numbers.Image (S.Trust_Epoch)); Put_Line ("state-sha256=" & MC_Hex.Encode (H));
      end if;
   elsif Argument_Count = 2 and then Argument (1) = "inspect-proposal" then
      Load_Proposal (Argument (2));
      if Status = OK then
         Put_Line ("scope=" & MC_Hex.Encode (P.Scope)); Put_Line ("mode=" & MC_Control.Mode'Image (P.Desired));
         Put_Line ("expected-state=" & MC_Hex.Encode (P.Expected_State));
         Put_Line ("trust-epoch=" & MC_Numbers.Image (P.New_Trust_Epoch));
         Put_Line ("request-id=" & MC_Hex.Encode (P.Request_ID)); Put_Line ("boot=" & MC_Hex.Encode (P.Boot_ID));
         Put_Line ("reason=" & MC_Hex.Encode (P.Reason)); Put_Line ("recovery-receipt=" & MC_Hex.Encode (P.Recovery_Receipt));
         Put_Line ("not-before-boottime-ms=" & MC_Numbers.Image (P.Not_Before));
         Put_Line ("expires-boottime-ms=" & MC_Numbers.Image (P.Expires));
         Put_Line ("signature-and-facts-NOT-verified=true");
      end if;
   else
      Put_Line (Standard_Error,"controlctl: make-authorities SPEC DIR | make-proposal SPEC POLICY OUT | sign-proposal PROPOSAL KEYDIR OUT");
      Put_Line (Standard_Error,"bundle POLICY PROPOSAL SIGDIR OUT | submit POLICY SCOPEHEX PROPOSAL BUNDLE | status POLICY SCOPEHEX | inspect-proposal FILE");
      Status := Invalid_Input;
   end if;
   Result;
exception when others => MC_FS.Close (R); MC_FS.Close (Out_R); Put_Line (Standard_Error,"control-operation=INDETERMINATE"); Set_Exit_Status (Failure);
end Controlctl;
