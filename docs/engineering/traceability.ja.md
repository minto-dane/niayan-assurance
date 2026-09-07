# 要求の追跡表

全件が未認定です。statusは実装の範囲であって実行成功ではありません。

|要求|内容|状態|ADR|主な実装|試験|
|---|---|---|---|---|---|
|REQ-001|履歴の厳格な束縛|implemented-unvalidated|ADR-0003|pkgcore/src/pkg_file_replay.ads#Consume<br>pkgcore/runtime/pkg_file_engine.adb#Read_Log|pkgcore/tests/run_file_replay_tests.adb|
|REQ-002|判断receiptの不変性|implemented-unvalidated|ADR-0005|pkgcore/src/pkg_file_replay.adb#Consume<br>pkgcore/runtime/pkg_file_engine.adb#Commit|pkgcore/tests/run_file_replay_tests.adb|
|REQ-003|実像と進行段階の一致|implemented-unvalidated|ADR-0006|pkgcore/src/pkg_file_replay.adb#Image_Allowed<br>pkgcore/runtime/pkg_file_engine.adb#Inspect|pkgcore/tests/run_file_replay_tests.adb<br>pkgcore/tests/run_file_engine_tests.adb|
|REQ-004|欠落記録の非初期化|implemented-unvalidated|ADR-0004|assurance/runtime/mc_fs.adb#Open_Locked<br>assurance/runtime/mc_log.adb#Open<br>pkgcore/runtime/pkg_file_engine.adb#Resume|assurance/tests/run_recovery_storage_tests.adb|
|REQ-005|読み取り専用診断|implemented-unvalidated|ADR-0008|pkgcore/runtime/pkg_recovery_audit.adb#Inspect<br>pkgcore/app/pkg_recoveryctl.adb|pkgcore/tests/run_file_engine_tests.adb|
|REQ-006|完全破損と部分末尾の区別|implemented-unvalidated|ADR-0007|assurance/runtime/mc_log.adb#Repair_Tail<br>pkgcore/runtime/pkg_file_engine.adb#Repair_Torn_Journal|assurance/tests/run_recovery_storage_tests.adb|
|REQ-007|冪等pinの容量保護|implemented-unvalidated|ADR-0009|assurance/runtime/mc_store.adb#Pin|assurance/tests/run_recovery_storage_tests.adb|
|REQ-008|保護rootの排除|implemented-unvalidated|ADR-0001|pkgcore/src/pkg_file_plan.adb#Allowed_Path|pkgcore/tests/run_file_replay_tests.adb|
|REQ-009|状態読取の安定性|implemented-unvalidated|ADR-0008|assurance/runtime/mc_atomic.adb#Read<br>pkgcore/runtime/pkg_recovery_audit.adb#Inspect|pkgcore/tests/run_file_engine_tests.adb<br>assurance/tests/engineering/test_engineering.py|
|REQ-010|永続化後の成功|partial-integration|ADR-0001|assurance/runtime/mc_fs.adb#Sync<br>pkgcore/runtime/pkg_file_engine.adb#Emit|pkgcore/tests/run_file_engine_tests.adb|
|REQ-011|Isolationの範囲|partial-integration|ADR-0001|pkgcore/runtime/pkg_quiescent_engine.ads|pkgcore/tests/run_file_engine_tests.adb|
|REQ-012|外部効果の結果不明|partial-integration|ADR-0010|statecore/src/state_operation.ads<br>statecore/runtime/state_executor.ads|statecore/tests/run_v2_state_tests.adb|
|REQ-013|独立アンカー|partial-integration|ADR-0012|assurance/runtime/mc_checkpoint_store.ads|assurance/tests/run_checkpoint_io_tests.adb|
|REQ-014|全対象停止の確認|partial-integration|ADR-0011|assurance/src/mc_stop_barrier.ads<br>statecore/runtime/state_barrier_store.ads|assurance/tests/run_stop_barrier_tests.adb|
|REQ-015|クラスタの所有権|partial-integration|ADR-0011|statecore/src/state_cluster_safety.ads<br>statecore/src/state_failover.ads|statecore/tests/run_cluster_resilience_tests.adb|
|REQ-016|復旧予算|partial-integration|ADR-0014|statecore/src/state_healing.ads<br>statecore/runtime/state_healing_journal.ads|statecore/tests/run_healing_tests.adb<br>statecore/tests/run_healing_io_tests.adb|
|REQ-017|設定/ネットワークの回復|partial-integration|ADR-0019|statecore/src/state_network_change.ads<br>statecore/runtime/state_network_controller.ads|statecore/tests/run_platform_tests.adb|
|REQ-018|起動候補|partial-integration|ADR-0019|statecore/src/state_boot_assessment.ads|statecore/tests/run_platform_tests.adb|
|REQ-019|業務データの復元|partial-integration|ADR-0013|assurance/src/mc_backups.ads<br>pkgcore/src/pkg_retention_batch.ads|assurance/tests/run_backup_contract_tests.adb<br>pkgcore/tests/run_retention_batch_tests.adb|
|REQ-020|署名と作用範囲|partial-integration|ADR-0012|assurance/src/mc_authorization.ads<br>assurance/runtime/mc_ingress.ads|assurance/tests/run_ingress_tests.adb|
|REQ-021|証拠の層と鮮度|implemented-unvalidated|ADR-0016|assurance/src/mc_qualification.ads<br>assurance/ci/run-engineering-checks.py|assurance/tests/run_qualification_tests.adb<br>assurance/tests/engineering/test_engineering.py|
|REQ-022|要求からの追跡|implemented-unvalidated|ADR-0017|assurance/ci/engineering.py#validate|assurance/tests/engineering/test_engineering.py|
|REQ-023|全テストmain登録|implemented-unvalidated|ADR-0017|assurance/ci/engineering.py#validate|assurance/tests/engineering/test_engineering.py|
|REQ-024|正確なソース在庫|implemented-unvalidated|ADR-0017|assurance/ci/engineering.py#inventory|assurance/tests/engineering/test_engineering.py|
|REQ-025|共有profile移行|partial-integration|ADR-0015|assurance/ci/refresh-contract.py<br>assurance/ci/check-contract.sh|assurance/ci/cross-repository.sh<br>assurance/tests/engineering/test_engineering.py|
|REQ-026|証明境界|partial-integration|ADR-0003|pkgcore/src/pkg_file_replay.ads<br>assurance/proof.gpr|pkgcore/tests/run_file_replay_tests.adb|
|REQ-027|緊急制御|partial-integration|ADR-0012|assurance/src/mc_control.ads<br>assurance/runtime/mc_control_io.ads|assurance/tests/run_control_tests.adb|
|REQ-028|境界付き入力|implemented-unvalidated|ADR-0018|assurance/runtime/mc_fs.adb#Open_New_Or_Lock<br>assurance/ci/engineering.py#read_regular|assurance/tests/run_recovery_storage_tests.adb<br>assurance/tests/engineering/test_engineering.py|
|REQ-029|秘密と診断|partial-integration|ADR-0018|pkgcore/app/pkg_recoveryctl.adb|assurance/tests/engineering/test_engineering.py|
|REQ-030|RTO/RPO|specification-only|ADR-0020|設計のみ|適格化未実施|
|REQ-031|restart authority|partial-integration|ADR-0002|statecore/src/state_service_catalogue.ads|statecore/tests/run_platform_tests.adb|
|REQ-032|ディストリビューション全面管理の完了条件|specification-only|ADR-0020|設計のみ|適格化未実施|
