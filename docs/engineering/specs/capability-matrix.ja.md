> **Nia OS 製品境界**: この文書の旧Leap/SLES/native RPMDB前提は履歴です。現行製品は [Nia構成](../../../../distribution/docs/architecture.ja.md) と [所有権](../../../../distribution/docs/ownership-and-effects.ja.md) を参照。既存部品の安全条件は無効化しません。

# 現行機能・実装段階

正本は`assurance/engineering/capabilities.json`。6runtime repository + distribution。
runtime-unvalidatedは実I/Oソースがあるという意味で、Ada実行・形式証明・本番承認ではない。
[統合仕様](solver-assurance.ja.md) / [配布条件](../../../../distribution/history/leap16/docs/qualification.ja.md)

|ID / 機能|段階|存在する実装|残る条件|
|---|---|---|---|
|CAP-001 統一ローカル管理CLI|runtime-unvalidated|署名plan、WAL、固定native worker起動|local-only; remote fleet daemon/manager HA未実装|
|CAP-002 署名計画・受入れ・部分tail修復|runtime-unvalidated|役割分離・exact subject・fresh期限|reportの意味は独立観測者とsite資格化が必要|
|CAP-003 管理WAL/CASと復旧系譜|runtime-unvalidated|exact資源集合、再生、保全、reservation|全volume巻戻しanchor/GC/長期移行は未接続|
|CAP-004 receiver台帳とgenesis|runtime-unvalidated|空/欠落拒否、明示provision、exact receipt|既存現場台帳の移行審査が必要|
|CAP-005 独立rootのRPM展開/ファイル復旧|runtime-unvalidated|署名・限定意味・前後像・WAL|native RPMDB/host /の全面管理ではない|
|CAP-006 systemd/Pacemakerローカル連携|runtime-unvalidated|固定command、永続intent、再観測|現場設定/独立業務観測は未資格化|
|CAP-007 service autoheal|runtime-unvalidated|予算永続化・明示初期化・結果不明保護|管理者/観測器との実接続試験未実施|
|CAP-008 etcd / cluster / rollout|sdk-unvalidated|mTLS比較更新、予算・段階展開|遠隔配送/監視常駐/実partition試験なし|
|CAP-009 停止確認と隔離署名|sdk-unvalidated|全対象停止・外部隔離確認集約|physical fencing hardware adapter未完成|
|CAP-010 network checkpoint|sdk-unvalidated|NM呼出し・意図・checkpoint|現場経路確認・OOBと統合試験が必要|
|CAP-011 ホスト観測・試験起動判定|sdk-unvalidated|proc/sys観測と条件判定|boot image書込/署名/installer未接続|
|CAP-012 RAS/FMA/FRU/WLM|restored-model|旧分岐の判定モデル復元|実telemetry ingestion/automatic cgroup tuning未接続|
|CAP-013 HOLD / incorporation / acceptance|restored-model|旧分岐の型/判定を復元|全RPMsolver/scriptlet意味への統合は未完成|
|CAP-014 platform/attestation/commissioning|restored-model|証拠・基準・信頼判定|TPM quote verifier/IMA collector現場統合未完成|
|CAP-015 backup保持/復元可能性|sdk-unvalidated|祖先/鍵/復元試験/保持集合の検査|実backup取得・削除・DB restore adapter未完成|
|CAP-016 six-repo開発・適合検査|tooling|ADR/要求/索引/在庫/fixtureの検査|source検査はAda実行・意味証明ではない|
|CAP-017 ネイティブRPMDB移行|not-implemented|未提供|dual-writer防止・全RPM semanticsの実装が必要|
|CAP-018 起動可能なISO/installer|not-implemented|未提供|Secure Boot含むbuild/install/recovery mediaが必要|
|CAP-019 データ復元・鍵災害復旧|not-implemented|判定SDK以上のbackend未提供|アプリ固有移行、RPO/RTO、独立鍵復旧が必要|
|CAP-020 完全OS/cluster ACID|not-promised|原子的全OS transactionとは呼ばない|複数状態領域を補償/照合で管理。全故障・exactly onceを保証しない|
|CAP-021 設定の意味・merge・migration・依存|sdk-unvalidated|exact typed schema, tri-state and guarded predicates|全native adapter/serializer、Ada実行/証明は未完|
|CAP-022 設定観測と診断CLI|runtime-unvalidated|有界native directoryとstrict input診断|署名された完全native観測を自動収集するdaemonではない|
|CAP-023 NVIDIA exact電源互換性|sdk-unvalidated|module flavor/notification/backing/target/running|実機collector・suspend試験・全driverルールpack未完|
|CAP-024 二者署名設定gate|sdk-unvalidated|正規形receipt、exact scope、認可合成|全既存workerへ必須接続は未完、投影adapterが必要|
|CAP-025 Leap16公開配布入力とKIWI生成|tooling|Leap-only、実offline二者署名/RPM-MD/hash検査、XML出力|imagebuild/元署名/依存解決/boot/installer/ライセンス/資格化は別工程|
|CAP-026 統一設定診断入口|runtime-unvalidated|固定hash configctlへのread-only起動|local-only、監視daemon/全fleet配布ではない|
|CAP-027 独立selection/schedule検査|sdk-unvalidated|形式非依存AST/所有権/順序/予算の直接検査|native完全closure、Ada実行と証明未完|
|CAP-028 CNF/独立RUP-RAT証明検査|sdk-unvalidated|決定的Boolean緩和、bounded text proof再計算|formal proof未完、extension variable/binary/無制限proof未対応|
|CAP-029 RPM native意味投影|sdk-unvalidated|EVR、集合with/without、guarded依存/競合、直接再検査|元headerから全Universe、全phase/scriptlet/triggerは未完|
|CAP-030 libsolv/CaDiCaL提案helper|tooling|非特権cache入力、候補/未検証proofのみ出力|実solver版で未実行。外部sandboxとsource認証が必要|
|CAP-031 統一resolver診断と実変更gate|runtime-unvalidated|固定CLI、元認可/native/currentの合成SDK|opt-in、全worker必須接続やnative観測は未完|
