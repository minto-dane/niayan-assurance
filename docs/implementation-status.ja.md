# 実装位置 — 耐障害・自動復旧強化版

| 要求 | 主なsource | 実装と境界 |
|---|---|---|
| 再起動で消えない復旧予算 | assurance/src/mc_retry_budget.*, statecore/src/state_healing.* | bounded FSMと実journal。budget無制限resetなし |
| 健全性の署名と鍵分離 | mc_health_report.*, mc_authentic.*, mc_gate.*, mc_site_policy.* | Ed25519経路とworker role/freshness検査。観測真実はsite責任 |
| 単一ノードの実復旧 | state_recovery_worker.adb, state_healing_engine.*, state_systemd_control.* | 実systemd操作。認可とfactsを外側から供給 |
| 依存故障の連鎖抑制 | state_dependency_graph.* | 循環/順序/伝播の判断器。発見daemonではない |
| crash/未知結果の継続 | state_healing_journal.*, mc_log.*, mc_store.* | 実CAS/WAL・exact前提・blind replay禁止 |
| 部分末尾の復旧 | state_healing_repair_claim.*, worker Repair分岐 | prefix/head/tailと署名を固定、保存/receipt/fsync/再認可後のみtruncate |
| rich cluster予算 | state_cluster_safety.*, state_reservation_safety.*, state_strict_coordinator.* | 純粋なadmission + 実etcd CAS SDK |
| canary/soak/回帰停止 | state_rollout.*, state_rollout_codec.*, state_rollout_store.* | FSM + 実永続化SDK。全配布daemon未完成 |
| planned reboot後の継続 | State_Rollout.Accept_Node_Boot | boot plan等のqualified証拠を要求。bootwriterではない |
| split-brain回避 | state_failover.* | 新旧incarnation/token/物理隔離/data条件。物理実施は外部 |
| 破損ファイルの確認 | pkg_inventory.*, pkg_image_inspector.*, pkg_scrubber.*, pkg_scrubctl | real fd/hash/xattr/metadata観測。独立root限定 |
| 自動修復の計画 | pkg_self_repair.* | exactBeforeと認可baselineから通常FilePlan生成。実施は前版workerへ |
| 回復点の安全な選択/保持 | pkg_recovery_catalog.* | 判断器。自動削除/DB復元ではない |
| コネクタ変更管理 | mc_contract_profile.*, contract_lock.*, ci/check-contract.sh, ci/cross-repository.sh | 固定sourceと実行時profile。proofや全private code同値性ではない |

全コードのbuild/実行/証明は別工程です。追加したAda試験も今回の環境では未実行で、別言語の参照チェックと混同していません。
