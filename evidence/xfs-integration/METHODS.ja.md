# 検査方法と保証境界

このディレクトリだけがXFSストレージ版の新しい検査結果である。別ディレクトリの結果は、その結果に記載されたソースについての履歴であり、本版の証明として転用しない。

Python試験は、実装したPythonの製品入力・mount読取・暗号工具、人工fixture、制御フロー、有限参照モデル、ソース/文書検査の組み合わせである。全356件をAda実行、形式証明、実XFS修復、実ディストリビューション起動の成功とは呼ばない。非特権で355件を実行し、root専用の拒否試験1件は別のプロセスで確認する。再実行は件数に加算しない。

`test_nia_xfs.py`は51件。実際の`/proc`読取以外では合成された事実を使う。合成事実は認証済み観測ではなく、返り値は常にexecution_permit=false。`run_xfs_health_tests.adb`はSPARK遷移に対する実行待ちのAda試験で、Python試験をその代用にしない。

source/build/proofランナーの実行ログ、source subject、ツール識別を保存する。gprbuild/gnatproveがないときはNOT_RUN。service定義の検査はオフラインの構文であり、実行ファイルのダミーを構文検査に用いた場合もnativeコードを実行したと表示しない。

対象環境はLinux 6.18.35/コンテナであり、kernel7/XFS実マウントはない。format/mount/repair、systemdサービス起動、healthmon ioctl、ディスク故障注入は一切実行していない。旧xfsprogsを最新版と見なさず、supply観測とruntime qualificationを分離する。

新規のkernel/XFS工具をそのまま信頼するのではなく、通常・rescueの正確な成果物、能力、feature bits、監視範囲、末尾破損、容量、電源断、IOエラー、クラスタ所有権を別の実機試験で認定する。仕様の存在や署名された自己申告は合格証拠ではない。
