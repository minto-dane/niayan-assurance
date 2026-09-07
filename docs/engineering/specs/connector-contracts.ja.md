# 仕様 E-CONNECT-1: 接続契約と異常の意味

|接続先|事前条件|成功時に必要な根拠|結果不明時|
|---|---|---|---|
|ファイル実行|exact plan、writer排他、必要reader停止、前後像、保存容量|全対象の前後像・永続化・同一根拠のWAL|Contextを閉じ、同じIDで再観測|
|systemd|固定unitとrestart owner、boot/invocation、認可|プロセス操作と業務健康を別々に確認|command終了だけで再送しない|
|Pacemaker/fencing|対象node/incarnation、資源、全必要経路|旧writerの実隔離と保存先側の権限|TTLだけで停止済みにしない|
|etcd|mTLS、RBAC、cluster ID、revision下限、guard、exact key|同一Txnの比較と結果|linearizable再読込とID照合|
|NetworkManager|checkpointで戻せる対象、OOB管理経路、期限|独立経路の複数正常観測と確定|checkpointと操作IDを照合|
|バックアップ|dataset/系統、鍵、チェーン、独立コピー|exact restore trial receipt、RTO/RPO測定|元バックアップと証拠を保全|
|起動管理|署名image、boot試行ID、rollback互換性|exact起動構成と安定観測|既知の互換な回復媒体へ|

## API結果

OKは関数に定義した範囲の成功だけを意味します。外部実行まで含まないplannerのOKを実行完了へ昇格しません。
Denied/Unsupportedは条件不足、Corruptは信頼できない状態、Conflictは期待状態との不一致です。
Indeterminateは副作用の有無・保存の有無が分からない状態です。一般のretryで消してはいけません。

## 有効性と再検査

認可と観測はroot/cluster/node/resource/boot/op/plan/epoch/token/policy/schemaに結び付けます。
一度の署名検査だけで永続的な権限にしません。変更直前、確定、再開に必要な状態を再確認します。
観測情報は署名者が実測した意味を持つ必要があります。ネットワークから受け取ったhealthy=trueだけでは足りません。

## 責任の分離

要求者、承認者、観測者、隔離実行者を同じ鍵のラベル変更で済ませません。
固定実行ファイルのhashだけでは動的ライブラリや設定は検証されません。適格化対象に含めます。
外部commandに任意のshell文字列を渡す接続は認めません。native API/固定引数と権限範囲を使います。

## この版の互換性変更

MC_FS.Open_LockedとMC_Log.Openへ、Create_If_Missing（既定True）を追加しました。
修正対象の復旧経路からはFalseを明示します。全既存SDKの初期化が同一方式へ統合されたわけではありません。
引数の互換性がある場合も共有source profileは変わります。古い署名付き方針を自動移植しません。
Pkg_File_Engineのfinish-terminal認可は、終端再照合時に記録済みreceiptを渡す呼び出しを追加します。
アダプターは同じ根拠に対する現在の権限と対象を確認し、都合のよい別receiptへ置換しません。

## 管理入口

[統一管理](unified-management.ja.md)はnative gateに上位の二者承認/予約/履歴を追加するものです。
受信者の認可・停止witnessは削除せず、routeをlocal-onlyに限定します。remote transportの契約は未実装です。
