> Edition note: this document describes inherited v2 components. For the current resilience extension, implementation limits and evidence, start with `assurance/docs/resilience.ja.md` in the source bundle. Earlier qualification counts do not apply to the new sources.

# Wire contract 2.0 — no v1 fallback

Header: 160 bytes, big-endian fields, framing magic MCP1 retained, **major=2, minor=0**.
Byte ranges below are 1-based. Header reserved byte10 must be zero; header size must equal160.
1..4 magic;5..6 major;7..8 minor;9 message kind;10 reserved;11..12 header size;
13..16 body length;17..32 request ID;33..48 cluster;49..64 node;65..80 resource;
81..88 membership epoch;89..96 fencing token;97..104 sequence;105..112 receiver CLOCK_BOOTTIME deadline;
113..128 receiver boot ID;129..160 SHA-256(body).

Kinds 1..10 preserve Plan/Prepare/Apply/Inspect/Recover request/result pairs;11..12 are Contract_Hello/Contract_Result;
13..20 append Commit/Restore/Reconcile/Repair request/result. The authoritative order is MC_Protocol.Message_Kind.

Request body: **192 bytes**, MCO2, u16 version2, action1..9, reserved8;
9..24 transaction;25..56 plan;57..88 contract digest;89..96 expected policy revision;
97..104 base generation;105..136 staged package set;137..168 evidence digest;169..192 allzero.
Actions are Plan,Prepare,Apply,Inspect,Recover,Commit,Restore,Reconcile,Repair.
Prepare/Apply require nonzero stage set. Commit/Restore require nonzero evidence digest.
Worker further binds these fields to the actual decoded plan and locally provisioned policy.

Signature: Ed25519 over **ASCII `MCP2-SIGNED-V2` plus two NUL bytes**, followed by the 160-byte header.
The header authenticates SHA-256 of the exact body. Envelope = header160 + body192 + signature64 =416 bytes.
Trusted public keys come from protected local policy, never from the submitted request.

Witness: 224-byte MCWIT002 statement, plus detached Ed25519 signature64 in witness-0.bin through witness-4.bin.
Domain is u16-big-endian length of `MC-WITNESS-v2`, ASCII domain, then statement.
Fields bind fact kind, cluster/node/root/transaction/receiver boot, plan/contract,epoch/token,issued/expires localboottime.
Kinds:0 reservation;1 quiescence;2 semantic health;3 data backward compatible;4 isolation confirmed.
Freshness and exact scope are checked each time an effect is authorized. A refreshed witness cannot replace the immutable envelope.
A signature authenticates its issuer's assertion, not the real-world truth of health/fencing.

## Policy and administration

`assure challenge` reports local boot identity/time; its transport must be authenticated.
`assure keygen PRIVATE-DIR` creates a local protected seed and public key (no argv secret).
`assure make-policy SPEC OUTPUT-DIR` / `rotate-policy SPEC POLICY-DIR`: strict local owner-controlled provisioning, monotonic serial/epoch/fence.
`assure make-request SPEC KEY-DIR OUTPUT-DIR` creates envelope.bin.
`assure sign-witness SPEC KEY-DIR OUTPUT-DIR` creates/updates a witness. This is NOT an automatic observer.
`assure repair-ledger POLICY-DIR LEDGER-DIR STORE-DIR REQUEST-DIR` requires fresh Repair plus reservation and isolation witness.

Exact specification keys are in MC_Admin. All numbers are canonical nonnegative decimal; IDs/hashes/keys are lowercase canonical hex;
all property files are LF terminated; duplicates/unknown fields are rejected. Unknown version/contracts do not trigger fallback.
No network daemon accepts privileged commands. Spools must be delivered through an independently authenticated, authorized transport with protected final ownership.

## Durable replay

Per receiver/root, requests.log and immutable request-ID.bin records precede effects.
Same ID/sequence/hash returns the stored result without repeating effects. Conflicting or stale requests are denied.
Pending/UNKNOWN only permits explicitly scoped recovery of the same transaction/plan, not an unrelated update.
A node reboot invalidates old boot-bound leases even if all wall clocks match. New signed requests are needed.

Partial final request records can be preserved into CAS and repaired only under the separate authenticated repair path.
The repair records the envelope, tail digest and previous log head first and leaves the operation UNKNOWN.
Do not infer rollback, success, stopped writer or successful fencing from a repaired log.

## Compatibility framework

contracts.source.sha256 pins all shared source files. contracts.lock.json and generated Contract_Lock enumerate the complete allowed file set.
Each repository has a local vendor snapshot; no floating remote import. Cross-repository tests compare executable vectors and rejection behavior.
The source bundle digest is a change-detection lock, not a trust root. Reviewed release signing and a protected distribution mechanism are separate.
Contract change policy: update pure codecs/specs, negative fixtures, per-repo copies, locks and compatibility matrices together; explicitly reapprove policy digest.
Do not automatically widen version ranges or permitted message kinds after a failed handshake.

## Unified-management migration

Existing receiver Open/Observe now rejects missing/empty requests.log. Use the explicit
`missionctl receiver-init` only for a new private directory. Nonempty historical logs
require replay/ownership/profile review. Do not initialize over a missing production ledger.
The controller workflow format is separate: [controller protocol](../../controlcore/docs/protocol.ja.md).
