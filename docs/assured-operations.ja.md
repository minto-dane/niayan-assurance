# 長期運用・統制・復旧の設計と実装境界

## 1. 実装位置

| 要求 | 実装 | 実行する副作用 | 接続が必要な部分 |
|---|---|---|---|
| 変更停止・隔離 | MC_Control / MC_Control_Codec / MC_Control_IO / controlctl | private policy内の署名要求・世代・履歴の永続化。既存MC_Gateのdispatch拒否 | 署名鍵の管理、全ノードへの配布・ACK、役割の本人確認 |
| 状態checkpoint | MC_Checkpoint / MC_Checkpoint_Store | immutable snapshot・manifest・pending/current公開、fsync、再照合 | 厳密な状態validator、独立した非巻戻しアンカー、状態の静止 |
| バックアップ受入 | MC_Backups | なし。型付き証拠からチェーンと復元候補を判定 | 実バックアップ、媒体検証、object lock確認、復元試験証明 |
| 一括保持 | Pkg_Retention_Batch | なし。削除集合を全体として検証 | 参照DBのCASと静止、認可、実削除、削除receipt |
| ノード再参加 | State_Readmission / State_Readmission_Store | mTLS etcd CASによる状態更新 | fencing、観測署名、実membership操作、業務ヘルス |
| 災害復旧 | State_Disaster / State_Disaster_Store | 独立した回復用etcdへCAS保存 | データ復元、新cluster、watch/cache無効化、資格情報の再発行 |

FSMが受け取る `Authenticated` や `All_Old_Writers_Isolated` などはネットワークからの真偽値を無条件に信じるためのものではありません。呼出し前に署名・対象・nonce・世代・観測内容を検査する認可器が必要です。generic callbackが存在するだけでは実運用接続は完成しません。

## 2. 変更停止と復旧の権限

3状態×9操作の権限を固定しました。Runningは全操作、Changes_HeldはInspect/Contain/Repair_Records、QuarantinedはInspect/Containのみです。
緩和はOperationsとSecurityの独立した主体系・鍵・ドメインを要求します。締め付けの既定閾値は1、緩和は2。最初からrunningの状態を作れません。

既存MC_Gate.Checkとledger修復が制御状態を検査します。新しいetcd storeも操作種別を検査します。ただし、任意の既存SDK呼出し、直接root操作、systemd/Pacemaker自身の全自律動作まで一つのファイルで止める機能ではありません。各管理系の責任者を明確にしてください。

これはdispatch境界の拒否です。チェック済みで既に外部へ送信した操作を取り消すことはできません。緊急停止の完全なフリート配布とノードACKの集計はサイト側です。分断ノードで保護を迂回して「全ノード停止完了」とは表示しないでください。

## 3. 復旧時にも単調な情報

通常のソフトウェア・配置状態とは別に、失効情報、受入禁止、信頼世代、再送high-water、クラスタincarnation、fencing token、監査証拠を扱います。
checkpointには再送epoch/token/sequenceを含め、同じログ件数で異なるlogheadへ置き換える候補も拒否します。
単に `Generation >= floor` ならよいとはしません。独立アンカーが受け入れたmanifest digestの完全一致を条件にします。

ローカルcontrol-stateは署名提案からのみ更新する運用を前提とし、全privateディレクトリを特権者が過去へ戻す攻撃まで単独で耐えません。rootを無制限に信頼しない環境では、MAC・別管理ストレージ・外部antirollback状態を含めて設計してください。秘密鍵や監査ログをsystem snapshotと一緒に戻してはいけません。

## 4. 修正した前版の不整合

`State_Rollout_Codec.Frame` は8192バイトでしたが、`State_Etcd.Compare_And_Swap`は4096バイトで拒否していました。新しい共通limitはdecoded 16384、保存Base64 21848、JSONの二重Base64 29132です。
Base64の丸め容量には16385バイトが入る場合があるため、読込み後にもdecoded lengthを独立に検査します。1/4096/4097/8192/16384と超過の試験を追加しました。

`MC_Atomic.Write(Must_Be_New=True)` は、名前衝突時に一時ファイルを残していました。確定したRENAME_NOREPLACE競合の場合だけ、この呼出しが作った一時名を削除・親directory同期するよう修正しました。rename結果不明時や保存先そのものは削除しません。

## 5. 今回の保証の表示

ソース、契約、試験はありますが、Ada build/testとGNATproveの実行結果はありません。コンパイルエラー、実行時不具合、証明未成立が残り得ます。形式検証対象の外側を含むTCBと、接続先が返す証拠の真実性は別問題です。
コンパイラまで検証した配布ではありません。独立参照モデルのPASSを実装のPASSと集計しないでください。
