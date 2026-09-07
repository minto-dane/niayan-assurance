# 仕様 E-REC-1: ファイル変更の再生と回復

## 一意な変更

変更はroot ID、transaction ID、plan SHA-256、target generation、epoch、fence、変更数で束縛します。
各レコードは連続sequence、previous record hash、同一の束縛を満たさなければなりません。
記録のダイジェストは誤破損検出です。媒体全体の古いコピーへの置換を防ぐ独立アンカーは別の前提です。

## 状態と許される遷移

|段階|許される記録|確認する条件|
|---|---|---|
|空の再生状態|Preparedのみ|Index=0、正確なplan hash|
|Forward|Apply_Intent / Apply_Done|1から順に処理、Doneには対応するIntentが必要|
|全Done|Applied|保留Intentなし、全実ファイルがAfter|
|Ready_To_Commit|Commit_Intent または Restore_Intent|確定と復旧の選択を認可|
|Commit_Pending|同一receiptのCommit_Intent / Committed|既に記録した確定根拠を変更しない|
|Reverse_Change|Restore_Intent / Restore_Done|変更数から逆順、同一receiptを維持|
|逆順完了|Restored|Next=0、保留Intentなし、全実ファイルをBeforeへ再照合|
|Forward_Final / Reverse_Final|追加レコードなし|終端後の修復記録も別監査streamへ|

同じIndexのIntent再記録は、その意味が同じ場合に限り受理します。Doneの重複や、Indexを飛ばす記録は拒否します。
Commit_Intentの後でRestoreへ変える経路はありません。再認可が新しくても、元の決定receiptは不変です。

## 実ファイルとの照合

ForwardのDone済み領域はAfter、まだIntentがない未来領域はBefore、保留IntentだけはBefore/Afterのどちらでもよいとします。
Ready/Commit/CommittedはすべてAfterです。Reverseでは完了済みsuffixをBeforeとし、RestoredはすべてBeforeです。
BeforeでもAfterでもない状態、DoneなのにBeforeへ戻った状態、未着手なのにAfterになった状態は停止条件です。
これにより単なる「どちらかの内容に見える」という緩い照合をやめます。
同一Before=Afterの項目は両方への一致として扱います。

## 中断と永続化

Intent永続化の前に副作用を開始しません。副作用後は内容・属性の確認と永続化を経てDoneを記録します。
Commitでは、Commit_Intent、root.stateの新世代（Activeを保持）、Committed、Active解除を順に永続化します。
新世代公開後の応答喪失は、その公開と履歴を照合して終了します。旧世代へ戻してCommitをやり直しません。
未完復旧を閉じて再開するときも同じtransaction IDとreceiptを使います。

## 欠落と破損

既存トランザクションのResume/Resume_Recordedは`Create_If_Missing => False`です。
ジャーナルがない場合は新規空ファイルを作らずCorruptを返します。Prepare時の初期作成と別API条件です。
最後の1〜255byteだけが不完全な場合は、原本bytes/hashと独立監査を永続化してから、その部分末尾のみを扱います。
256byteの完全レコードが不正なら自動切り詰めをしません。Partial tailがあることから、副作用なしとは推論しません。

## 回復方向

この状態機械は、安全な記録解釈を行うもので、業務データの逆移行を発明しません。
実際のApply継続/Restoreの認可は、現在の隔離、データ互換性、回復用CAS、容量、権限、信頼情報の根拠が必要です。
原本を保持し、別の復旧媒体へ移行する場合もroot identityと世代の正本を独立に確認します。

## 終端の再照合

Reconcile_Terminalは新しい世代判断をしません。記録されたreceiptを変更せず、現在の認可へ渡して再照合します。
新世代のaccepted planとpackage setの両方を確認し、実ファイル全体がAfterなら未完のCommitted記録を完結します。
Reverse_FinalはBeforeの再照合と現在の認可を経てActive状態を解除します。
古いreceiptが存在することだけで、失効や所有権変更後の操作を認可しません。
