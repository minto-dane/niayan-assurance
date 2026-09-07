# 同意経路のレビュー記録

## レビューで修正した設計・コード
- UIだけの操作と、同意UI内で資源が発生するnative portalを別遷移にし、後者はPortal_Pendingを先に保存。
- 失効をRevocation_Ready/Revoke_Pending/Closedへ分離し、結果不明の撤回を繰り返さない。
- requestの固定質問hash、UI owner、resource、本人・世代・期限を反映前後で照合。
- 新しいgrantだけで履歴を使い切らないよう、ticketごとの終端予約を保持。
- 欠落台帳・古いanchor・部分末尾を自動的に新規状態へ変換しない。
- SCM_RIGHTS/SCM_PIDFDを拒否する際、受信済みFDを閉じる。callerのUser_Confirmedをwireに置かない。

## 確認の限界
Pythonの状態モデルは独立した単純化モデルであり、Adaとの同値性証明ではない。private D-Bus試験は実libsystemdと偽UI peerを使い、Ada FFI本体や実GTK/KDE UIは実行していない。通常runではfake peerを起動せず、専用private busの試験だけで使う。

## 製品完成性
Niaはまだ未完成。Capsuleの同意接続だけで独立rescue、全DEB効果、full root writer、boot/installer、remote management HA、physical fencing、DB復元、安全な長期GCが完成するわけではない。既存のproduction-closure仕様とrootのAGENTS.mdで実装優先順位を示す。受入証拠のない対象へ運用許可を出さない。

## レビュー修正
既存MC_Logは正常なprefixと部分tailを分けて読み取れるため、同意storeではOpen/Check_AnchorにHas_Torn_Tailの明示拒否を追加した。拒否は証拠の自動切り詰めではない。隔離I/OのAda試験に、欠落、新規要求の重複、anchor応答喪失、anchorの古さ、snapshot欠落、部分tailを登録した。Ada実行は未実施であり試験コードの存在をPASSにしない。

配布のgateを追加した段階で中央の固定集合と不一致を検査が発見した。required_gatesとnia_policyの集合を同期し、削除・自己申告PASS・重複・異なるsource対象を拒否する回帰試験を追加した。
