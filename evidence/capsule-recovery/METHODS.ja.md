# 検査方法と結果の解釈

`current/report.json`が今回の最終source検査。実行前後のsource subject一致、ログハッシュ、終了値を記録。7群合計486の固有Python試験のうち、非特権で485成功・root用1件skip。root拒否用の1件は`root-refusal.log`で別途成功を確認した。反復や有限組合せの数を別test件数へ加算しない。

新規cohort50件は、人工Ed25519鍵とanchor、実際の通常ファイル、欠損・複製破損・属性・FIFO/link拒否・容量・I/Oエラーを使う。原本は人工cohortで、実際の全Nia journalを復元した試験ではない。fault注入は操作位置で例外を発生させるもので、装置の電源断や永続化保証の実機試験ではない。

Capsule53件は、未認証入力の要求化、能力の積集合・拒否条件、診断wire、実copyと再hash/readonly mode、source保全、制限違反・中断を扱う。bwrap/AppArmor/seccomp/Portal/VM/Steamを起動する試験ではない。Pythonの有限モデルをAdaの機能的正しさの証明に使わない。

`build-attempt/`と`proof-attempt/`は環境にツールがないことを記録した試行。source subjectは試行時点のもので、現在のAdaをコンパイル・証明した記録ではない。最後のGPR source-dir整理の前に実施している。`toolchain-probe.log`にはgccの実呼出しとHTTPS取得の失敗を残す。

既存7repoの動的binary契約試験は`assurance/ci/cross-repository.sh`へ拡張したが未実行。ソースlockや資料の参照が一致することは、意味的な完全性・本番認定ではない。
