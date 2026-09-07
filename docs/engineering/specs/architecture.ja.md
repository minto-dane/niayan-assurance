<!-- Current base/repository count: superseded by solver-assurance.ja.md and ADR-0035/0036. -->
現行baseはLeap16.0のみ、6runtime repo。base/構成数は[現行統合仕様](solver-assurance.ja.md)を優先。以下の未完実装境界は維持する。

# 設計仕様 E-ARCH-1: 所有権と保証境界

## 目的と非目的

目的は、既存Linuxの上で、変更・障害・回復の状態を矛盾なく管理することです。
全OSをACIDトランザクションにすること、任意のroot操作を無害化すること、任意の障害から無停止で復旧することは主張しません。
現段階の製品境界は独立管理ルート、限定したパッケージ意味、明示的に接続するサービス・クラスタSDKです。
ホスト`/`、native RPMDBの所有権引継ぎ、すべてのscriptlet、ISO/インストーラーは未完成です。

## 四つの独立リポジトリ

|リポジトリ|正本となる状態|他者から受け取るもの|所有しないもの|
|---|---|---|---|
|pkgcore|受入済みファイル計画、管理ルート世代、変更・復旧履歴|認可、停止確認、健全性・データ互換性の根拠|業務DB、fencing、systemdの実プロセス状態|
|statecore|サービス操作意図、復旧予算、更新予約と配布進行|独立した観測、認可、etcd応答|etcd合意の実装、物理電源、業務データの真実|
|assurance|型・形式・認可規則・固定契約、開発証跡の構造|正確な署名済みバイト列、ローカル方針|万能root実行、外部主体の無条件な信用|
|controlcore|workflow intent、予約、receipt、受入れ、復旧系譜|二者plan、fresh native要求、三者closure|native stateの正本、物理fencing、業務DB|

systemdはプロセス・資源を実行し、Pacemakerはクラスタ上の実行場所を決定します。
同じサービスに独立した複数の再起動決定者を置きません。systemdの起動成功と業務の正常性は別です。
ファイルの正本とRPMDBの正本を二重に作りません。現行の独立管理ルートを超える移行には新ADRが必要です。

## 変更の経路

取得・解析・計画 → 認可と停止条件 → write-ahead intent → 限定した副作用 → 実状態照合 → 完了記録 → 受入状態の公開。
復旧は独立した方向・認可・互換性根拠を持ちます。結果不明を成功や失敗へ勝手に変換しません。
新しいPkg_File_Replayは永続履歴の意味を検査する純粋コアで、既存Pkg_File_Engineと診断器から共有します。
Pkg_Recovery_Auditは読み取り専用です。ここからApply/Restoreを直接呼ぶ経路はありません。

## 信頼境界

入力バイト列と解析した意味の対応、署名鍵の役割、root/node/boot/operation/plan/epoch/fenceの一致を検査します。
特権I/OはSPARK_Mode Offの境界です。Linux、ABI、ファイルシステム、ディスク、ネイティブライブラリ、実観測器を前提として列挙します。
既存の汎用コールバックに`Status := OK`だけを返す実装を入れて境界を埋めることは禁止します。

## 独立性

各リポジトリはvendorに固定した共有ソースと自分のGPRでビルドします。
四者の統合検証だけが兄弟checkoutを要求します。外部の最新版を自動取得して共有型を変更しません。
この版はrecovery-engineering入力を基準に、別枝で欠落した95canonical Adaと3testsを在庫付きで統合しました。
同名は現行を優先し、復元を実接続や資格化の完了と扱いません。詳細は[統一管理仕様](unified-management.ja.md)。
