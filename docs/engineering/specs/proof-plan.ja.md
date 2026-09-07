# 仕様 E-PROOF-1: 証明義務とTCB

## ファイル取引の純粋コア

Pkg_File_Replay.Valid(B,V)を状態不変条件とし、ConsumeのPostは、失敗ならV不変、成功ならValidを要求します。
加えて独立に確認すべき性質は、sequenceの単調増加、同一binding、terminalの吸収性、receiptの不変性、
Forwardのdone prefix/untouched suffix、Reverseのdone suffix、counter境界です。
Image_Allowedは「unknown画像を拒否」「done領域と画像が一致」「未intentの未来領域はbefore」を満たす必要があります。

## 実装とモデルの対応

codecがdecodeしたframeの正確な意味 → Replay.Consume → Engine.Read_Log → Inspect → Materialize/Commit/Restoreの順に追います。
Codecだけ証明してruntimeの順序を無条件に信用しません。FFIは明示した事前/事後/失敗/不明条件に分解します。
Pure coreの合成的証明と、永続化順序のモデル、対象I/O試験が別々に必要です。

## TCB

Ada compiler/runtime、GNATprove/SMTの前提、Linux kernel、glibc ABI、FSと装置の永続化、
libsodium/libarchive/libcurl/libxml2、固定commandの動的依存、実observer、署名鍵管理、etcd/Pacemakerを含みます。
SPARK_Mode Off、Import、Unchecked_Deallocation、assume/検査抑制をinventoryとレビューで追跡します。
この版に検証済みコンパイラの保証はありません。HOL4/CakeMLで実装したとは主張しません。

## 禁止される証明の取り繕い

失敗した証明をpragma Assumeで置換、難しい処理を無記録でOffへ移動、assertionを無効化、
resultを握り潰す、全エラーを再試行可能へ変換、といった変更を認めません。
False_Positive等の注釈にも、理由・具体的な義務・レビュアー・対象subjectを必要とします。

## 実行

各repoの`make flow`と`make prove`は未証明やツール不在を成功扱いしません。
証明を実施しても、実行していないruntimeや、指定していない性質の証拠へ拡大解釈しません。
[SPARKの前提管理の一次資料](../sources.ja.md)を参照してください。


## 容量・管理状態の追加証明義務

`MC_Journal_Budget.Fits(Used, Limit, Pending, Added)`は範囲検査を短絡評価し、
減算が常に定義され、成功時に `Used + Pending + Added <= Limit` が数学的整数上で
成立することを証明する。式の右辺を機械整数で再加算して証明のためにoverflowを作らない。
これはレコード数の論理保証であり、空きブロック・inode・fsync成功を証明しない。

`Ctl_Workflow.Completion_Reserve`は各live planの未確定操作とcloseに必要な予約を合計する。
計画受け入れ後、および各状態遷移後に、すでに受け入れた予約を新規計画が消費しないことを
検査する。結果不明の同一再観測は記録数を増やさず、新しい結果・証拠・状態変化は通常の記録を要求する。
有限の余力で無制限の再試行や媒体障害を許容するという主張はしない。

## 外部処理・観測の境界

`MC_Command`と`MC_FS`と`MC_Store`はSPARK外の実I/O境界である。
PID保持、pidfdによる終了観測、reap前のgroup cleanup、descriptorの非衝突、期限・出力量、
ctimeとFD/path照合、返す内容のhash、欠落状態を作らないOpenは、対応するLinux API条件で試験する。
メタデータ照合は敵対的rootやstorageの虚偽応答に対する完全性証明ではない。排他writer、
信頼したkernel/runtime、対象mount、強制アクセス制御という前提を残す。

`Pkg_Managed_Engine`の合成順は停止・構成・解決の検査を重ね、現在の認可を再確認する。
各generic callbackの意味と、すべての副作用がこの経路を通ることは別に証明・統合試験する。
コールバックが成功を返すだけの実装を置いて、本体の保証へ算入しない。旧workerの存在は
自動的にこの保証範囲へ含まれない。共有profileとsolver/manager profileの再固定は証明の代用ではない。

## 独立した復旧形式の前提

元の状態を開くことと新規初期化を分ける。`MC_Store.Initialize`の事前条件は空の私有領域であり、
`Open`は欠落したlock/objects/incoming/pinsを生成しない。部分初期化は正常状態へ昇格せず、
復旧手順に従って保全・照合する。形式の互換性、完全性、外部の信頼下限、物理永続化は独立した条件である。
