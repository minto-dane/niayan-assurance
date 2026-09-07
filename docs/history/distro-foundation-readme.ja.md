# 履歴資料: 入力版README

現行版の合格・実行証跡ではありません。

# Mission Core — ディストリビューション基盤強化版

Edition: `distro-foundation-source-2026-09-06`。3つの独立したMITライセンスのコードベースです。
前版の自動復旧、クラスタ変更・停止確認、ファイル復旧、制御停止、バックアップ保持を残し、ホスト・サービス・ネットワーク・起動・全体系構成・リリース判定を追加しました。

**これはソース強化版であり、起動可能なLinuxディストリビューションや、本番認定済みのバイナリではありません。Adaコンパイル・実行とGNATproveは未実施です。**

|リポジトリ|今回の追加|
|---|---|
|`pkgcore/`|RPMと生成imageの出所・kernel/initramfs/module/driver等を束ねる構成検査、独立RPM spec|
|`statecore/`|読取り専用hostctl、三値のhost admission、service graphと資源予算、systemd unit生成、ネットワーク変更状態と永続制御、実NM checkpoint呼出し、起動安定性評価、observer unit/timer、独立RPM spec|
|`assurance/`|proc/sys固定パスのbounded reader、31項目のexact-subject署名付き資格証拠、source/vendor/profile更新と公開fixture再生成工具、共有契約固定、配備・受入れ文書、独立RPM spec|

## 入口

`STATUS.ja.md` → `assurance/docs/distro-foundation.ja.md` → `assurance/docs/build-and-test.ja.md`。
実装と未接続境界: `assurance/docs/distro-traceability.md`、`assurance/platform/component-map.json`。
各独立RPMの作成入口: 各repoの`packaging/README.ja.md`。サービスや鍵の自動配備はしません。

```
statecore/docs/platform-admission.ja.md
statecore/docs/network-transactions.ja.md
statecore/docs/boot-readiness.ja.md
pkgcore/docs/system-composition.ja.md
assurance/docs/release-qualification.ja.md
assurance/docs/distro-migration.ja.md
```

共有ソースは114ファイル、profileは `4456e174f112533e103adfb3050dd58e006f9e5f39772e911a087bb7e20ff8b0` です。これはソース差分ロックであり、署名・証明ではありません。旧認可を暗黙に変換しません。

## 実装範囲の区別

hostctlは実際のproc/sysを読むコードです。ネットワーク制御は実ファイル永続化と、固定busctlからNMへ呼出すコードを含みますが、認可・独立観測・アンカー・対象設定の検査は必須接続です。純粋なboot assessmentはimage書込みやTPM検証を実施しません。system compositionもnative RPMDBの完全な置換ではありません。

新しい検査を既存の全workerへ自動挿入したとはしていません。信頼するSDK接続、完全な対象一覧、外部効果の正しい観測と、迂回されない権限制御が必要です。

## 検査

独立参照・署名・限定Linuxプローブ82項目、ソース・配備構文86項目、保守工具9項目を今回実行しました。これをAdaの実行試験や形式証明の成功とは扱いません。`assurance/evidence/METHODS.ja.md`に範囲、実際のログ、NOT_RUN条件を記録しています。

## 重要な未完境界

全RPM scriptlet/trigger/RPMDB所有権移行、ホスト/の全面管理、bootloader/image installer、常駐fleet/request distribution、物理fencing、業務観測、DB migration・実復元、資格情報provisioning、長期GC、実機でのpartition/powercut試験と運用支援体制が残っています。

SPARKコアとLinux/native APIを扱うAda `SPARK_Mode => Off`境界を分離しています。未知状態を合格扱いにしたり、Secure Boot/TLS/LSM/監査を自動解除したり、人工テスト鍵を本番へ登録したりする経路は追加していません。
