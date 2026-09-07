# この版の変更レビューと残るリスク

状態: 独立レビュー待ち。ベース: distro-foundation-source-2026-09-06。

|観測した経路|変更|残る前提|
|---|---|---|
|Resumeが既定の作成付きOpenを呼ぶ|既存のみを開き、欠落をCorruptにする|親directory、CAS、独立世代の運用保護|
|ログの再生判定が実I/Oエンジン内に混在|Pkg_File_Replayへ純粋な規則を分離、診断と共用|SPARK証明とAda実行未実施|
|実像のBefore/After所属だけで継続判断|完了prefix・未着手領域・逆順suffix・終端を区別|writer排他、reader停止、他のrootは保証外|
|確定/復旧の再開時に別receiptへ変え得る|一度記録したreceiptを固定、現在の再認可と分離|認可アダプターの正しい意味付け|
|復旧の最後が個別照合だけ|全Beforeを再照合してからRestored|外部writerを許可しない|
|終端再照合の根拠が暗黙|Package_Setと記録済みreceiptを現在のGuardへ渡す|古いreceiptだけで現在の権限としない|
|同一pinの再送で未公開一時物が残る|確定したEEXISTと同一pinを確認して自分の一時名だけ削除|結果不明や不一致pinは保持|
|metadata読取が変更を見逃す|前後のfd属性を照合し変化はConflict|ABAや悪意のあるrootは除外|
|既知のspecialをread/writeで開き得る|開く前のStatと開いた後のfstatで検査|検査の間の競合を許さないprivate parent|
|保護pathの配下だけを拒否|管理・監査・秘密ディレクトリそのものも拒否|環境固有の追加path方針が必要|
|通常make testに全mainがない|33 mainを独立の実行台帳へ登録し引数も検査|実行環境の選択/資格情報の隔離|

診断CLIは自動修復の代わりではありません。観測を保存し、許可された復旧器へ渡すための非変更入口です。
新しいledgerやOS-wide ACIDを同時に導入せず、既存形式の意味を厳しくしました。旧媒体/方針の移行は明示レビューが必要です。
