# 本ラウンドの証拠範囲

対象はsummary.jsonのsource_subjectで固定する。current/のsource/build/proofの実行前後のsourceが一致する。
source modeでは全383試験のうち382件が非特権で成功し、root拒否1件はskipされた。同じ1件を別のrootコンテキストで実行して成功した。
再実行、同じ試験内の128比較、fixture生成、表の照合件数を固有試験数へ加算しない。

追加のtest_final_runtime.pyは21件: 実プロセス／Linux API 9、source照合9、有限予算モデル3。
実プロセスは当該試験が生成した短時間の無害な子のみ。サービス、既存PID、ネットワークや実ディスクを変更しない。
rebind工具の6件は計画・順序・確認の開発用検査。これは人工的な公開試験鍵の再生成であり、本番署名の生成ではない。

Adaでは3つのmain（論理予算、FS観測、command lifecycle）を追加し、既存のCAS/lock/管理器試験を拡張した。
いずれも未実行。PythonのAPI試験はAda FFIコードそのものの試験ではない。

GNAT/SPARKの無償の公式導入経路を確認し、実gccによるAda frontend呼出し、local cache照会、Debian/GitHubのHTTPS取得を試行した。
gnat1がなく、取得はDNSまたはdownload toolの失敗、導入はできなかった。TLS/認証を迂回しない。
全6 repoのmake compile-all/flowは前提ツール不足で停止し、build/proof runnerはNOT_RUNを保存した。
実機boot、XFS scrub/repair、停電、cluster partition、DB restore、GPUは未実行。

初回に共有source更新に伴うprofile/fixture不一致を検出し、条件を緩めず正しい依存順の再固定工具で修正した。
attempts/には失敗と中間成功をそのまま保持する。現行の成功はcurrent/だけである。
記録のcwdや元ディレクトリは実行時の値を改変していない。移動先はattempt-index.jsonで対応させる。

受入の上限はsource検査層。署名、hash、プロセス終了、形式モデル、実業務の正しさを相互に代用しない。
