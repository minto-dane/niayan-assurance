> Edition note: this document describes inherited v2 components. For the current resilience extension, implementation limits and evidence, start with `assurance/docs/resilience.ja.md` in the source bundle. Earlier qualification counts do not apply to the new sources.

# CI policy v2

Source locks are mandatory; adding an unlisted shared file is a failure, not an ignored extension.
Run compile-all, all unit/runtime tests, independent CLI conformance, GNATprove flow/proof, source and target-dependency review.
Record toolchain and OS/native-library versions and hashes per run. No unlocked dependency auto-download is performed by these Makefiles.
No private keys, cluster credentials or production state belong in CI fixtures.

A passing source test is not production qualification. Separate gates cover target architecture/ABI, native tool profiles,
file system fault behavior, actual HA/fencing, witness issuer correctness, data migrations, backup restore, operational signing/revocation.
Do not continue a pipeline after a failed signature, unknown schema, compile, test or proof command.
Output logs must be reviewed/redacted before publication; native tool output may contain infrastructure details.
