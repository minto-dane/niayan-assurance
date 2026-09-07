> **Nia OS 製品境界**: この文書の旧Leap/SLES/native RPMDB前提は履歴です。現行製品は [Nia構成](../../../../distribution/docs/architecture.ja.md) と [所有権](../../../../distribution/docs/ownership-and-effects.ja.md) を参照。既存部品の安全条件は無効化しません。

<!-- Current base/repository count: superseded by solver-assurance.ja.md and ADR-0035/0036. -->
現行baseはLeap16.0のみ、6runtime repo。base/構成数は[現行統合仕様](solver-assurance.ja.md)を優先。以下の未完実装境界は維持する。

# 継続開発計画 — 境界を埋める順序

## P0: まず現在の実装を検証する

四repoの全sourceコンパイル、登録されたすべてのAda test、SPARK flow/proofを実行し、未証明/境界注釈を解消します。
最初の実機対象を一つのkernel/FS/native library/toolchain profileに限定し、file engineの電源断・再中断・ENOSPC/EIOを試験します。
成果物は、正確なsubject、工具version、義務一覧、失敗ケースと修正、全再試験です。

## P1: 読み取りと停止・認可を実環境へ接続する

実際のinventory/observerが出す署名の意味、systemd/Pacemakerの所有権、物理fencingとストレージ側token強制を試験します。
SDKのコールバックを仮のOKで埋めません。誤った対象への作用がないこと、結果不明で二重実行しないことを確認します。
ローカルの署名付き統一管理はcontrolcoreへ実装しました。
遠隔フリート配送、独立アンカー、鍵更新、OOB復旧と資格化はここで完成させます。

## P2: ディストリビューションの全面管理

RPMDBの所有権移行、全依存/trigger/scriptlet、SELinux/ACL/特殊属性、boot chain、initramfs、署名、installer/ISOを実装します。
今ある独立rootの仕組みをそのまま`/`へ向けて済ませないでください。
最小の対応package setを選び、対応契約を増やし、未対応packageは拒否する方針を維持します。

## P3: 長期運用と災害復旧

実バックアップの取得・削除・復元、鍵復旧、token世代の非巻戻し、長期容量、GC、監査保存、複数拠点、復旧訓練を扱います。
RTO/RPOと想定する複合故障を測定します。台数や状態機械の数を、可用性の証拠としません。

## 完了の定義

コードがあるだけでは完了しません。要求、ADR、仕様、正/否定/障害試験、証明またはTCB根拠、運用接続、
移行/rollback、監視、独立レビュー、対象環境の証跡が同じリリースsubjectに揃った機能だけを適格化します。
この計画の未完部分を、コンパイル上の微調整として扱わないでください。

## 統一管理の残り

管理器HA選出・remote transport・全volume antirollback・signed checkpoint移行・容量GCは未接続です。
128保持workflow/65,536管理recordの上限を、自動削除や新規logで回避してはいけません。
CAP台帳を参照し、runtime/SDK/model/not-implementedを混同しないでください。
