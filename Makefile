# SPDX-License-Identifier: MIT
# Run as an unprivileged user in an isolated build workspace. No install target.
SHELL := /bin/sh
GPRBUILD ?= gprbuild
GNATPROVE ?= gnatprove
.PHONY: compile-all all build check-tools check-contract test test-build flow prove evidence qualification
all: build
check-tools:
	@command -v $(GPRBUILD) >/dev/null || { echo 'gprbuild is required; NOT QUALIFIED' >&2; exit 78; }
check-contract:
	./ci/check-contract.sh
build: check-tools check-contract
	$(GPRBUILD) -p -P assurance.gpr
test-build: check-tools check-contract
	$(GPRBUILD) -p -P tests.gpr
test: test-build
	./build/test-bin/run_journal_budget_tests
	./build/test-bin/run_request_replay_tests
	./build/test-bin/run_platform_assurance_tests
	./build/test-bin/run_qualification_tests
	./build/test-bin/run_contract_tests
	./build/test-bin/run_ingress_tests
	./build/test-bin/run_v2_tests
	./build/test-bin/run_resilience_contract_tests
	./build/test-bin/run_control_tests
	./build/test-bin/run_backup_contract_tests
	./build/test-bin/run_control_vector_tests tests/fixtures/control-v1
	./build/test-bin/run_stop_barrier_tests
	./build/test-bin/run_stop_vector_tests fixtures/stop-v1
	./build/test-bin/run_cohort_recovery_tests

flow: check-contract
	@command -v $(GNATPROVE) >/dev/null || { echo 'GNATprove missing; proof NOT RUN' >&2; exit 78; }
	mkdir -p build/proof-obj
	$(GNATPROVE) -P proof.gpr -U --mode=flow --checks-as-errors=on --warnings=error
prove: check-contract
	@command -v $(GNATPROVE) >/dev/null || { echo 'GNATprove missing; proof NOT RUN' >&2; exit 78; }
	mkdir -p build/proof-obj
	$(GNATPROVE) -P proof.gpr -U --mode=all --level=4 --checks-as-errors=on --warnings=error --proof-warnings=on --report=statistics
evidence:
	./ci/verify.sh
qualification:
	@echo 'BLOCKED: production installation, adapters, proofs and qualification are incomplete.' >&2
	@exit 78

# Compile every source, including SDK adapters not linked by a CLI main.
compile-all: check-tools check-contract
	$(GPRBUILD) -p -c -u -P assurance.gpr

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
