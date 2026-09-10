# Nia OS 本番接続と受け入れ条件

状態: 規範仕様。起動可能製品の完成宣言ではない。対象は固定Debian 13 TrixieのDEBを供給入力とするNia OS、XFS永続領域、amd64。

## 保証の単位

製品資格はソース名やOS名ではなく、ソース・ビルド・契約・パッケージ集合・設定・カーネル・ハードウェア・障害モデル・運用責任者の正確な組に対して行う。全機能名が一覧にあることは、観測から実行・復旧まで経路が閉じている証拠ではない。次の表のいずれかが未完なら、対象の業務を承認しない。

| 領域 | 現在の実装 | 閉じるべき実行経路・受入試験 |
|---|---|---|
| Supply | 署名chain、DEB読み取り、署名付き一原本CAS照合、正確な新規原本差集合のmap、source/rebuild receipt、profile工具 | 本番observer/key配備、mapと実際の受理済み基準・公開計画・保持への束縛、記録済み復旧と新規admission、公式採用集合の全量検査、鍵失効・時刻・期限、供給遅延、例外承認と緊急修正 |
| 意味 | neutral solver、DEB比較、独立候補／証明検査 | 元情報から全phase/effectへの変換、元形式での再検査、全closureに対する不正候補試験 |
| 設定 | 汎用schema／merge／priority、NVIDIA契約、段階別証明 | 個別ソフトの全inputとネイティブ検証、生成物、実行中の値、issuerの分離 |
| ファイル | descriptorベースのcapture、WAL/CAS、原本／終端照合 | Nia full-root/catalog assembler、初期所有権、全副作用と原子的公開境界 |
| 合成 | Pkg_Managed_Engineの必須callback連鎖 | 実workerへの接続、同じ排他予約、全phaseで抜けのない負の試験 |
| 管理 | 署名plan、installp等の採用CLI、request/result照合 | 認証済み遠隔transport、receiver識別、manager HA、幂等な受領とreplay拒否 |
| クラスタ | etcd CAS、quorum/停止予算、barrier、failover判断 | 実トポロジー、独立fencing、書き込み経路の遮断、分断／遅延／二重writer試験 |
| サービス | systemd/Pacemaker adapter、復旧予算と結果不明 | restart責任者の一元化、実業務health、依存障害、飽和と再参加 |
| XFS | 観測工具、health状態、非修復unit | 対応kernel/tool/feature、署名event collector、完全性・修復結果・rescueの実接続 |
| データ | backup/retention/readmission/disasterの判断SDK | DB固有schema migration、WAL/PITR、実backup/backend、鍵復旧、復元訓練 |
| 起動 | UKI／ESP／LUKS／layout契約、候補評価 | 認証済みdisk identity、format/installer、鍵登録、両起動経路、電源断／鍵失効 |
| 信頼 | 署名・期限・subject・control状態 | 運用鍵の保管・交代・失効、独立antirollback floor、認可基盤の回復 |
| MAC | AppArmor product方針、service隔離契約 | 実profile、違反時の手順、loader/library/cgroup、kernel資格、最小権限 |
| RAS | FRU/WLM/電源・ネットワーク・時刻のモデル | 実sensor、観測範囲、複合障害、diagnostic/privacy、過度の自動修復抑止 |
| 長期運用 | 有限ログ、論理完了予約、pinとcheckpoint SDK | 参照閉包とアンカーを伴うGC／移行、容量枯渇、バックアップ時の整合、監査保持 |
| Release | source manifest、契約固定、証拠工具、出荷条件 | first-partyの実build/proof、イメージ構築、SBOM/source義務、署名・独立承認 |

「外部接続」と記したものは細かなコンパイル修正ではない。サイト固有であっても、製品側に受け取る証拠、失敗時の状態、再試行条件、権限、timeoutと所有権の契約が必要である。生のBooleanや終了値をその証拠へ自動変換しない。

## 安全性と可用性

新規変更の前提が不明なら新規変更を止めるが、無関係の正常な既存サービスは維持する。書込所有権が不明な資源は封じ込める。沈黙・期限切れ・helper終了・多数の正常応答だけで旧writerの停止を断定しない。

N+1の更新余力は物理的な故障領域と復元可能なデータを伴わなければならない。三つのVMが同じhost/storage/powerへ依存している構成を三障害領域と数えない。保守中さらに故障する条件と、通常時一故障の条件を分ける。RTO/RPO、性能の最悪側遅延、受入停止の上限は業務契約に値を持たせる。

全原本・全復元鍵の喪失、任意の侵害kernel、無制限のroot writerをソフトウェアだけで完全修復する保証は置かない。独立backup、鍵の別系統回復、隔離と再構築の手順が必要である。XFSのmetadata検査をファイル内容・DB整合性・攻撃検出の代わりにしない。

## 必須障害行列

1. intent保存の前後、外部操作の前後、完了保存の前後、復旧の途中でそれぞれ停止。
2. fsync失敗、disk/inode/log容量不足、CAS/pin/lock/journal欠落、完全record破損と部分末尾。
3. 正常な応答が遅れて到着、成功した操作の応答喪失、同一要求再送、無効なnative候補。
4. ノード・boot・catalog・cluster各世代の変更、時計の逆行、証拠失効、鍵交代。
5. cluster分断、旧writer停止の失敗、fencing経路だけの故障、観測経路欠落。
6. 旧設定が新版で廃止、同一バイトの意味変更、initramfs更新漏れ、データ形式非互換。
7. XFS metadata修復成功だが内容破損継続、監視の欠落、修復timeout、rescueの機能不一致。
8. 正当な業務データを残したOS rollback、失効情報を残した旧boot、管理器自身の更新失敗。
9. 長期稼働のログ境界、collector飽和、child残留、性能飽和中の復旧と証拠保全。

各試験はexpected state、lost/duplicate write、権限の変化、復帰条件を記録する。起動やpingの成功だけでは合格にしない。実行済みと計画を混ぜず、同じsource/binary/profileへ証拠を結び付ける。

## 開発の次工程

最初に全sourceをcompileし、既存の全Ada試験とflow/proofを実行する。認可を緩めたり未証明を除外して形式上成功させない。その後一つの正確な採用closureと単一nodeで、full-root→config→native effects→正常／rescue boot→復旧を閉じる。この同じ実行器を、既存HA契約と物理fencingへ接続する。個別コンポーネントに別の正本を増やさない。
