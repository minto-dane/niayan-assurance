# Capsule・認証済み復旧の実装レビュー

本変更は未認定source。対象は独立した原本からの候補再構成、設定・権限の厳密な判定、アプリ世代とruntime/データの分離。live-root復旧と全アプリ実行backendが完成したという意味ではない。

## 実装

新しいSPARK: MC_Recovery_Cohort、Capsule_Types/Policy/Lifecycle/Broker/Mounts/Wire。新しい診断実行口: capsulectlとCtl_Capsule、nia capsule-check。Pythonは非特権のcohort署名/完全inventory/候補再構成、Flatpak request正規化、tree materialization、wire生成。

## レビューで是正した境界

復旧証拠を書けないI/Oエラーを、入力複製の不良として無視しない。input/outputの重複を拒否し、export開始前に完全集合を検査する。ファイル内容だけでなくdir/rootのmode/owner/xattrも正本へ記録して、権限ドリフトを検出する。

PortalのFileChooserを常に単一FDと仮定しない。raw network/audio/driの権限を、それより狭い能力と同じ意味にしない。世代copyのchmodだけで本番のimmutable boundaryが成立したと扱わない。Capsuleの純粋な判定と、実kernelのLSM/seccomp/VM/peer情報の正しさを分離する。

## 統合

7リポジトリの共有契約を固定し、CLI配布、テストmain、要求/危険/ADR/故障台帳、source inventoryを照合する。旧sourceの検査実績を新版の証明として持ち越さない。現行説明は仕様、変更理由はADR-0050/0051、未接続はCapsule integrationとcohort仕様に置く。

## 証拠

Pythonの暗号・file I/O・拒否・中断・有限model試験を実行し、AdaとSPARKは別結果として記録する。OS power loss、live corruption repair、Portal/bwrap/VM/GPUは未実施。自己申告のTrueやfixtureの鍵で製品qualificationを作らない。
