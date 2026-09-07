# RUN-SOLVE: 解決検査の拒否・結果不明

1. 新しい変更だけを停止し、既に正常なサービスへ不要な停止/再起動をしない。
2. 原データの署名情報、snapshot/boot/generation、Uのhash、候補、proof、tool profile、
   拒否codeと燃料/資源制限を保全する。秘密情報を証拠bundleへ含めない。
3. Invalid_Input/Unsupported/Exhausted/IO_Error/IndeterminateをUNSATへ読み替えない。
4. Missing metadata/observer/source coverageは管理者が確認する。条件削除、--nodeps、
   signature/TLS/SELinux/停止gate無効化を回避策にしない。
5. libsolv problemsを調べても自動的にsuggested relaxationを適用しない。
6. SAT候補が拒否されたら、exact同一入力に対し別の候補を非特権で提案できるが、
   試行回数/時間を制限し、候補探索ループが管理業務を圧迫しないようにする。
7. UNSAT確認ではUからCNFを再生成し、証明列全体の検査完了を確認する。
   未対応extension proofなら対応した別checkerを審査するか結果未確定のまま保留。
8. 現在のboot/設定/期限/方針/予約が変わった場合は、古いvalid reportを流用しない。
9. 復旧は新しい逆計画で認可し、業務データ/鍵の巻き戻しは別の契約で扱う。

本手順は本番資格化済みの復旧commandではない。現在のnative observer/worker接続と
実機試験の欠落を記録し、診断成功のみで実行を許可しない。
