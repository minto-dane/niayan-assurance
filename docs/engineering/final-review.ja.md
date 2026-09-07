# Nia OS 実装・接続の最終レビュー

2026-09-07。レビュー対象は本ZIPのsource集合であり、実機製品の資格化ではない。

## 判定

供給元・所有権・設定・変更・復旧・信頼の責任は定義されている。一方、full-rootの導入、実boot/HA/data backend、適格な観測器、強いgateの全実行経路への接続は未完である。この配布を「コンパイルの微修正だけでデータセンターへ配備できるもの」と分類しない。

現行の[実行契約](specs/execution-safety.ja.md)と[本番接続表](specs/production-closure.ja.md)を読み、機能名ではなく、認証済み入力から効果・回復・実観測まで到達できるかで評価する。

## 確認した問題と修正

| 識別 | 問題 | 処置 | 検証境界 |
|---|---|---|---|
| F-01 | helper leaderが先に終了すると子孫groupのcleanupを飛ばす場合 | pidfdで観測、未回収leaderのままgroup cleanup、期限／出力上限 | Python runner/nativeは実行、Ada本体は未実行 |
| F-02 | stdout close後にdeadlineが失われる開発runner | leader終了とEOFを別に待つ。reap前にcleanup | 実プロセスの否定試験 |
| F-03 | 標準FDが閉じた呼出しで0..4への複製が衝突し得る | fork前にsource FDを64以上へ複製 | Ada回帰試験を用意、未実行 |
| F-04 | 同一inodeへの変更後mtimeだけ復元すると観測を流用し得る | ctime、事前／事後FD、最終path照合 | 実statx ABI/nativeとsource検査、Ada未実行 |
| F-05 | 新規intentがログ容量を消費し完了を記録できない | receiverと全管理planの論理余力をadmission時に検査 | finite model、Ada境界試験は未実行 |
| F-06 | 結果不明の反復観測で容量を消費する | 正確に同じ未解決状態の再観測はno-op | source/モデル。新情報は通常記録 |
| F-07 | 既存lock欠落時に別inodeを作成し得る | 初期化と通常アクセスを分離 | source検査、Ada root-lock欠落試験を追加 |
| F-07b | CAS Openがlock/pins欠落を新規状態で隠す場合 | 空の私有領域のInitializeを分離、返す内容も再hash | source検査、Ada欠落・旧lock保持・pins保全試験を追加 |
| F-08 | model Generationとmembership Epochを等号比較 | namespaceを分離、native/sourceとlive authorityで別々に拘束 | source検査、実接続は未完 |
| F-09 | 独立した強いgateの合成を呼出し側が落とし得る | Pkg_Managed_Engineで全callbackを必須とし弱いEngineを非公開化 | 接続SDK。旧worker全面移行ではない |
| F-10 | handbookの現行base表示とADR indexが不一致 | Nia/DEB/XFSの入口と全ADR索引へ統一 | 台帳・全local参照・source固定の機械検査 |

設計変更の理由・代替案は[ADR-0049](adr/ADR-0049.ja.md)へ記録する。通常の製品文書は現行仕様を記述する。wire/disk形式を無断で解釈変更せず、shared sourceと管理器profileを更新し公開fixtureを再生成する。

## 今回の検査の意味

`assurance/tests/engineering/test_final_runtime.py`は実際の検査runner、害のない有限時間child、Linux pidfd/statx/FDを使用する。source文字列の回帰確認と独立した有限算術モデルは、そのレイヤーとして区別する。Ada版を代用して動かした試験ではない。追加のAda test mainはtest-planに登録し、私有領域とそのtestが生成したchildだけを扱う。

全既存Python/native-tool試験、契約の固定、管理器profile、resolver source、lineageの変更対応、ADR/要求/危険/故障/test-mainの照合を再実行する。実際の結果は`assurance/evidence/final-review/`に保存し、過去のPASSは現行の証拠として転用しない。

## SPARK導入

SPARK/GNATproveは無償の導入経路がある。公式資料は手動のFSF buildとAlire経由を示す。ソース本体の証明を行う場合、対応するGNAT/compiler/runtimeとGNATproveを揃え、配布の出所と成果物hashを保存する。

この環境ではgccはあるがgnat1/GPRbuild/GNATprove/Alireはない。実compiler呼出しはgnat1不在で失敗し、Debianと公式GitHubのHTTPS取得は名前解決に失敗した。local cacheも確認したが導入済みbinaryは見つからなかった。TLSを無効化したり未確認のbinaryを実行する代替経路は使わない。実ログを証拠へ収録する。

この結果は「SPARKを一般に導入できない」という意味ではない。本環境でAda build/試験/flow/proofを実行できなかったという限定された結果である。proofを実施していないのに警告ゼロや全証明済みと記録しない。

一次資料:
- https://docs.adacore.com/spark2014-docs/html/ug/en/install.html
- https://alire.ada.dev/crates/gnatprove
- https://github.com/alire-project/GNAT-FSF-builds/releases
- https://docs.adacore.com/spark2014-docs/html/ug/en/source/how_to_run_gnatprove.html

## 受け渡し

これはコード・契約・実行した開発検査を揃えたsource配布である。独立審査、本体build/proof、採用closureの統合、target障害行列を完了して初めて対象範囲を拡大する。署名、メタデータ正常、helper終了、solverの解、文書の参照一致を相互に代用しない。

## 再検査中に検出したprofile不一致

共有source更新後の全体検査で、resolverの固定profileとmanagerの人工fixtureが旧profileを参照していることを検出した。検査条件を緩めず、依存順にprofileと人工fixtureを再生成する`rebind-development.py`を追加した。手順は開発仕様に記録し、初回失敗ログも過去の試行として保持する。
