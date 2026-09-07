# Property-to-implementation traceability (NOT a proof report)

| Property | Implementation | Ada test entry | This environment |
|---|---|---|---|
| Tighten/resume separate authority, strict epochs | MC_Control | run_control_tests | source present; not compiled/proved |
| Canonical multi-signer request, domain separation | MC_Control_Codec/MC_Authentic | run_control_vector_tests | independent public fixture signature checks only |
| Durable signed state + exact acknowledged retry | MC_Control_IO | run_control_io_tests | Ada not executed |
| Missing latch does not fall back | MC_Gate/MC_Control_IO | run_control_io_tests | source wiring inspected; not executed |
| Exact external anchor, replay floors | MC_Checkpoint | run_control_tests | discrete reference model only |
| Lost anchor response/current reconciliation | MC_Checkpoint_Store | run_checkpoint_io_tests | Ada not executed; test anchor is in-process only |
| Parent closure/tested backup set | MC_Backups | run_backup_contract_tests | independent reference cases |
| Whole-batch surviving recovery points | Pkg_Retention_Batch | run_retention_batch_tests | independent reference cases |
| Isolation/read-only rejoin/soak | State_Readmission | run_readmission_tests | Ada not executed |
| New incarnation/epoch/watch reset/admission | State_Disaster | run_disaster_tests | independent guard cases; not live restore |
| Compare revision + exact digest persistence | State_Readmission_Store/State_Disaster_Store | site integration required | not connected to live etcd |
| 8192 byte payload/double Base64/logical limit | State_Etcd_Limits/State_Etcd | run_etcd_limit_tests | independent Base64 size tests |
| Definite EEXIST cleans only own staging name | MC_Atomic | file engine/control IO tests | isolated Python renameat2 probe, not Ada |

MC_Release.Build_Qualified remains False. New evidence enum items require threshold/control, anchor, backup, readmission, disaster rehearsal, retention race and etcd limit qualification in addition to all prior gates. A Boolean array alone is not an authenticated qualification record.
