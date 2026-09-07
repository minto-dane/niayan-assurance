> 現行の統合範囲・初期化・互換変更は [統一管理仕様](engineering/specs/unified-management.ja.md) を参照。以下の個別SDKの記述は、全接続・全試験の完成を意味しません。

# 全対象停止確認（Stop Barrier v1）

## 契約と責任

実装: `MC_Stop_Barrier`、`MC_Stop_Barrier_Auth`、`State_Barrier_Store`。
Policy/Stateは各4608byte、Evidenceは320byteのcanonical binaryです。
末尾SHA-256は誤り検出であって、署名や権限証明ではありません。
Evidenceの署名domainは`MISSION-CORE-STOP-ACK-v1`、署名方式は既存のEd25519境界を使用します。

Policyは、cluster・barrier・receiver boot・正確な変更計画・完全な対象一覧digest・現在の共有プロファイル・変更許可キー内容/版・epoch・最大有効時間へ拘束します。
Policyの認証と完全性は独立した管理主体で行ってください。自己署名した任意の鍵を持ち込めば、運用上の認可を得られる仕組みではありません。
署名鍵が一致しても、観測内容の物理的真実までは暗号で保証できません。

## 対象の識別

一行は(node ID, resource ID, subject boot ID)です。同じリソースが別ノードに存在しても別行です。
同一(node, resource)の二重登録、同一nodeに矛盾するboot/stop鍵を持つ登録、stop鍵とfence鍵の役割重複を拒否します。
32行を超える場合は契約改訂または相互に独立と証明できる別の対象範囲を設計します。単純に複数バリアへ分割して全体原子性を得たと主張しないでください。

## Drained

停止側の認証済み証拠は、永続的な停止ラッチ、受付キューの閉鎖、In_Flight=0、Unknown_Effects=0、Last_Dispatched=Last_Completedを必要とします。
`Last_Completed`は「最大の完了ID」ではなく、途中に未解決の穴を残さない**連続して結果確定済みのwatermark**として発行する必要があります。
並列タスクの最大IDだけを報告する観測器は、この契約の前提を満たしません。
永続停止ラッチが実行受付・再起動経路すべてを止め、再認可まで維持されることを統合側で確認します。

## Fenced

node自身の停止報告ではなく、独立したfence観測鍵を使います。
必要な全隔離経路maskと、古い実行個体のretirementが永続的であることを要求します。
この構成は電源断・ネットワーク・共有ストレージ・資格情報等のどれを隔離するかを自動発見しません。実際の書込経路を把握してPolicyへ入れる必要があります。
既にIsolatedの対象をnode自身のDrained報告で解除しません。

## 時計と再送

EvidenceのStampはreceiver-localなmonotonic時刻とreceiverのboot IDへ拘束します。
遠隔ノードのmonotonic値をそのまま代入してはいけません。認証済みchallenge/応答とreceiver時刻を結ぶ観測橋を適格化するか、該当条件を満たす局所観測器を使ってください。
今回その分散観測橋・配信daemonは提供していません。

Node_Agent/Fence_Observerのsequenceを別々に保持します。再送で期限を延長しません。
未来の観測、古いepoch/guard、期限切れ、受信boot変更を拒否します。receiver再起動時は新しい認可済みbarrierと新しい観測が必要です。
生存確認や最大時刻差だけで別boot間の時間を比較しません。

## 状態遷移

`Collecting`で全対象の停止/隔離証拠を集め、`Ready`確認後に`Seal`します。
`Sealed`は恒久的な許可ではありません。利用時に`Usable`で最新状態・鮮度を再検査します。
署名・世代・時刻が正しい負の観測（キュー再開、未確定操作、隔離経路喪失等）を受けた場合は`Blocked`へ移し、既存sealも無効にします。
`Blocked`は時間や正常観測だけで解除しません。原因を解消し、別の認可済みbarrierを作ります。
不正署名や未認可の観測で任意に状態を書き換えることも許しません。

## CLI

4repoの共通検査コマンドです。ビルド後、pkgctl/statectl/assure/missionctlの実際のmain名は各GPRで確認してください。

```
check-stop-policy FILE
check-stop-state FILE
verify-stop-evidence POLICY EVIDENCE SIGNATURE
```

これらは構造・署名を検査するだけです。出力の`authorized=false`は意図したものです。
Policyの権限、対象一覧の完全性、実観測、最新etcd状態、実行可能性は確認しません。
public fixtureの鍵を本番authorityに入れないでください。

## 永続化

`State_Barrier_Store`は、認可callbackとローカル制御状態を通し、期待etcd revision・before-state hashを確認して比較更新します。
最新の負の観測が先に確定した場合、古いstateでのSealの比較更新は失敗します。
ただしetcdの更新と外部ファイルの変更は同じ原子操作にはなりません。実行器自身の停止ラッチ・fencing・操作直前の確認が別途必要です。
