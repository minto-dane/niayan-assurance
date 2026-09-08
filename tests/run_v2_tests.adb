-- SPDX-License-Identifier: MIT
with MC_Types; use MC_Types; with MC_Base64; with MC_JSON; with MC_Requests; with MC_Protocol;
with MC_Witness; with MC_SHA256; with MC_Text; with MC_Numbers; with MC_Properties;
with Test_Support; use Test_Support;
procedure Run_V2_Tests with SPARK_Mode=>Off is
   use type MC_Requests.Request; use type MC_JSON.Index;
   function B(S : String) return Bytes is
      R : Bytes(1..S'Length);
   begin for I in R'Range loop R(I):=Byte(Character'Pos(S(S'First+I-1))); end loop; return R; end;
   Out_Data : Bytes(1..1_024); Used : Natural; S : Outcome; N : Counter;
   D : MC_JSON.Document; P : MC_Properties.Document; W,W2 : MC_Witness.Statement; WF : MC_Witness.Frame;
   R,R2 : MC_Requests.Request; RF : MC_Requests.Request_Bytes;
   procedure Bad64(T : String) is
   begin MC_Base64.Decode(T,Out_Data,Used,S); Expect(S/=OK,"base64-invalid-" & T); end;
   procedure Bad_JSON(T : String) is
   begin MC_JSON.Parse(B(T),D,S); Expect(S/=OK,"json-invalid"); end;
begin
   for Length in 0..256 loop
      declare Data : Bytes(1..Length); begin
         for I in Data'Range loop Data(I):=Byte(I mod 256); end loop;
         MC_Base64.Decode(MC_Base64.Encode(Data),Out_Data,Used,S);
         Expect(S=OK and then Used=Length and then Out_Data(1..Used)=Data,"base64-roundtrip");
      end;
   end loop;
   Bad64("Zg="); Bad64("Zh=="); Bad64("Zm9="); Bad64("Zg== "); Bad64("____"); Bad64("=AAA");
   MC_JSON.Parse(B("{""count"":1,""kvs"":[{""key"":""YQ=="",""value"":""Yg=="",""mod_revision"":12}]}"),D,S);
   Expect(S=OK,"etcd-json-profile");
   declare Data : constant Bytes:=B("{""count"":1,""kvs"":[{""key"":""YQ=="",""value"":""Yg=="",""mod_revision"":12}]}"); begin
      MC_JSON.Natural_Number(Data,D,MC_JSON.Member(Data,D,1,"count"),N,S);
      Expect(S=OK and then N=1,"json-count");
      Expect(MC_JSON.Element(D,MC_JSON.Member(Data,D,1,"kvs"),2)=0,"json-array-bound");
   end;
   Bad_JSON("{""a"":1,""a"":2}"); Bad_JSON("{""a"":-1}"); Bad_JSON("{""a"":1e2}");
   Bad_JSON("{""a"":""\u0061""}"); Bad_JSON("[1,]"); Bad_JSON("{}garbage");
   MC_Numbers.Parse("9223372036854775807",N,S); Expect(S=OK and then N=Counter'Last,"counter-last");
   MC_Numbers.Parse("9223372036854775808",N,S); Expect(S/=OK,"counter-overflow");
   MC_Numbers.Parse("01",N,S); Expect(S/=OK,"counter-noncanonical");
   MC_Properties.Parse(B("key=a" & ASCII.LF & "key=b" & ASCII.LF),P,S); Expect(S/=OK,"properties-duplicate");
   MC_Properties.Parse(B("key=a"),P,S); Expect(S/=OK,"properties-missing-terminator");
   MC_Properties.Parse(B("first=a" & ASCII.LF & "second=b" & ASCII.LF),P,S);
   Expect(S=OK and then MC_Properties.Has_Exactly(P,"second,first"),"properties-exact-keys");
   Expect(not MC_Properties.Has_Exactly(P,"first,first"),"properties-repeated-key-not-exact");
   declare
      Last_Byte : Bytes(Integer'Last .. Integer'Last) := (others => 10);
      Last_Key : constant String(Integer'Last .. Integer'Last) := "k";
      Empty_Bytes : Bytes(1..0);
   begin
      MC_Properties.Parse(Last_Byte,P,S); Expect(S/=OK,"properties-last-index-rejected");
      MC_Properties.Parse(Empty_Bytes,P,S); Expect(S/=OK,"properties-empty-rejected");
      Expect(not MC_Properties.Has_Exactly(P,Last_Key),"properties-key-last-index-rejected");
      Expect(not MC_Properties.Has_Exactly(P,""),"properties-empty-key-list-rejected");
   end;
   R.Transaction_ID:=(others=>1); R.Plan_Digest:=(others=>2); R.Contract_Digest:=(others=>3);
   R.Stage_Set_Digest:=(others=>4); R.Evidence_Digest:=(others=>5);
   for A in MC_Requests.Requested_Action loop
      R.Action:=A; RF:=MC_Requests.Encode(R); MC_Requests.Decode(RF,R2,S);
      Expect(S=OK and then R2=R,"all-v2-actions-roundtrip");
      RF(192):=1; MC_Requests.Decode(RF,R2,S); Expect(S/=OK,"unknown-request-field-denied");
   end loop;
   RF:=MC_Requests.Encode(R); RF(6):=1; MC_Requests.Decode(RF,R2,S); Expect(S/=OK,"legacy-request-denied");
   MC_Requests.Decode(RF(1..160),R2,S); Expect(S/=OK,"legacy-size-denied");
   R.Action:=MC_Requests.Commit; R.Evidence_Digest:=Zero_Digest;
   MC_Requests.Decode(MC_Requests.Encode(R),R2,S); Expect(S/=OK,"commit-without-evidence");
   W.Cluster_ID:=(others=>1); W.Node_ID:=(others=>2); W.Root_ID:=(others=>3); W.Transaction_ID:=(others=>4);
   W.Boot_ID:=(others=>5); W.Plan:=(others=>6); W.Contract:=(others=>7); W.Epoch:=1; W.Token:=2;
   W.Issued:=100; W.Expires:=120;
   WF:=MC_Witness.Encode(W); MC_Witness.Decode(WF,W2,S); Expect(S=OK,"witness-codec");
   Expect(MC_Witness.Matches(W2,W,110,20),"witness-fresh");
   Expect(not MC_Witness.Matches(W2,W,120,20),"witness-expiry-exclusive");
   W2.Boot_ID:=(others=>9); Expect(not MC_Witness.Matches(W2,W,110,20),"witness-boot-binding");
   Report;
end Run_V2_Tests;
