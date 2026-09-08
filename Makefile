# SPDX-License-Identifier: MIT
# Run as an unprivileged user in an isolated build workspace. No install target.
SHELL := /bin/sh
GPRBUILD ?= gprbuild
GNATPROVE ?= gnatprove
JOBS ?= 1
.PHONY: compile-all all build check-tools check-contract test test-build flow prove evidence qualification
all: build
check-tools:
	@command -v $(GPRBUILD) >/dev/null || { echo 'gprbuild is required; NOT QUALIFIED' >&2; exit 78; }
check-contract:
	./ci/check-contract.sh
build: check-tools check-contract
	$(GPRBUILD) -s -j$(JOBS) -p -P assurance.gpr
test-build: check-tools check-contract
	$(GPRBUILD) -s -j$(JOBS) -p -P tests.gpr
test: test-build
	./ci/test-all.sh

# Shared bounded proof runner, copied into each independent repository.
include ci/proof.mk
evidence:
	./ci/verify.sh
qualification:
	@echo 'BLOCKED: production installation, adapters, proofs and qualification are incomplete.' >&2
	@exit 78

# Compile every source, including SDK adapters not linked by a CLI main.
compile-all: check-tools check-contract
	$(GPRBUILD) -s -j$(JOBS) -p -c -u -P assurance.gpr

.PHONY: test-control-io
# Only fresh private test directories; no live service/cluster mutations.
test-control-io: test-build
	./ci/control-io-test.sh

.PHONY: test-recovery-storage
test-recovery-storage: test-build
	./ci/recovery-storage-test.sh

.PHONY: engineering-check
# Optional bundle-level integration check; the ordinary independent build is unchanged.
engineering-check:
	@test -f ../assurance/ci/engineering.py || { echo 'Seven sibling repositories required for this integration check' >&2; exit 78; }
	python3 ../assurance/ci/engineering.py check
