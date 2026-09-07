-- SPDX-License-Identifier: MIT
package Contract_Lock with SPARK_Mode => Off is
   Count : constant := 153;
   subtype Item_Index is Positive range 1 .. Count;
   function Name (Index : Item_Index) return String;
   function Expected (Index : Item_Index) return String;
end Contract_Lock;
