# 設定互換性・配布入力の異常対応

1. 新しい変更を保留し、認証済みplan・receipt・報告・元設定・新vendor既定値を保全する。秘密値を公開ログへ出さない。
2. exact package/adapter/validator、native優先順位、include、kernel command line、initramfs、実行個体を照合する。
3. unknownと廃止/矛盾を区別する。観測器が不在なら構文正常を捏造せず、資格化された観測器で取り直す。
4. NVIDIAなら通知方式、旧hooks、保存方式・容量、署名とcohortを検査し、Secure Boot等を切らない。
5. 原因が競合writer/不正変更なら自動上書きを止め、既存incident/隔離手順へ進む。
6. 修正または復旧は新しい認可計画と現在のデータ互換性を必要とする。古い承認や信頼を戻さない。
7. 対象候補と稼働状態を別々に検査し、再起動があれば旧結果を破棄して安定時間を再計測する。
8. 配布input異常では実imageをビルド/起動せずsnapshot・承認鍵・世代を再照合する。

禁止: --nodeps/--nogpgcheck、SELinux permissive、無認証validator、任意shellの実行、native RPMDBと別DBの二重書換え。
このrunbookの存在は障害試験の実施証拠ではない。復旧終了には独立した現場確認が必要。
