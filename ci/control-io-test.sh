#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
umask 077
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
D=$(mktemp -d "${TMPDIR:-/tmp}/mc-control-io.XXXXXXXX")
# Retained for diagnosis. These are test-only ephemeral signing keys; never import
# them into a real site's authority set. Directory mode is 0700.
printf 'Isolated test workspace: %s\n' "$D"
mkdir "$D/policy" "$D/ops" "$D/security" "$D/checkpoint"
./build/test-bin/run_control_io_tests "$D/policy" "$D/ops" "$D/security"
./build/test-bin/run_checkpoint_io_tests "$D/checkpoint"
