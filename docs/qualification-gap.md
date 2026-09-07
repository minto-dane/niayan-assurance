# Current edition additions — still unqualified

New host probes, service catalogue, NetworkManager SDK, boot/cohort and signed qualification APIs do not eliminate the existing native-root/RPMDB, fleet execution, real observer/fence/data/backup and boot-installer gaps. New RPM specs are not tested rpmbuild outputs. Every pure-model fact must be established by its trusted adapter. Boot assessment is NOT a bootloader or TPM verifier. Compilation/proof/integration remain NOT RUN. See distro-foundation.ja.md and distro-traceability.md.

## Previous detailed gap register (retained)

# この版で新たに明確化した未完境界

今回追加したcodec/状態機械/実I/O SDKにも、未コンパイル・未実行・未証明の部分があります。
コンパイル修正だけで本番認定へ進むものではありません。

1. authenticatedな全対象inventory、停止ラッチの実効性、穴のない完了watermark、受信側時刻と遠隔署名を結ぶ観測橋・配信daemonはサイト側の実装・適格化が必要です。
2. guardの初期設定・更新、独立したrevision高水位、CA/RBAC分離は利用側が提供します。etcd応答のID検査だけで誤clusterへの事前書込防止とはなりません。
3. State_Barrier_Store/Pkg_Quiescent_EngineはSDKです。既存workerを全てこの経路へ切り替えるdeploy/移行サービスは追加していません。
4. etcdctl native JSONの合成fixtureを使っています。固定する実binary/serverによる成功・失敗・省略field・非ASCII・timeout・certificate更新を統合試験する必要があります。
5. 停止確認と実ファイル/サービスの間は単一ACID transactionではありません。外部資源fencing、継続した停止ラッチ、再照合が必要です。
6. RPMDB全面移行、全scriptlet、boot chain、backup取得/削除/復元、フリートdaemon、物理隔離、長期運用・電源断・災害復旧の既存未完項目も残ります。

---

## 以前の版の説明（変更点は上記を優先）

# Current delta — assured-operations-source-2026-09-06

This edition is NOT QUALIFIED. Build/execute/GNATprove, physical failover and power-cut tests remain unexecuted. Added interlock, checkpoint, backup, readmission and disaster code does not remove the site integration gaps below.

Current specific boundaries: no distributed stop broadcast/ACK service; no cancellation of already-dispatched actions; no online authority rotation; protected policy files alone do not resist privileged full-volume rollback; recovery receipts need site validation; no default nonrollback anchor; unanchored pending checkpoint needs explicit operator reconciliation; no existing-WAL compactor integration; retention is a planner, not a delete executor; no native fencing/backup/DB restore/client rebind implementation; new etcd stores require a surviving independent control plane.

**Do not return OK unconditionally from generic authorization/anchor callbacks to complete integration.** Test-only synthetic evidence and public fixture keys are not production trust sources.

Prior-edition qualification details follow and remain relevant unless explicitly superseded above.

---
# Qualification gaps — current resilience edition

This source distribution is NOT production qualified. The earlier v2 limitations were not removed merely by adding recovery policy modules.

## Implementation, not just toolchain

- Full native RPMDB migration and ownership handover, all RPM dependency/scriptlet/trigger semantics, host `/` mutation remain outside this release. Independent managed roots only.
- Site topology/semantic-health/data-compatibility observers and their signing/revocation/high-water lifecycle are not implemented as a finished deployed service. Signing a supplied report is not observing facts.
- Physical fencing, storage-side fencing-token enforcement and real data promotion are NOT implemented by `State_Failover`; it is an admission predicate for qualified evidence.
- Rich etcd reservation and rollout persistence exist as SDKs. A complete fleet distribution/dispatch/operator control plane is not supplied.
- Continuous automatic scrub→independent authorization→execution→new accepted inventory publication is not a finished daemon. Scanner, constrained planner and existing execution engine exist separately.
- Boot-chain writes, authenticated recovery media production, firmware changes, DB schema migrations, backup/restore systems and disaster recovery are not implemented.
- Journal compaction, supported recovery-state/budget-policy migration, administrative hold release, zero-downtime observer/profile rotation and external alert transport remain design/integration work. Deleting journals to reset limits is not a substitute.

## Validation

- Ada compilation, Ada unit/integration/I/O tests and GNATprove were not run successfully in the available environment. A compiler frontend/toolchain was unavailable.
- `SPARK_Mode` and contracts are specification intent, not proof results. Native I/O/command/crypto adapters are explicitly unproved Ada `SPARK_Mode => Off` boundaries.
- No systemd/Pacemaker/etcd deployment, live quorum/fence, real power loss, hardware watchdog, Secure Boot, full filesystem failure injection, backup restoration or long-duration load qualification was performed.
- Linux x86-64/glibc FFI assumptions, storage durability, dynamic native-library dependencies and systemd/Pacemaker version output profiles need deployment-specific validation.

## Required release gates

No release should be labeled mission-critical on code volume, model checks or build success alone. Record reviewed requirements and actual evidence for functional/flow proof obligations, parser robustness, persistence failure points, key/profile upgrades, unknown effect reconciliation, network partitions and fencing, data durability/recovery, dependency failures, resource exhaustion, actual node/domain capacity, operator recovery and change approvals.

Keep the old compatible recovery path for unresolved records during upgrades. Preserve audit/trust/revocation facts outside software rollback. An availability shortcut that fabricates observations, clears failed checks or auto-reinitializes lost state is not acceptable.
