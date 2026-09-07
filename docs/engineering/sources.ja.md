# 外部根拠（一次資料、2026-09-06確認）

自作仕様の選択はADRで記録し、以下の資料と区別します。認証や適合認定を取得したことを意味しません。

- Linux fsync(2): https://man7.org/linux/man-pages/man2/fsync.2.html — ファイルとdirectoryの永続化、エラー。
- Linux rename(2): https://man7.org/linux/man-pages/man2/rename.2.html — 単一name変更とエラーの範囲。
- etcd API guarantees: https://etcd.io/docs/v3.5/learning/api_guarantees/ — APIの保証と応答喪失時の結果不明。
- etcd disaster recovery: https://etcd.io/docs/v3.5/op-guide/recovery/ — revision、restore、watch再構成。
- SPARK User's Guide / team usage: https://docs.adacore.com/spark2014-docs/html/ug/en/source/how_to_use_gnatprove_in_a_team.html — 前提と未検証コード。
- NIST SP 800-218（2022 final）: https://csrc.nist.gov/pubs/sp/800/218/final — 開発工程へのセキュリティ組込み。
- NIST SP 800-218r1 initial public draft: https://csrc.nist.gov/pubs/sp/800/218/r1/ipd — この参考資料を既存finalや取得済み認定と混同しない。
- SQLite atomic commit: https://sqlite.org/atomiccommit.html — DB内部のatomicityの参考。本管理器はSQLiteのACID保証を継承していない。

版が変わる外部APIは、リリースで固定する実binaryとserverで再試験します。資料の閲覧だけを接続試験に数えません。
