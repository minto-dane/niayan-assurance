-- SPDX-License-Identifier: MIT
with MC_Types;use MC_Types;with MC_Log_Format;with MC_Request_Replay;with Test_Support;use Test_Support;
procedure Run_Request_Replay_Tests with SPARK_Mode=>Off is
   use type MC_Request_Replay.State;
   State,Before : MC_Request_Replay.State;E : MC_Log_Format.Log_Entry;S : Outcome;
begin
   E:=(Sequence=>1,Kind=>MC_Request_Replay.Genesis,Root_ID=>(others=>1),Operation_ID=>(others=>1),
       Object=>(others=>2),Generation=>1,others=><>);
   MC_Request_Replay.Consume(State,E,S);Expect(S=OK and then not State.Pending,"explicit genesis");
   E.Sequence:=2;E.Kind:=MC_Request_Replay.Begun;E.Operation_ID:=(others=>3);E.Epoch:=1;E.Token:=1;E.Index:=1;
   MC_Request_Replay.Consume(State,E,S);Expect(S=OK and then State.Pending,"begin requires durable fresh request");
   E.Sequence:=3;E.Kind:=MC_Request_Replay.Unknown_Outcome;E.Result:=Indeterminate;
   MC_Request_Replay.Consume(State,E,S);Expect(S=OK and then State.Pending,"unknown is not success");
   E.Sequence:=4;E.Kind:=MC_Request_Replay.Known_Failure;E.Result:=Denied;
   MC_Request_Replay.Consume(State,E,S);Expect(S=OK and then not State.Pending,"known failure retained");
   E.Sequence:=5;E.Kind:=MC_Request_Replay.Begun;E.Operation_ID:=(others=>4);E.Index:=2;
   Before:=State;MC_Request_Replay.Consume(State,E,S);Expect(S/=OK and then State=Before,"stale failure code on begin rejected");
   E.Result:=OK;MC_Request_Replay.Consume(State,E,S);Expect(S=OK,"fresh begin explicitly resets result");
   E.Sequence:=6;E.Kind:=MC_Request_Replay.Known_OK;E.Root_ID:=(others=>9);Before:=State;
   MC_Request_Replay.Consume(State,E,S);Expect(S/=OK and then State=Before,"root confusion rejected");
   E.Root_ID:=(others=>1);E.Object:=(others=>9);MC_Request_Replay.Consume(State,E,S);
   Expect(S/=OK and then State=Before,"receipt bound to request digest");
   E.Object:=(others=>2);MC_Request_Replay.Consume(State,E,S);Expect(S=OK,"exact terminal receipt");
   E.Sequence:=7;E.Kind:=MC_Request_Replay.Genesis;E.Operation_ID:=E.Root_ID;E.Epoch:=0;E.Token:=0;E.Index:=0;
   Before:=State;MC_Request_Replay.Consume(State,E,S);Expect(S/=OK and then State=Before,"cannot reset existing ledger");Report;
end Run_Request_Replay_Tests;
