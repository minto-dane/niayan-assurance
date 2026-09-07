# Coordination integrity — requirement / implementation / evidence

All Ada tests below are **written, not compiled or executed in this environment**.
Pure SPARK annotations are not proof results. Independent reference tests are not refinement proofs.

| ID | Requirement | Implementation | Ada regression test | Remaining assumption |
|---|---|---|---|---|
| CI-01 | response from provisioned cluster only | State_Etcd_Wire.Read_Response/Write_Response | run_etcd_wire_tests | isolated client credentials, trusted endpoint; response check is post-dispatch |
| CI-02 | reject stale revisions and contradictory absence | State_Etcd_Wire.Read_Response | run_etcd_wire_tests | persistent independently provided minimum revision |
| CI-03 | compare guard and target in one txn | State_Etcd_Wire.Write_Request + State_Etcd.Compare_And_Swap | run_etcd_wire_tests request byte checks | actual pinned etcdctl/server behavior, protected guard writer |
| CI-04 | malformed write acknowledgement is UNKNOWN | State_Etcd_Wire.Write_Response | run_etcd_wire_tests | command-runner side-effect classification; reconciliation by caller |
| CI-05 | all consumers, not a majority | MC_Stop_Barrier.Ready/Seal | run_stop_barrier_tests (8 subsets, single node) | complete authenticated inventory |
| CI-06 | node agent cannot claim fencing authority | MC_Stop_Barrier_Auth.Verify | run_stop_vector_tests; cross-repository.sh | key custody, qualified independent fence observer |
| CI-07 | fresh negative report revokes prior seal | MC_Stop_Barrier.Observe | run_stop_barrier_tests | reliable delivery and durable enforcement; not a perfect failure detector |
| CI-08 | no replay/future/other boot/old guard acceptance | MC_Stop_Barrier.Observe | run_stop_barrier_tests; run_stop_vector_tests | receiver-local authenticated observation bridge |
| CI-09 | concurrent receipt update not overwritten | State_Barrier_Store | no live etcd test executed | correct independent Authorize, latest-state CAS, external isolation |
| CI-10 | actual file engine checks quiescence | Pkg_Quiescent_Engine.Engine | compile-all wiring only, no native integration execution | integration opts in; qualified observer + original permission policy |
| CI-11 | duplicated backup position is not a new restore point | Pkg_Retention_Batch.Plan | run_retention_batch_tests | authenticated catalog, trusted timestamp interval |
| CI-12 | repeated copying cannot inflate recovery span | Pkg_Retention_Batch.Plan | run_retention_batch_tests | semantic meaning of data position and completed time |
| CI-13 | special source files rejected before hashing | each ci/check-contract.sh | real shell negative tests (FIFO, manifest FIFO, Unix socket etc) | fixed private workspace, no concurrent untrusted writer |
| CI-14 | independent binaries reject malformed contracts | MC_CLI inspection commands | cross-repository.sh | builds/toolchain not available here |

Current independent checks: evidence/independent-checks.json.
Current shell/source/build-entry checks and failed tool invocations: evidence/source-checks.json.
No live etcd, physical fencing, powercut, or GNATprove evidence is implied by these files.
