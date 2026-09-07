> 過去の別系統版から統合した参考文書です。記載された実装モデルの復元を意味し、収集器・実機接続・形式証明の完成を意味しません。現在の統合範囲は `assurance/docs/engineering/specs/unified-management.ja.md` と機能台帳を参照してください。

# Platform qualification

`platformctl check FACTS single|cluster` は `MC_Platform_Profile` の入力を厳格な key=value 形式から読み、必要条件が欠ければ non-zero exit する。

これは検査対象から事実を収集するツールではない。FACTS は qualified observer が、ノード identity・baseline・policy に束縛して作ること。

特に次を禁止する。

- 管理対象自身が `secure-boot=true` 等を自己申告しただけで admission する。
- `getenforce` 等一つのコマンドの文字列だけで security policy 全体を証明したとみなす。
- backup file の存在を restore test とみなす。
- fencing command の exit 0 を、旧 writer が物理的に隔離された証拠とみなす。
- wall-clock rollback 後に古い署名/lease を再び valid とみなす。

実 platform adapter は TPM quote、event log、IMA measurement/appraisal、remote audit receipt、crash dump receipt、backup restore receipt、out-of-band controller 等を独立に照合する。
