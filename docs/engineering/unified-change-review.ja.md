# Unified-management change review — 実装・文書の整合性点検

独立レビュー承認ではなく、今回の作業で行ったsource/architecture reviewの記録です。
全仕様の形式的同値性・全命令実行結果・全故障復旧を検証したとは主張しません。

|ID|発見/設計上の問題|今回の処置|残る検証|
|---|---|---|---|
|REV-01|receiver台帳の欠落をOpenが新規作成|明示Genesis/provisionとexisting-only読取へ分離|Ada I/O / 実停止試験|
|REV-02|失敗recordのResultを次のBegunへ引継ぐ|E.ResultをOKへ初期化、共通replayコア|Ada回帰/proof|
|REV-03|healing既存Openで予算reset可能|Allow_Provisioning既定False、adminだけTrue|現場移行・I/O試験|
|REV-04|reconcileがeffects.logを作る|Reconcile_Onlyではcreateしない|全legacy adapterの追加棚卸し|
|REV-05|個別workerを統合する実行経路なし|第4repo controlcore、二者plan、WAL、receipt、三者accept|Ada/実worker/権限境界試験|
|REV-06|一部資源だけのrecoveryで親予約を解放|完全同一資源集合、祖先はResolved_By、同一cluster固定|系譜・並列・現場隔離の試験|
|REV-07|管理ログの修復で証拠/判断を失う懸念|exact tailに三役署名、保全後truncate、再Open必須|電源断/fsync障害|
|REV-08|共有profileだけではmanager解釈変更を識別できない|固有implementation profileをpolicyへ追加|移行/鍵失効/旧履歴試験|
|REV-09|版分岐で95canonical Adaと3tests消失|欠落分復元、18同名は現行優先、在庫台帳|復元モデルのcompile/接続|
|REV-10|文書の三repo方針と四repo実装が矛盾|ADR-0002をsuperseded、ADR-0021へ要求移行、build案内更新|人による設計全体レビュー|
|REV-11|多様なSDKが完成済みと誤認される|20capabilityのruntime/SDK/model/未実装を機械台帳化|残backendsを実装・資格化|
|REV-13|GPRで復元したplatformctlがRPMへ未収録|specへ追加、全14application mainを配布定義と照合|rpmbuild未実施|
|REV-12|試験PASSを別sourceへ流用する危険|実行前後hash、new evidence、旧証拠を履歴扱い|CI署名/ビルド依存固定|

## 文書監査の範囲

全repo内Markdown/RSTのfile参照、要求40件、ADR27件、危険26件、故障計画34件、
canonical Adaの字句索引、全GPR test-mainの登録を機械照合します。数値は生成後のreportで再確認。
独立したコードパーサや証明器で全仕様の意味を検証する工程ではありません。
旧版の文書・証拠は履歴として保持し、現行のarchitecture/capability/migration仕様を優先します。

## 未完を隠さない

全RPMDB/host root、全scriptlet、ISO/installer、fencing実装、DB backup/restore、remote fleet、
manager HA、独立antirollback anchor、GCは今回で完成していません。コンパイルの微調整ではありません。
未知状態をOKで埋めるadapterを置かず、実行できない条件をDenied/Indeterminate/Not_Qualifiedとして残します。
