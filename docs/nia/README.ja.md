# Nia OS の現行製品設計への入口

Nia OS の供給元は **Debian 14 Forky / DEB**。管理権威はNiaである。既存管理器のDB互換・引継ぎは不要という設計変更を反映した。

現行仕様は、リポジトリの`distribution/docs/architecture.ja.md`、`distribution/docs/base-decision.ja.md`、`distribution/docs/ownership-and-effects.ja.md`、`distribution/docs/storage-boot.ja.md`、`distribution/docs/build-release.ja.md`。

既存の`engineering/specs/`、各componentのdocsはAPI・既存状態機械・過去の研究を含む。Niaの製品適用範囲は現行仕様・最新ADR・`distribution/contracts/implementation-map.json`を正とする。旧RPM/SUSEのサンプルを現行Niaのデプロイ手順として実行しない。

コードと仕様が未接続の箇所を、優先順位だけで解消済みにしない。現行ソースはホスト全体の完成ディストリビューションではなく、起動イメージも含まない。
