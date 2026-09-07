# 仕様 E-FORMAT-1: 永続形式・版・拒否規則

## ログ M C L O G 0 0 2

数値はネットワーク順の固定幅です。Ada配列は1始まり、表はbyte位置を1始まりで表します。

|位置|内容|
|---|---|
|1–8|magic `MCLOG002`|
|9–16|sequence U64（1..2^63-1）|
|17–18|kind U16|
|19|Outcomeのコード|
|20–24|予約、すべて0|
|25–40|root ID|
|41–56|operation ID|
|57–64|epoch|
|65–72|fencing token|
|73–80|index|
|81–88|target generation|
|89–120|planまたはreceiptのdigest|
|121–152|直前の256byte frameのSHA-256|
|153–224|予約、すべて0|
|225–256|先頭224byteのSHA-256|

上位bitによるCounter範囲外、未知Outcome、予約領域非零、magic違い、checksum違い、sequence不連続を拒否します。
このハッシュ鎖自体には秘密鍵も署名もなく、悪意ある完全な履歴置換を防ぐものではありません。
kindの意味とreceiptの不変性はPkg_File_Replay、byte列の構造はMC_Log_Formatが担当します。

## ファイル計画

MCPLAN02、header 192byte、shape 128byte、最大1024変更、最大4,500,000byteです。
Pathは相対pathで、virtual FS、秘密・監査・管理状態のrootと子を一般変更から排除します。
Before/Afterにはkind、mode、UID/GID、size、mtime、内容とxattrのdigestがあります。
境界数、canonical path、禁止domain、重複・祖先関係はPkg_File_Planを参照します。
仕様の数値を変更したらこの表、Ada tests、fixture、接続profileを一緒に変更します。

## root.state / CAS / pin

root.stateは192byteの厳格な形式です。root ID、generation、active transaction/plan、accepted plan、package setを保持します。
CASのpathは`objects/<sha256先頭2字>/<残り62字>`、pinは`pins/<transaction ID>`です。
pinの値は正確なplan digestの32byteです。既存pinと一致する再送では、その呼び出しの未公開一時ファイルだけを除去します。
公開結果が不明な場合は一時名も消しません。pinは全blobの保有証明ではないため、別に全参照blobを検査します。

## 診断出力

`pkg_recoveryctl inspect STATE_DIR STORE_DIR PLAN_SHA256` は読み取り専用の`mission-recovery-audit-1`を出します。
exit 0はメタデータの限定検査が通った意味です。実ファイル、全回復blob、認可、停止ラッチ、独立アンカーは検査していません。
`execution_permit=false`を常に出し、失敗はexit 2、使い方違いは64、runtime不適合は78です。
欠落ファイルを作らず、部分末尾の長さとdigest、不正record位置、再生phaseを返します。生payloadや秘密は出しません。
書込み者を停止した原本または一貫したフォレンジックコピーで使用してください。

## 互換性

バイト列の版が同じでも受理する意味が厳しくなることがあります。
今回のreceipt不変条件とphase-aware照合はその例です。旧readerを消す前に旧媒体を読み取り専用で評価します。
旧契約を自動許可するfallbackはありません。状態移行中にcodecを現場で手編集することは禁止します。
