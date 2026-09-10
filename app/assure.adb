-- SPDX-License-Identifier: BSD-3-Clause
with Ada.Command_Line; with Ada.Text_IO; with Ada.Directories;
with MC_Types; use MC_Types;
with MC_CLI; with MC_File_IO; with MC_SHA256; with MC_Hex;
with Contract_Lock; with MC_Admin;
procedure Assure with SPARK_Mode => Off is
   use Ada.Command_Line; use Ada.Text_IO;
   Failed : Boolean := False;
   procedure Check_Listing (Base, Subdir : String) is
      Search : Ada.Directories.Search_Type;
      Item : Ada.Directories.Directory_Entry_Type;
      Known : Boolean;
      use type Ada.Directories.File_Kind;
   begin
      Ada.Directories.Start_Search(Search,Base & "/" & Subdir,"*");
      while Ada.Directories.More_Entries(Search) loop
         Ada.Directories.Get_Next_Entry(Search,Item);
         declare
            Simple : constant String := Ada.Directories.Simple_Name(Item);
         begin
            if Simple /= "." and then Simple /= ".." then
               Known := False;
               for K in Contract_Lock.Item_Index loop
                  if Contract_Lock.Name(K)=Subdir & "/" & Simple then Known := True; end if;
               end loop;
               if not Known or else Ada.Directories.Kind(Item)/=Ada.Directories.Ordinary_File then
                  Put_Line(Standard_Error,"unlisted or non-file contract entry: " & Subdir & "/" & Simple);
                  Failed := True;
               end if;
            end if;
         end;
      end loop;
      Ada.Directories.End_Search(Search);
   exception
      when others =>
         Ada.Directories.End_Search(Search);
         raise;
   end Check_Listing;
begin
   if MC_Admin.Handle then return; end if;
   if MC_CLI.Handle_Common then return; end if;
   if Argument_Count=1 and then Argument(1)="status" then
      Put_Line("component=assurance production_qualified=false");
      Put_Line("SPARK_contracts=SOURCE_ONLY GNATprove=NOT_RUN Ada_tests=NOT_RUN");
   elsif Argument_Count=1 and then Argument(1)="release-gate" then
      Put_Line(Standard_Error,"BLOCKED: consult evidence/qualification.json; passing unit tests alone is insufficient.");
      Set_Exit_Status(78);
   elsif Argument_Count in 2..7 and then Argument(1)="audit-vendors" then
      for Root in 2..Argument_Count loop
         Check_Listing(Argument(Root) & "/vendor/contracts","src");
         Check_Listing(Argument(Root) & "/vendor/contracts","runtime");
         for J in 1..Contract_Lock.Count loop
            declare
               Name : constant String := Argument(Root) & "/vendor/contracts/" & Contract_Lock.Name(J);
               Data : constant Bytes := MC_File_IO.Read_File(Name,1_048_576);
            begin
               if MC_Hex.Encode(MC_SHA256.Hash(Data))/=Contract_Lock.Expected(J) then
                  Put_Line(Standard_Error,"contract drift: " & Contract_Lock.Name(J)); Failed:=True;
               end if;
            end;
         end loop;
      end loop;
      if Failed then Set_Exit_Status(Failure); else Put_Line("locked-contract-copies-match"); end if;
   else
      Put_Line("assure status | release-gate | audit-vendors REPOSITORY_DIR [REPOSITORY_DIR ...]");
      Put_Line("assure contract-profile | contract-vector | check-header FILE | verify-envelope HEADER BODY SIG KEY");
      Put_Line("assure recovery-contract-vector | check-health-frame FILE | verify-health-report FRAME SIG KEY");
      Set_Exit_Status(Failure);
   end if;
exception
   when others =>
      Put_Line(Ada.Text_IO.Standard_Error,"assurance check failed");
      Ada.Command_Line.Set_Exit_Status(Ada.Command_Line.Failure);
end Assure;
