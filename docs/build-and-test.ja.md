# ビルドと試験 — unified-management版

現行の詳細手順は[開発ガイド](engineering/specs/development.ja.md)、[controlcore試験](../../controlcore/docs/verification.ja.md)。
4repoを兄弟checkoutに置く統合検査と、各repoの独立buildを区別します。

```sh
python3 assurance/ci/engineering.py check
python3 assurance/ci/unified-audit.py
python3 assurance/ci/run-engineering-checks.py --mode source
```

非特権の隔離環境でGNAT/GPRbuild/GNATproveを用意した後、build/proof modeを実施します。
個別repoはmake compile-all/build/test/flow/prove。全Ada test-mainの引数・隔離I/O実行はtest-plan.jsonが正本です。
assurance/ci/cross-repository.shは4binaryのnative契約を比較し、controlcoreの固有契約は同repoのvector testで確認します。

requests.logをmkdir/touchだけで用意する旧手順は使えません。[明示初期化](../../controlcore/docs/operations.ja.md)を参照。
proof targetは未証明やツール不在を成功扱いしません。既存evidenceの件数は旧版の履歴であり、新版の試験成功ではありません。
Ada実行、RPM build、サービス起動、NetworkManager、実クラスタ、Secure Boot、電源断はこの配布では未実施です。
