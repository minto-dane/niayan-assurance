# Recovery cohort v1

## 認証

manifestはASCIIへ正規化した、key順・空白なしJSON。重複key、非有限数、型違いのcounterを拒否する。anchorは`NIA-RECOVERY-ANCHOR-v1`とNULに正規JSONを連結してEd25519署名する。署名される要素はnode、generation、trust_epoch、manifest_sha256、pending_sha256、issued/expires、nonce。外部でpinしたanchorそのもののSHA-256に完全一致することを先に要求する。

trust文書はnode/current trust/min generation、threshold、最大anchor寿命、鍵registry。thresholdは2以上。署名は別principal、別public key、別domainを要求し、recovery役とwitness役を両方必要とする。domainの物理的独立性は組織の鍵運用が保証し、名前の違いだけから証明しない。時計も外部の健全性条件が必要。

## manifest

`nia-recovery-manifest-v1`はnode、cohort digest、generation、trust_epoch、catalog_path、checkpoint_path、ソート済みpending要求ID、root_attributes、directories、objects。各objectはpath/kind/mode/uid/gid/xattrs/size/sha256/chunks。通常ファイルのみ。kindはmanaged-file/catalog/checkpoint/journal/audit。catalog/checkpoint/journalは必須。directory/rootもmode、uid/gid、xattrを記録する。各fileの祖先directoryをすべて列挙し、認証されたempty directoryも保持する。余分なdirectoryはdrift。

chunkは65536bytes、最後のみ短い。chunk hashとwhole-file hashを両方照合する。1cohort最大16384objects、65536chunks、4GiB。metadata最大8MiB、xattrは1object256件/128KiB。大規模システムは独立した整合性単位へ分割し、全cohortのrootを外部anchorへ結び付ける追加の運用接続が必要。上限を超えた際に検査を省略しない。

## 準備工具

`export()`はライブラリ関数で、静止した通常ファイル集合からunsigned manifest/chunk群を作る。全input集合は事前事後に確認し、sourceとoutputの重複を拒否する。署名・独立commitを行うサービスは別。

```
python3 assurance/tools/nia_recovery.py verify --anchor ANCHOR.json --trust TRUST.json --expected-anchor SHA256 --replica COPY1 --replica COPY2
python3 assurance/tools/nia_recovery.py inspect --anchor ANCHOR.json --trust TRUST.json --expected-anchor SHA256 --replica COPY1 --state-root CLOSED_STATE_ROOT
python3 assurance/tools/nia_recovery.py reconstruct --anchor ANCHOR.json --trust TRUST.json --expected-anchor SHA256 --replica COPY1 --replica COPY2 --candidate EMPTY_PRIVATE_DIRECTORY
```

候補は新しい私有directory。元データへのwriteはない。`candidate-ready.json`は独立native検査と結果照合が必要な状態であり、run permissionではない。破損metadataは他copyからhash一致のものを探索するが、署名検査前に信用して書き込まない。元anchorが取得できない場合は停止する。
