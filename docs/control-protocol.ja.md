# MC-CONTROL-v1 — 二者承認・永続的変更停止

## 意味と保存

scopeはpolicy rootのIdentityです。個人名などではなく16バイトのID。authoritiesは最大8個で、public keyとprincipalは重複不可、domainは1..65535、Operations/Security両方が必要です。bootstrap CLIは2鍵の構成を生成します。

ファイルはowner=euid、通常ファイル、link count=1、mode0400/0600、exact sizeを検査します。親rootは既存MC_FSのPrivate_Only検査を通す必要があります。競合書込みはcontrol.lockで直列化し、requestと状態履歴を保持してからcurrentをatomicに置換します。

初期化はQuarantinedだけ。解除/緩和は、必要署名数、両役割、複数domain、新trust-epoch、非ゼロrecovery-receipt hashを必要とします。同一requestのexact retryは保存済み要求・全署名と照合し、再適用しません。

receipt hashは任意の内容の真実性を自動的に証明しません。解除担当者は、そのhashに対応する観測・試験・fencing等の証拠を別途確認する責任があります。sign-proposalは内容を理解して承認する人間/認可器の代替ではありません。

## 検証環境での操作順序

本番policyとは別の、所有者限定0700のディレクトリと独立した2鍵を用意します。既存 `assure keygen` の構文はassureのusageを参照し、鍵ディレクトリをネットワーク公開しないでください。

1. `controlctl make-authorities SPEC POLICY` で公開鍵と役割を固定します。既存ファイルへの上書きは禁止です。
2. `controlctl make-proposal SPEC POLICY OUT` でreceiverのboot IDと単調時刻を含む候補を作成します。初回はmode=quarantineです。
3. `controlctl inspect-proposal OUT/control-proposal.bin` で対象・前状態・要求・reason/receipt・期限を確認します。表示は署名検証済みの意味ではありません。
4. 各署名者が `controlctl sign-proposal PROPOSAL KEYDIR SIGDIR` を別々に実行します。同一のcanonical proposalへ署名してください。
5. `controlctl bundle POLICY PROPOSAL SIGDIR OUT` で署名を検査し、bundleを作ります。署名不足でもbundle生成自体はあり得ます。閾値はsubmitが判定します。
6. `controlctl submit POLICY SCOPEHEX PROPOSAL BUNDLE` で検査・永続化し、`controlctl status POLICY SCOPEHEX` で確認します。
7. 解除には新しいrequest、新しい前状態hash、新trust-epoch、実際の根拠hash、独立した両役割の署名を必要とします。

make-proposal/sign/bundleの出力先は新しいprivateディレクトリを使い、既存の証拠を上書きしません。受理期限は受信ノードのboottimeに基づき最大300000ms。分散時計合わせを仮定しないため、異なるマシンで生成したproposalをそのまま受信ノードで使えません。初期化後のtime expiryで制御状態が解除されることはありません。

テンプレートは `assurance/examples/control-*.conf.in`。値は意図的に非動作placeholderです。テストfixtureの公開鍵をproductionに信頼させてはいけません。

## バイナリ形式

以下は1始まりbyte position。整数はbig-endian。Counterは0..2^63-1。reservedはすべてzero。decoderはencodeし直して全byte一致を要求します。以下のSHA-256は破損検知であって署名ではありません。

### Authority: 1024 bytes

1..8=`MCROLE01`; 9..24=scope; 25..56=contract source profile; 57..64=serial;
65=count; 66=tighten threshold; 67=resume threshold。
97+(i-1)*96から各signer: 32-byte key、16-byte principal、2-byte domain、1-byte role(0=Operations/1=Security)、残りzero。
993..1024=SHA256(bytes1..992)。未使用slotもzero。

### Proposal: 320 bytes

1..8=`MCPROP01`; 9..24=scope; 25..56=contract;
57..64=expected revision; 65..72=new trust epoch; 73=desired mode(0 Running,1 Held,2 Quarantined);
81..96=receiver boot; 97..112=request ID; 113..144=expected exact state SHA256;
145..176=reason hash; 177..208=recovery receipt hash; 209..240=authority frame SHA256;
241..248=not-before boottime-ms; 249..256=expires boottime-ms;
289..320=SHA256(bytes1..288)。

Ed25519 signs: `u16be(13) || ASCII("MC-CONTROL-v1") || proposal320`。
注意: domain文字列の実際の長さはコードの `Domain'Length` / `len(domain)` を正本とする。バイナリは固定文字列をlength-prefixで分離し、他の署名領域を受理しません。
bundleは512 bytes、authority順の8×64-byte署名。未署名slotはzero。

### State: 256 bytes

1..8=`MCCTL001`; 9..24=scope; 25..56=contract; 57..64=revision; 65..72=trust epoch; 73=mode;
81..96=incident ID; 97..112=last request; 113..144=previous state SHA256;
145..176=reason hash; 177..208=authority SHA256; 225..256=SHA256(bytes1..224)。
Runningのみincident=zero。genesis revision=1のみprevious=zero。署名済み提案と署名bundleは別のimmutable requestファイルに保持します。

## 未対応・禁止

authorityファイルの直接置換によるオンライン鍵ローテーションは未対応で、既存stateとのhash不一致になります。旧/新両authorityで承認するrotationプロトコルを追加するまでは、別管理の鍵変更・移行計画が必要です。
現在のコードは履歴の自動GC、全フリート配布、権限逸脱したrootからの全volume rollback防御を実装していません。欠落/破損時に勝手にgenesisへ戻してrunningにする手順は禁止です。
