> 現行の統合範囲・初期化・互換変更は [統一管理仕様](engineering/specs/unified-management.ja.md) を参照。以下の個別SDKの記述は、全接続・全試験の完成を意味しません。

# 今回の互換性と移行

新しいshared unitsとrelease enumの追加によりruntime source profileが変わります。既存の認可方針・control-state・checkpoint・policyを、旧profileのまま新バイナリへ暗黙に受け入れる処理はありません。

4リポジトリは同時に新しい固定コピーへ更新して再ビルド・接続試験を行います。共有コードだけを各サイトで少しずつ編集する構成を避けます。旧バイナリ、元policy、失効情報、回復情報を保存し、署名権限者が影響とstate schemaを確認した移行として受け入れます。

fixtureは新しいprofileに合わせて再生成した人工データです。既存の本番鍵や認可を自動再署名するスクリプトは付けません。古いevidence履歴は新sourceの合格証拠へ転用しません。

新しいhost/network/boot/cohortのAPIは既存の全workerに自動的に挿入されていません。導入前に呼出し側の接続点と、迂回経路がないことを確認してください。未接続のチェックを「有効」と表示しないでください。

新規RPM specは付属工具の配布用です。インストール時にサービス起動、ユーザー作成、秘密鍵登録、Secure Boot設定、ネットワーク設定、ネイティブrpmdb移行を行いません。必要なidentity/LSM/Polkit/永続領域は、別の監査対象のprovisioning手順で用意してください。

## ロック更新用のbuild-time工具

`python3 ci/refresh-contract.py` は候補profileを計算するだけです。差があれば非零終了します。
更新は `--write --acknowledge-interface-change` が必須です。さらに `--sync-sibling-vendors` を付けると、隣接するpkgcore/statecoreの固定コピーを更新します。
これはビルド補助PythonでありSPARKのruntimeではありません。信頼した非特権の作業コピーで実行します。署名、証拠の承認、fixtureの自動本番登録は行いません。
複数ファイルの更新途中に停止した場合、契約検査の不一致を解消するまでビルド・配備してはいけません。更新後は人工fixtureの再生成と独立ビルド接続試験が必要です。

人工fixtureの再生成は `python3 ci/regenerate-public-fixtures.py --public-test-only` です。固定の公開テスト用鍵から作り、秘密鍵や本番報告を入力する機能はありません。この工具は試験用の署名しか作らず、実際の承認や本番移行の代わりにはなりません。テスト鍵は誰でも再生成可能で、本番へ登録禁止です。
