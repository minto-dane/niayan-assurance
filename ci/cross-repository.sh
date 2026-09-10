#!/bin/sh
# SPDX-License-Identifier: BSD-3-Clause
# Strict source-lock + independent executable conformance. Not a live cluster test.
set -eu
umask 077
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
make build test
make -C ../pkgcore build test
make -C ../statecore build test
make -C ../controlcore build test
make -C ../configcore build test
make -C ../resolvercore build test
make -C ../capsulecore build test
./build/bin/assure audit-vendors ../pkgcore ../statecore ../controlcore ../configcore ../resolvercore ../capsulecore
gprbuild -p -P integration.gpr
./build/integration-bin/run_integration_tests
D=$(mktemp -d "${TMPDIR:-/tmp}/mc-contract.XXXXXXXX")
cleanup() { rm -f -- "$D/observed.hex" "$D/rejection.log"; rmdir -- "$D"; }
trap cleanup EXIT HUP INT TERM
for executable in ./build/bin/assure ../pkgcore/build/bin/pkgctl ../statecore/build/bin/statectl ../controlcore/build/bin/missionctl ../configcore/build/bin/configctl ../resolvercore/build/bin/resolverctl ../capsulecore/build/bin/capsulectl; do
    "$executable" contract-profile > "$D/observed.hex"
    cmp contract-profile.hex "$D/observed.hex"
    "$executable" contract-vector > "$D/observed.hex"
    cmp fixtures/golden-header.hex "$D/observed.hex"
    "$executable" recovery-contract-vector > "$D/observed.hex"
    cmp fixtures/golden-health.hex "$D/observed.hex"
    "$executable" verify-health-report fixtures/golden-health.bin fixtures/health.sig fixtures/test-observer.pub
    for invalid in fixtures/health-reserved.bin fixtures/health-unknown-kind.bin fixtures/health-invalid-boolean.bin fixtures/health-truncated.bin; do
        if "$executable" check-health-frame "$invalid" > "$D/rejection.log" 2>&1; then
            echo 'FAIL: invalid health contract accepted' >&2; exit 1
        fi
    done
    if "$executable" verify-health-report fixtures/golden-health.bin fixtures/health-wrong-domain.sig fixtures/test-observer.pub > "$D/rejection.log" 2>&1; then
        echo 'FAIL: cross-domain health signature accepted' >&2; exit 1
    fi
    if "$executable" verify-health-report fixtures/golden-health.bin fixtures/health.sig fixtures/test-authority.pub > "$D/rejection.log" 2>&1; then
        echo 'FAIL: requester key accepted as observer' >&2; exit 1
    fi
    "$executable" check-stop-policy fixtures/stop-v1/policy.bin
    "$executable" check-stop-state fixtures/stop-v1/sealed-state.bin
    for n in 1 2 3; do
        "$executable" verify-stop-evidence fixtures/stop-v1/policy.bin "fixtures/stop-v1/node-$n.bin" "fixtures/stop-v1/node-$n.sig"
    done
    "$executable" verify-stop-evidence fixtures/stop-v1/policy.bin fixtures/stop-v1/fence-1.bin fixtures/stop-v1/fence-1.sig
    for sig in wrong-domain.sig wrong-role.sig; do
        if "$executable" verify-stop-evidence fixtures/stop-v1/policy.bin fixtures/stop-v1/node-1.bin "fixtures/stop-v1/$sig" > "$D/rejection.log" 2>&1; then
            echo 'FAIL: invalid stop acknowledgement signature accepted' >&2; exit 1
        fi
    done
    for bad in evidence-reserved.bin evidence-boolean.bin; do
        if "$executable" verify-stop-evidence fixtures/stop-v1/policy.bin "fixtures/stop-v1/$bad" "fixtures/stop-v1/$bad.sig" > "$D/rejection.log" 2>&1; then
            echo 'FAIL: signed noncanonical stop evidence accepted' >&2; exit 1
        fi
    done
    if "$executable" check-stop-policy fixtures/stop-v1/policy-reserved.bin > "$D/rejection.log" 2>&1; then
        echo 'FAIL: noncanonical stop policy accepted' >&2; exit 1
    fi
    if "$executable" check-stop-state fixtures/stop-v1/state-reserved.bin > "$D/rejection.log" 2>&1; then
        echo 'FAIL: noncanonical stop state accepted' >&2; exit 1
    fi
    "$executable" verify-envelope fixtures/request-header.bin fixtures/request-body.bin fixtures/request.sig fixtures/test-authority.pub
    for invalid in fixtures/unknown-major.bin fixtures/legacy-v1-header.bin fixtures/reserved-flag.bin fixtures/truncated-header.bin; do
        if "$executable" check-header "$invalid" > "$D/rejection.log" 2>&1; then
            echo 'FAIL: a malformed/version-incompatible header was accepted' >&2
            exit 1
        fi
    done
done
# Unauthenticated legacy direct-mutation commands must remain blocked.
# Authenticated workers have real effects and are not exercised by this loop.
for executable in ../pkgcore/build/bin/pkgctl ../statecore/build/bin/statectl; do
    code=0
    "$executable" apply > "$D/rejection.log" 2>&1 || code=$?
    test "$code" -eq 78 || { echo 'FAIL: mutation gate not closed' >&2; exit 1; }
done
printf '%s
' 'Cross-repository conformance passed; live adapters and release qualification NOT established.'
