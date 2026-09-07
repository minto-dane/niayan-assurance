> 過去の別系統版から統合した参考文書です。記載された実装モデルの復元を意味し、収集器・実機接続・形式証明の完成を意味しません。現在の統合範囲は `assurance/docs/engineering/specs/unified-management.ja.md` と機能台帳を参照してください。

# Trusted Computing Base / proof boundary

SPARK `Pure` core で証明を狙うのは state transition、authorization predicate、bounds、rollback/fencing/admission rules である。

`SPARK_Mode => Off` runtime、Linux kernel、filesystem/device durability、libsodium、libarchive、libcurl、libxml2、firmware、TPM、systemd、Pacemaker、etcd、database、hardware は無条件に証明済みとは扱わない。

外部 adapter には以下を要求する。

1. exact object identity / generation / boot ID への binding。
2. canonical encoding と domain-separated signature。
3. stale/replay/rollback protection。
4. unknown result を success に変換しない。
5. destructive effect より前の durable intent record。
6. state transition 後の independent observation。
7. adapter 自身の version/digest を accepted baseline に含める。

コンパイラまで証明する構成を将来採用する場合も、OS syscall/driver/hardware assumption は別に残る。
