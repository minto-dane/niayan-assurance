-- SPDX-License-Identifier: MIT
with MC_Types; use MC_Types; with MC_Journal_Budget;
with Test_Support; use Test_Support;
procedure Run_Journal_Budget_Tests with SPARK_Mode => Off is
begin
   Expect(MC_Journal_Budget.Fits(0,8,4,4),"exact reservation fits");
   Expect(not MC_Journal_Budget.Fits(1,8,4,4),"cannot borrow pending capacity");
   Expect(not MC_Journal_Budget.Fits(9,8,0,0),"overfull rejected");
   Expect(not MC_Journal_Budget.Fits(0,8,9,0),"overcommitted rejected");
   Expect(MC_Journal_Budget.Fits(Counter'Last-2,Counter'Last,1,1),"last record checked without addition");
   Expect(not MC_Journal_Budget.Fits(Counter'Last,Counter'Last,1,1),"overflow cannot admit");
   for Used in Counter range 0..32 loop
      for Pending in Counter range 0..32 loop
         for Added in Counter range 0..32 loop
            Expect(MC_Journal_Budget.Fits(Used,32,Pending,Added) =
              (Used+Pending+Added<=32),"finite exhaustive arithmetic");
         end loop;
      end loop;
   end loop;
   Report;
end Run_Journal_Budget_Tests;
