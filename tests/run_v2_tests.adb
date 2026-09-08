-- SPDX-License-Identifier: MIT
with MC_Types; use MC_Types; with MC_Base64; with MC_JSON; with MC_Requests; with MC_Protocol;
with MC_Witness; with MC_SHA256; with MC_Text; with MC_Numbers; with MC_Properties;
with MC_Paths; with MC_Dirents; with MC_Numbers;
with Test_Support; use Test_Support;
procedure Run_V2_Tests with SPARK_Mode=>Off is
   use type MC_Types.Byte;
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
   declare
      Last_Data : Bytes(Integer'Last .. Integer'Last) := (others => 123);
   begin
      MC_JSON.Parse(Last_Data,D,S); Expect(S/=OK,"json-last-index-rejected");
      D:=(others=><>); D.Count:=1;
      D.Nodes(1):=(Node_Kind=>MC_JSON.Number_Node,First=>3,Last=>2,others=><>);
      MC_JSON.Natural_Number(B("123"),D,1,N,S); Expect(S/=OK,"json-reversed-number-span");
      D.Nodes(1).First:=0; D.Nodes(1).Last:=2;
      MC_JSON.Natural_Number(B("123"),D,1,N,S); Expect(S/=OK,"json-number-span-outside-data");
      D.Nodes(1):=(Node_Kind=>MC_JSON.String_Node,First=>1,Last=>3,others=><>);
      MC_JSON.String_Bytes(B("abc"),D,1,Out_Data,Used,S);
      Expect(S/=OK,"json-string-span-requires-quotes");
      MC_JSON.Parse(B("[1]"),D,S); Expect(S=OK,"json-array-for-metadata-check");
      D.Nodes(2).End_Index:=0;
      Expect(MC_JSON.Element(D,1,1)=0,"json-array-rejects-invalid-child-span");
      MC_JSON.Parse(B("{""k"":1}"),D,S); Expect(S=OK,"json-object-for-metadata-check");
      D.Count:=2; D.Nodes(1).End_Index:=2;
      Expect(MC_JSON.Member(B("{""k"":1}"),D,1,"k")=0,"json-member-requires-value-node");
      MC_JSON.Parse(B("""x"""),D,S); Expect(S=OK,"json-string-for-output-boundary");
      MC_JSON.String_Bytes(B("""x"""),D,1,Last_Data,Used,S);
      Expect(S=OK and then Used=1 and then Last_Data(Integer'Last)=120,"json-output-last-index");
      MC_Base64.Decode("Zg==",Last_Data,Used,S);
      Expect(S=OK and then Used=1 and then Last_Data(Integer'Last)=102,"base64-output-last-index");
      Expect(MC_Base64.Encode(Last_Data)="Zg==","base64-input-last-index");
   end;
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
      Negative_Origin_Bytes : Bytes(-1..-2);
      Negative_Origin_Text : String(-1..-2);
   begin
      MC_Properties.Parse(Last_Byte,P,S); Expect(S/=OK,"properties-last-index-rejected");
      MC_Properties.Parse(Empty_Bytes,P,S); Expect(S/=OK,"properties-empty-rejected");
      Expect(not MC_Properties.Has_Exactly(P,Last_Key),"properties-key-last-index-rejected");
      Expect(not MC_Properties.Has_Exactly(P,""),"properties-empty-key-list-rejected");
      MC_Properties.Parse(Negative_Origin_Bytes,P,S);
      Expect(S/=OK,"properties-null-negative-origin");
      MC_JSON.Parse(Negative_Origin_Bytes,D,S); Expect(S/=OK,"json-null-negative-origin");
      Expect(not MC_Paths.Safe_Relative(Negative_Origin_Text),"path-null-negative-origin");
   end;
   declare
      L, Before : MC_Dirents.Listing;
      Entry_Data : Bytes(1..24):=(others=>0);
      Last_Entry : Bytes(Integer'Last-23 .. Integer'Last):=(others=>0);
      Empty_Entries : Bytes(-1..-2);
      use type MC_Dirents.Listing;
   begin
      Entry_Data(17):=24; Entry_Data(20):=122;
      MC_Dirents.Append_Linux64_LE(Entry_Data,L,S);
      Expect(S=OK and then L.Count=1 and then MC_Dirents.Image(L.Names(1))="z","dirent-decode");
      Entry_Data(20):=97; MC_Dirents.Append_Linux64_LE(Entry_Data,L,S);
      Expect(S=OK and then L.Count=2,"dirent-append");
      MC_Dirents.Sort(L);
      Expect(MC_Dirents.Image(L.Names(1))="a" and then MC_Dirents.Image(L.Names(2))="z","dirent-sort");
      Before:=L; MC_Dirents.Append_Linux64_LE(Entry_Data,L,S);
      Expect(S/=OK and then L=Before,"dirent-duplicate-is-atomic");
      MC_Dirents.Append_Linux64_LE(Entry_Data(1..23),L,S);
      Expect(S/=OK and then L=Before,"dirent-truncation-is-atomic");
      Last_Entry(Integer'Last-7):=24; Last_Entry(Integer'Last-4):=122;
      MC_Dirents.Append_Linux64_LE(Last_Entry,L,S);
      Expect(S/=OK and then L=Before,"dirent-last-index-is-atomic");
      MC_Dirents.Append_Linux64_LE(Empty_Entries,L,S);
      Expect(S=OK and then L=Before,"dirent-null-negative-origin");
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
   declare
      Power : Counter:=1;
      procedure Number_Image(N : Counter) is
         Reference : constant String:=Counter'Image(N);
         Encoded : constant String:=MC_Numbers.Image(N);
         Parsed : Counter;
      begin
         Expect(Encoded=Reference(Reference'First+1..Reference'Last)
           and then Encoded'First=2,"bounded-decimal-image");
         MC_Numbers.Parse(Encoded,Parsed,S);
         Expect(S=OK and then Parsed=N,"bounded-decimal-roundtrip");
      end;
   begin
      Number_Image(0); Number_Image(Counter'Last-1); Number_Image(Counter'Last);
      for I in 1..18 loop
         Number_Image(Power-1); Number_Image(Power); Number_Image(Power+1);
         Power:=Power*10;
      end loop;
      Number_Image(Power-1); Number_Image(Power); Number_Image(Power+1);
   end;
   Report;
end Run_V2_Tests;
