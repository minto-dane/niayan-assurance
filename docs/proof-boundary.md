> Current-edition addendum: pure SPARK targets now also include MC_Control, MC_Control_Codec, MC_Checkpoint, MC_Backups, Pkg_Retention_Batch, State_Readmission, State_Disaster and State_Etcd_Limits. MC_Control_IO, MC_Checkpoint_Store, controlctl and new etcd stores remain SPARK_Mode Off boundaries. Source presence is NOT a formal proof. See assured-traceability.md and checkpoints.ja.md for mandatory external anchors and validators.

> Edition note: this document describes inherited v2 components. For the current resilience extension, implementation limits and evidence, start with `assurance/docs/resilience.ja.md` in the source bundle. Earlier qualification counts do not apply to the new sources.

# Proof boundary — source release, not a proof certificate

Pure SPARK targets: codecs, request binding, replay rules, witness matching, bounded path/number/JSON/property profiles,
RPM header/value/dependency/file-plan models, node availability budget, configuration merge, and state transitions.
GNATprove has NOT run on this expanded release. Contracts, finite bounds and assertions are proof obligations, not proof results.

Explicit SPARK_Mode=>Off targets: persistent I/O, Linux ABI, process execution, key storage, crypto/native parsers,
network retrieval, administrative CLIs, native systemd/Pacemaker/etcd adapters and orchestration of I/O.
The real filesystem executor is not formally verified end to end. Proving the pure plan/model does not prove its I/O implementation.

TCB / explicit assumptions:

* Linux kernel, glibc/ABI, Ada compiler/runtime, filesystem durability semantics, storage device honoring flushes.
* libsodium (Ed25519), libarchive, libcurl/TLS stack/trust store, libxml2 and all their transitive dependencies.
* Pinned ELF commands and their dynamic libraries/configuration. ELF pinning avoids PATH/script substitution; it does not make a command a verified program.
* Protected directories, no malicious privileged/same-owner out-of-band writes, working local clock/boot identity, independent trust state preservation.
* Signed topology/reservation/health/isolation facts issued by a properly implemented and operated site observer.
* Existing etcd consensus, namespace RBAC, transport trust, protection against restoration of stale fencing state.
* Pacemaker ownership/fencing policy and application-specific data consistency requirements.

Safety vs liveness: unknown or unsupported conditions stop new effects. A stopped update is not automatically a stopped healthy workload.
A blocked budget is not automatically released to improve liveness. No lease expiration is interpreted as successful physical fencing.

Future proof work: model filesystem and persistent state transitions including interruptions of recovery, connect that model to each FFI result;
verify uniqueness/order of effects and before/after image publication; prove protocol/model compatibility across separately built releases.
Compiler-to-machine-code verification is not provided. No CakeML/HOL4 implementation is claimed.
