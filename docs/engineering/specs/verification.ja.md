# 仕様 E-VERIFY-1: 検証層と終了条件

|層|何を確認するか|確認できないもの|
|---|---|---|
|文書/在庫lint|要求・ADR・コード・試験の参照、全テストmainの登録|機能の正しさ、証明|
|参照モデル|有限状態・クラッシュ切断点・拒否規則の設計矛盾|Ada/FFIの実挙動|
|Ada単体|codec、replay、境界値、契約assertion|対象装置での永続化|
|隔離I/O|実journal/CAS/fsync/read-only inspector|電源断やcluster安全性|
|GNATprove flow|対象SPARKのデータ依存・初期化|未指定の要件やFFI|
|GNATprove proof|契約・実行時エラーに対する証明義務|仕様自身の適切性、未検証境界|
|対象環境試験|実FS、Secure Boot、NM、systemd、etcd、fence、restore|想定外の故障の無条件保証|
|独立レビュー/運用承認|正確な成果物に対する人と責任の承認|将来の変更を無条件に承認すること|

## リリース手順

source/vendor profileを固定 → inventory/traceability → 全source compile → 全GPR test main → 接続適合 → flow/proof →
parser/fault/upgrade/target試験 → 依存・脅威レビュー → exact binary/source/contract/platformの署名付き資格証拠。
途中層のPASSで後続層を省略しません。ツール不在はNOT_RUNで、successにしません。

'test-plan.json'は通常unit/隔離I/O/ホスト読取の分類と引数を記録します。
任意production対象を指定するテストは含めません。実際のfencing等は別の専用ラボと事前承認で実施します。

## 新しい回帰試験

missing journalを作らない、完全レコード破損を保持、部分末尾のdigest不一致を拒否、
同じpinの再送で一時ファイルが増えない、receiptを途中変更できない、完了領域と実像の不一致を拒否する試験を用意します。
Ada試験はこの環境では未実行です。Python参照試験は別実装として明記します。

## 証跡

各実行に新しいdirectoryを作り、source subject、実際のコマンド・終了コード・tool version・ログhash・開始終了時刻を記録します。
前の版のevidenceは歴史資料で、現在のsubjectへ再利用しません。source変更後はsubject不一致を表示します。
署名と独立評価のないCI JSONは本番承認ではありません。ログ自体にも権限と保管方針を設けます。

## 故障カタログと参照モデルの対応限界

fault-cases.jsonの26項目は実機の受入れ計画です。Pythonのtest_replay_model.pyを参照先に載せていますが、
それによって全故障が参照モデル上で再現されたことにはなりません。
参照モデルが実際に扱うのはログ形式・順序・receipt・切断prefix・Before/After分類です。
容量不足、媒体の永続化、鍵やネットワーク、実業務データの復元は別の未実施試験です。
実機検証結果を得るまではcatalogのexecutionをnot-runから実行済みへ読み替えません。
