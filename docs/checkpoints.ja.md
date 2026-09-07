# immutable checkpointと独立アンカー

## 実装

`MC_Checkpoint` は320-byteのcanonical descriptorと連続性の判定です。
`MC_Checkpoint_Store` は `Load / Publish / Reconcile` を持つgeneric実I/O SDKです。
Snapshotは最大MC_Types.Max_Message(1 MiB)、root/stream/contract、exact payload digest、世代、previous digest、loghead、監査receipt、covered record数、trust epoch、replay epoch/token/sequenceを含みます。

`Follows` は世代+1・previous完全一致・各highwater非減少を要求します。同じcovered record数ならlogheadも不変です。counter overflowを避けて判定します。

## 必須コネクタ契約

- `Authorize(phase,before,after)`：対象root/stream、変更方針、現在の変更停止、承認根拠を検査。
- `Validate_State(descriptor,payload)`：payloadが全状態を正しく表すか、内部不変条件とrecord境界が一致するか、信頼・再送情報を省略していないか検査。単なるhash一致だけでは不足。
- `Check_Anchor(descriptor,manifest)`：独立した信頼ドメインの受理済みmanifest完全一致を検査。ローカルcurrentを見てOKと返してはいけません。
- `Advance_Anchor(expected,descriptor,manifest)`：exact previousからの認証付きCAS。結果不明はIndeterminate。失敗した系と同じストレージへ置かない。

`Quiescent=True` は呼出し側の義務です。対象の書込みを本当に静止させ、ログ境界を取得してください。任意workerの全排他をこのSDKが自動確立するわけではありません。

## 永続化順序と中断

1. exact currentとexternal anchorを確認。
2. 内容アドレスのsnapshotとmanifestをimmutable保存・同期。
3. pending descriptorを保存・同期。
4. 認可を再確認しexternal anchorをCAS更新。
5. anchor完全一致を再確認しcurrent pointerを公開・同期。

4の応答を失った場合、`Reconcile`は外部アンカーが候補を受理した場合だけ、payload検査・previous照合の後currentへ公開します。epochだけ合う別候補は拒否します。
4より前で停止した未受理pendingは勝手に採用しません。現版は未受理pendingの署名付き破棄/置換APIを持たず、次のPublishを阻止します。運用者が証拠を保全して判断する境界です。失敗したbootstrapも同様です。

## 意図的に行わないこと

元WAL、payload CAS、監査データの削除・切詰めはしません。既存MC_Gate/復旧台帳を自動的にcheckpoint形式へ移す仕組みも未接続です。これを無制限なjournal growth問題の全解決と表示しないでください。
future compactorでは、外部アンカー、独立復元試験、全consumerのreplay floor、参照集合の固定、active writerの静止、監査receiptの維持を別に確認する必要があります。

IO試験`run_checkpoint_io_tests`のアンカーは、応答喪失を制御する**メモリ上のtest double**です。実fsync/read/atomic publishを実行するコードですが、電源断や本番アンカーの実証ではありません。今回そのAda試験自体も未実行です。
