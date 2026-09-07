# 認証済みcohortからの復旧

## 保証の単位

cohortは、同じ時点のcatalog、checkpoint、journal、未確定要求集合、関連する管理ファイルと監査historyの正確な集合。path、内容hash、chunk hash、mode、uid/gid、xattrを署名付きmanifestで拘束する。directoryとrootも属性を記録する。完全な読み取り対象集合を定め、欠落を正常な空状態にしない。未列挙ファイル・空directory・改変属性も検査する。

根本の信頼は、壊れたディスクから自己発見するものではない。独立した回復チャネルで取得した、正確な受入anchor digest、現在のtrust epoch、generation下限、鍵・失効情報を使う。複数のlocalコピーの多数決で正しい世代を決めない。古い有効署名、同一鍵の別名、同じ承認ドメイン、期限切れ、未知の鍵を拒否する。

## 回復の境界

- 配布ファイル・core: 認証済み原本からbyte単位で再構成できる。動的データや生成効果は別契約。
- catalog/checkpoint/history: 独立anchorで確定した完全な原本から復元する。ファイル一覧やmtimeから履歴を捏造しない。全コピーが失われたhistoryは検出するが生成しない。
- 未確定外部操作: 正確な要求集合を保ち、復旧後に再照合する。履歴の欠落から未実行と推定しない。
- 秘密鍵・信頼下限・業務DB: 本generic復旧の対象外。別の鍵回復、単調信頼記録、DB固有復元を使う。

coreの改変が疑われる場合、同じ壊れたcoreの「正常」報告を信頼しない。署名済みの独立rescue、別の検査・鍵チャネル、媒体の保全を必要とする。kernel/root権限や全検査器・全原本・全鍵が同時に侵害/喪失した場合まで、自己修復で完全性を保証しない。

## 状態遷移

Quarantined → Reconstructing → Candidate_Checked → Reconciliation_Only → Operational。入力が正しいこと、writer静止、容量、証拠保全を確認し、操作の前に状態と試行予算を永続化する。候補のbyte一致だけでOperationalへ移さない。

`MC_Recovery_Cohort`はこの遷移とquorum条件のSPARK実装。証拠を取得・認証し、遷移を永続化して実操作へ接続するexecutorは別。応答不明のlive操作を再送しない。既存のNia停止条件、信頼下限、ログ予算、監査規約を迂回しない。

## 実工具

`assurance/tools/nia_recovery.py`は非特権の検査と、新しい私有candidateへの再構成。verifyは複製の完全性、inspectは明示した元領域の完全inventory、reconstructはchunkごとの正しい複製を選んでcopyする。複数の壊れた複製でも必要chunkが残っていれば混ぜて復元できるが、全コピーに同じchunkがなければ完了markerを作らない。

不正chunkは限定予算で証拠領域へ保存する。証拠出力のI/O失敗を入力複製の不良として握りつぶさない。正常な元データは変更しない。途中candidateを再利用・自動削除しない。partially-written markerは通常の完全な記録検査を通過しない。

復旧payloadは0600の作業ファイルで、署名された元のuid/gid/mode/xattrはmanifestに保持する。特権属性の適用はnative validatorと最終executorが担当する。symlink・device・任意の全host treeはこのcohortファイル形式では扱わない。今回のraw復旧対象は完全に列挙できる通常ファイル集合。元カタログ内のリンク意味などはnative層で別に検証する。

## 自動化の限界

本工具の自動性は、正確な原本探索・破損検出・候補再構成にある。live `/`の自動置換、独立rescueの起動、native journal replay、業務データの自動復元を完成したものではない。全workerへの強制接続も未完。目標は足りない根拠を推測で埋めず、安全に復帰できる条件を機械的に確認すること。
