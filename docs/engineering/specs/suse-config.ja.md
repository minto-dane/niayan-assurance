> **Nia OS 製品境界**: この文書の旧Leap/SLES/native RPMDB前提は履歴です。現行製品は [Nia構成](../../../../distribution/docs/architecture.ja.md) と [所有権](../../../../distribution/docs/ownership-and-effects.ja.md) を参照。既存部品の安全条件は無効化しません。

<!-- Current base/repository count: superseded by solver-assurance.ja.md and ADR-0035/0036. -->
現行baseはLeap16.0のみ、6runtime repo。base/構成数は[現行統合仕様](solver-assurance.ja.md)を優先。以下の未完実装境界は維持する。

# SUSE16基盤・設定互換性の統合仕様

版: suse-config-integrity-2026-09-06。独立した承認・本番認定は未取得。
現在の構成は assurance/pkgcore/statecore/controlcore/configcore の5コードベースとdistribution組立て束。
以前の4repo/Fedora説明は履歴であり、新しい基盤の導入手順として使わない。

[Config設計](../../../../configcore/docs/architecture.ja.md)、
[構文仕様](../../../../configcore/docs/schemas-v1.md)、
[receiptと実行器](../../../../configcore/docs/integration.ja.md)、
[NVIDIA](../../../../configcore/docs/nvidia.ja.md)、
[SUSE選定](../../../../distribution/history/leap16/docs/base-selection.ja.md)、
[組立て](../../../../distribution/history/leap16/docs/assembly.ja.md)。

## 不変条件

未確認をAbsentやYesとして補完しない。管理者意図を旧既定値と区別する。
対象パッケージの意味に対するschema/validatorを固定し、廃止キーや条件不成立を拒否する。
すべての入力経路と生成・実行依存を含まない検査は完全とは表示しない。
新しい設定への意味検査と、過去の復旧像への現在時点の互換性検査を分離する。
独立したwriterを増やさず、Pkg_File_Engineへ接続する。既存RPMDBはnative zypper所有のまま。

## 範囲

汎用処理のあることと、すべてのパッケージにnative adapterがあることは別。
今回NVIDIAのexact能力判定、限定modprobe構文、直接ディレクトリ観測を追加。
OpenSSH/systemd/NetworkManager/DB等には汎用schema/graphを利用できるが、全native文法・
隔離validator・initramfs・稼働観測の全接続ができたとは主張しない。

## 状態・復旧

[設定ライフサイクル](../../../../configcore/docs/recovery.ja.md)はpureな判断。
実executorは前後像、WAL、単一writer予約、設定receipt、受信台帳を合成する。
証明書が失効した時や観測が不明な時に、正常な既存業務を勝手に停止させず、新しい変更を拒否する。
書込み所有権やデータに危険がある場合は別の停止・隔離プロトコルが責任を持つ。

## 実行入口

`configctl`は読取り専用。`missionctl config-check`は固定toolへの入口。
新しいPkg_Configuration_Engineはopt-in SDKで、既存ワーカーの全面移行は未接続。
実build工具distroctlはsigned snapshotsを検査しKIWI記述を生成するが、ISO・署名boot・インストールをしない。

[実装段階と残作業](capability-matrix.ja.md)と
[配布受入条件](../../../../distribution/history/leap16/docs/qualification.ja.md)を、機能名だけで置き換えない。
