# 上限・運用責任・停止条件

| 項目 | 実装上の上限/条件 |
|---|---|
| shared予約/rollout/cluster view | 31ノード |
| service別cluster budget | 16サービス |
| 依存グラフ | 32ノード |
| retry timestamp履歴 | 64枠、累積policy上限は最大1,000,000 |
| 健全性/多くの追加契約frame | 256 bytes、healing stateは1,024、rolloutは8,192 |
| healing/log基盤 | 固定レコード、最大1,048,576 records、全prefix走査 |
| inventory/ファイル計画 | 最大1,024対象、既存planの型/容量制約も適用 |
| scrub CLI | 256MiB、60秒の通常処理予算。kernel内I/O停止を打ち切るhard deadlineではない |
| rich etcd予約 | 最大3回のCAS再試行、毎回新しいqualified観測 |
| native runtime | Linux x86-64/glibc向けの既存FFIを前提。別ABIへそのまま配布しない |

この上限はベンチマーク、可用性SLA、推奨運用規模を意味しません。全31ノード/16サービスの組み合わせや全WAL容量を実測・証明したという表示ではありません。

## 運用で必要なもの

クォーラム/データ複製/障害ドメインを正しく観測する接続、鍵と失効の運用、外部high-waterと監査保管、空き容量/履歴長の監視、検証したバックアップと復元、物理fencing、NTPだけに依存しないreceiver-local鮮度管理、実サービスごとの業務ヘルス/データ互換性の規約を用意してください。

新しい恒常heartbeat daemonはありません。event/incidentの進行を要求として供給する設計です。大量のノイズを署名してWALへ毎秒流すことは避け、外側でbounded queueと監視/容量計画が必要です。そのqueue/外部alarm連携はsite adapterの責任です。

## 自動解除しないもの

未解決effect、期限切れslot、累積予算、critical integrity hold、完全レコード破損、失効した鍵、足りないData_Quorum、古いdata schema、対応外RPMは自動解除しません。継続のために保護を緩めるコードは追加していません。

一方で、通常のmaintenanceフラグや時間窓内の予算切れは恒久停止と区別します。正常な業務サービスを、リポジトリが一時的に不達であるだけで停止させる仕様ではありません。

## Rootと監査

実効UID所有private directoryによる境界は、不正なroot自身からは守れません。source manifestやhash-chainも、全コピーを同時に置き換えるrootに対する単独の耐改ざん証明ではありません。権限分離・MAC・独立鍵・外部監査/高水位・復旧経路が必要です。

外部commandは固定path/hash、shellなし、限定引数/環境で実行しますが、そのbinaryの動的libraryや全systemd D-Bus policyまで同時にhash固定するものではありません。target serviceに強い権限が必要だからといって、汎用shellのroot実行許可へ置き換えないでください。

## 長期運用で残る実装

journal compactionとbudget/holdの承認された移行API、observer鍵の重複期間付きrotation、複数controllerの高水位運用、site統合daemon、バックアップ装置/boot更新/DBmigration、alert輸送は未完成です。小さなcompile修正だけで済む項目とは区別します。
