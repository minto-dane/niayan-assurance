# 開発ガイド E-DEV-1

## 開始

四つのrepoを兄弟directoryへ置き、各repoのREADME、GPR、SECURITY.mdを確認します。
通常ビルドは一つのrepoだけで可能です。cross-repository/engineering検査には固定した四つが必要です。
本番資格情報を持たない非特権の作業環境を用い、hostサービスの起動・ネットワーク変更をCIへ混ぜません。

```sh
python3 assurance/ci/engineering.py check
python3 assurance/ci/engineering.py lint
python3 assurance/ci/engineering.py subject
python3 -m unittest discover -s assurance/tests/engineering -v
python3 assurance/ci/run-engineering-checks.py --mode source
```

Ada toolchainのある非特権環境では、次も実施します。

```sh
python3 assurance/ci/run-engineering-checks.py --mode build
python3 assurance/ci/run-engineering-checks.py --mode proof
```

buildはcompile-allとtest-buildの後、test-planのunit/隔離I/O mainを一つずつ実行します。
ホスト読取テストは`--include-host-observers`による明示選択が必要で、未選択の場合はNOT_RUNとして残ります。
全層で成功を求めるリリース検査と、通常の開発source検査を混同しません。
実行ごとに新しいevidenceディレクトリを作り、終了値・時間・log hash・source subject・tool識別を記録します。
source/code inventoryを実行前後に束縛し、更新されていたら失敗します。
本番用の環境変数や資格情報を子プロセスへ渡さず、試験用directoryは独立して生成・削除します。
残すログと生成物には、入力由来の秘密を出さないことを各テストの契約に含めてください。
実行制限は1コマンドの時間と出力量に設定します。バックグラウンドの子も終了させます。
このCI JSONとhash manifestには本番承認の署名はありません。

個別repoでは引き続き`make compile-all`、`make test`、`make flow`、`make prove`を使えます。
`make test`だけで全隔離I/Oテストが実行されたとは扱わず、test-planとの照合を行います。
`assurance/engineering/test-plan.json`に、通常make test以外の隔離I/O試験も含めて全mainを登録します。
現時点の結果はNOT_RUNです。実行後の結果は計画ではなく別のevidenceに残します。

## 変更の単位

障害/要求ID → 脅威と故障への影響 → ADR → 仕様と状態遷移 → 契約とコード → 正常・否定・再中断試験 →
source inventory → 互換性/移行/証明影響 → 独立レビュー、の順に変更します。
ライブラリ追加、enum追加、境界数増加、永続field変更、認可の緩和は「細かな修正」として扱いません。

## 参照と在庫

`requirements.json`のcode/test/spec/ADR参照が壊れるとengineering checkは失敗します。
新しいtest mainをGPRへ追加した場合はtest-planも必要です。
`component-catalog.json`は全canonical Ada src/runtime/appを含む字句索引で、生成後のdiffをレビューします。

```sh
python3 assurance/ci/engineering.py inventory --write
```

## 接続変更

共有ソースを変えたら、`refresh-contract.py --write --acknowledge-interface-change --sync-sibling-vendors`を使用します。
次に`regenerate-public-fixtures.py --public-test-only`を実施します。
この処理は本番の鍵や承認を生成しません。旧状態のreader、保留操作、対応する実binaryを保持する移行審査が必要です。

## レビューの分担

コード作成者だけで、認可・永続形式・fencing・回復・鍵変更を承認しません。
owner役割は`ownership.json`に定義します。実際の担当者への割当は運用側で行い、空欄を承認済みとは扱いません。
PR/ADR/failure reportの様式はtemplatesにあります。秘密情報を添付せず、証拠の保存先とdigestを記します。

## ローカル検査と配布

ソース用checkerはCI管理権限そのものを代替しません。攻撃者がソースとcheckerと署名者を同時に支配する前提では不十分です。
リリースではexact subjectに束縛した別の署名検査を使います。自動的に本番へインストールする入口は設けません。

## controlcoreの追加手順

共有source変更後は、vendor同期→管理器profile更新→両方のfixture再生成→在庫再生成の順です。

```sh
python3 assurance/ci/refresh-contract.py --write --acknowledge-interface-change --sync-sibling-vendors
python3 controlcore/ci/manager-profile.py --write --acknowledge-interface-change
python3 assurance/ci/regenerate-public-fixtures.py --public-test-only
python3 controlcore/ci/generate-test-fixtures.py --public-test-only
python3 assurance/ci/engineering.py inventory --write
python3 assurance/ci/unified-audit.py
```

新profileを生成しても、本番鍵の再承認・reader移行・未解決操作の管理は別です。
実行証跡はsource hashを確定してから採ります。profileや文書を変更したら再試験します。

## 依存する開発用profileの更新

変更した共有sourceはresolverとmanagerの実装profile、およびそれに結び付く人工test fixtureを失効させる。これらを個別に更新する場合も、shared→resolver/vendor→manager→人工fixture→inventory→全checkの順を守る。

非特権の隔離checkoutで、まず次を使って固定された手順だけを表示する。

```sh
python3 assurance/ci/rebind-development.py
```

独立レビューを別に進めたうえで、開発用の再生成が必要な場合は明示的に実行する。

```sh
python3 assurance/ci/rebind-development.py --write \
  --acknowledge-incompatible-change --public-test-only
```

これは公開された人工鍵を使うtest fixtureだけを再生成する。productionの鍵・証拠・認可は生成しない。全手順と変更前後source subjectをevidenceへ記録する。途中失敗したcheckoutを正常とせず停止し、人間の変更を自動rollbackしない。再生成が成功しても、意味互換性や形式証明が成立したことにはならない。
