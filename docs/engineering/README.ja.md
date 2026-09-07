# 復旧・開発保証ハンドブック

対象はこのZIP内のソースです。設計の採用と、実装の存在と、実行試験と、形式証明と、本番適格化を区別します。
本ハンドブックを置いたことによって、既存のSDKが完成した運用システムに変わることはありません。

## 現行の製品

Nia OS、固定Debian 14 Forky/DEB供給、Nia catalog、XFS永続領域。6コードベースとdistributionから構成する。製品の正本はdistribution/profilesとcontractsで、コードに未接続の仕様は実装gapとして管理する。

[実行境界](specs/execution-safety.ja.md) / [最終レビュー](final-review.ja.md) / [本番接続条件](specs/production-closure.ja.md)。

## 読む順序

1. [保証範囲と構造](specs/architecture.ja.md) と [故障モデル](specs/failure-model.ja.md)
2. [復旧プロトコル](specs/recovery-protocol.ja.md) と [ACIDの境界](specs/acid-contract.ja.md)
3. [永続形式](specs/storage-formats.ja.md) と [接続契約](specs/connector-contracts.ja.md)
4. [セキュリティ](specs/security.ja.md)、[検証計画](specs/verification.ja.md)、[形式証明](specs/proof-plan.ja.md)
5. [開発手順](specs/development.ja.md)、[更新・移行](specs/release-migration.ja.md)、[優先順位](specs/continuation.ja.md)
6. [ADR一覧](adr/README.ja.md)、[運用手順一覧](runbooks/README.ja.md)、[API索引](api-index.ja.md)

## 正本と生成物

`assurance/engineering/requirements.json` が要求ID・コード・試験・ADRの正本です。
`hazards.json` と `fault-cases.json` は故障時の条件と未実施試験の正本です。
`test-plan.json` は全GPRテストmainの起動分類です。`component-catalog.json` とAPI索引はソース由来の字句索引です。
**索引に載ることは、その機能の意味が完全に形式化された証拠ではありません。**

相矛盾した旧版の追記文書より、このハンドブックの保証制限を優先します。
動作の最終的な実態はソースと検証結果で確認し、仕様との差異は欠陥として記録します。
ADRは全件、独立レビューを待つ状態で登録しています。架空のレビュー担当者・承認は記録しません。

## 誤解してはいけないこと

`SPARK_Mode`、契約、ハッシュ、署名、正常終了、参照モデルPASSは別物です。
署名は主体とバイト列を結び、観測内容の物理的な真実を保証しません。
現状のコンパイル・Ada実行・GNATprove・実電源断・物理fencingは未実施です。
`engineering.py check` は参照・在庫・開発規則を検査するもので、本番承認を発行しません。

## 統一管理の入口

[統一管理仕様](specs/unified-management.ja.md)、[機能台帳](specs/capability-matrix.ja.md)、[API索引](api-index.ja.md)を用いる。`unified-audit.py`は全repo文書のfile参照とlineage/capabilityを検査する。全仕様と実装の意味的同値性証明ではない。設計の理由・置換関係はADR、過去の検査結果はhistory領域に保持する。
