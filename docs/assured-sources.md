# Primary technical references consulted

Access date: 2026-09-06. These explain existing mechanisms, not certification of this code.

- etcd disaster recovery: https://etcd.io/docs/v3.5/op-guide/recovery/ — revision restoration, revision bump and compaction considerations for watch clients. This code does NOT invoke etcdutl or claim a verified etcd restore implementation.
- ClusterLabs fencing/SBD: https://projects.clusterlabs.org/w/fencing/using_sbd_with_pacemaker/ — fencing authority and watchdog/isolation boundaries. A typed Boolean in an adapter must originate from a real checked observation.
- The Update Framework specification: https://theupdateframework.github.io/specification/latest/ — threshold signatures, distinct keys and trust freshness. MC-CONTROL is a separate protocol, NOT TUF and NOT an implementation of TUF root rotation.
- etcd maintenance: https://etcd.io/docs/v3.5/op-guide/maintenance/ — compaction/defragmentation are separate from snapshot restore. The generic checkpoint store does not compact existing application journals.

Canonical ABI of this edition is specified by source codecs, locked source profile, public test vectors and accompanying documents. No external standard is claimed to validate application-specific backup positions, role independence or business health.
