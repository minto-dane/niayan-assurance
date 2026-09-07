#!/bin/sh
# SPDX-License-Identifier: MIT
# Runtime Ada test, ONLY a private temporary tree. Retain evidence on failure.
set -eu
umask 077
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
D=$(mktemp -d "${TMPDIR:-/tmp}/mc-recovery-storage.XXXXXXXX")
mkdir "$D/state" "$D/store"
printf 'isolated test directory: %s\n' "$D"
./build/test-bin/run_recovery_storage_tests "$D/state" "$D/store"
printf 'Evidence retained: %s\n' "$D"
