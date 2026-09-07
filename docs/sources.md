> Edition note: this document describes inherited v2 components. For the current resilience extension, implementation limits and evidence, start with `assurance/docs/resilience.ja.md` in the source bundle. Earlier qualification counts do not apply to the new sources.

# Primary implementation references

These are interface/design references, not evidence that this implementation was compiled, tested on the referenced platform, or proved.

- Linux openat2: https://man7.org/linux/man-pages/man2/openat2.2.html
- Linux fsync and directory persistence: https://man7.org/linux/man-pages/man2/fsync.2.html
- Linux renameat2: https://man7.org/linux/man-pages/man2/rename.2.html
- RPM tags: https://rpm.org/docs/4.20.x/manual/tags.html
- RPM boolean dependencies: https://rpm-software-management.github.io/rpm/manual/boolean_dependencies.html
- rpmkeys: https://rpm.org/docs/4.20.x/man/rpmkeys.8
- libarchive filters: https://manpages.debian.org/testing/libarchive-dev/archive_read_filter.3.en.html
- libcurl SSL peer/hostname checking: https://curl.se/libcurl/c/CURLOPT_SSL_VERIFYPEER.html and https://curl.se/libcurl/c/CURLOPT_SSL_VERIFYHOST.html
- libxml2 reader API: https://gnome.pages.gitlab.gnome.org/libxml2/html/xmlreader_8h.html
- systemctl: https://www.freedesktop.org/software/systemd/man/systemctl.html
- ClusterLabs fencing: https://clusterlabs.org/projects/pacemaker/doc/3.0/Pacemaker_Explained/html/fencing.html
- ClusterLabs XML feature/API revisions: https://projects.clusterlabs.org/w/projects/pacemaker/pacemaker_feature_set/
- etcdctl v3 txn syntax/RPC: https://github.com/etcd-io/etcd/blob/main/etcdctl/README.md
- etcd transactions: https://etcd.io/docs/v3.5/tutorials/how-to-transactional-write/
- GNATprove boundaries: https://docs.adacore.com/spark2014-docs/html/ug/en/usage_scenarios.html

Deployments must record the actual release versions and hashes; “latest documentation” is not a version pin.


## Resilience edition primary references (consulted 2026-09-06)

- etcd API guarantees: https://etcd.io/docs/v3.6/learning/api_guarantees/ — use qualified fresh state and linearizable compare/update; local reference tests do not test etcd.
- Pacemaker fencing: https://clusterlabs.org/projects/pacemaker/doc/3.0/Pacemaker_Explained/html/fencing.html — timeout/unreachability alone is not proof of safe resource retirement.
- systemd.service: https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html — integration versions and Restart/notification semantics must be qualified on site.

These references describe upstream components, not independent validation of this source bundle.
