# Primary design references (checked 2026-09-06)

These document external APIs, not successful integration tests for this source.

- NetworkManager D-Bus: CheckpointCreate/Destroy/Rollback, exact device scope, nonzero autonomous timeout, ActivateConnection semantics.
  https://networkmanager.dev/docs/api/latest/gdbus-org.freedesktop.NetworkManager.html
- systemd automatic boot assessment: boot counters and successful-boot conditions.
  https://systemd.io/AUTOMATIC_BOOT_ASSESSMENT/
- busctl invocation and structured JSON output.
  https://manpages.debian.org/trixie/systemd/busctl.1.en.html
- systemd resource controls (CPUQuota is relative to one CPU; cgroup dependency).
  https://manpages.debian.org/trixie/systemd/systemd.resource-control.5.en.html
- Fedora build-tool package names for the independent RPM specfiles.
  https://packages.fedoraproject.org/pkgs/gcc/gcc-gnat/
  https://packages.fedoraproject.org/pkgs/gprbuild/gprbuild/
- SPARK proof scope and external assumptions.
  https://docs.adacore.com/spark2014-docs/html/ug/en/usage_scenarios.html

No external source code or proprietary IBM implementation was copied. The three source repositories retain MIT licenses. Distribution binary licensing remains that of its respective publisher.
