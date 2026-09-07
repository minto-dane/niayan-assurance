# Deterministic protocol test fixtures (NOT production credentials)

Header v2, request body192, envelope416. The signature uses the public RFC8032 test seed
`9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60`. This key is publicly known and must never be trusted by a real deployment.
Private production keys are not included. Native/reference checks below do not run Ada.

Source generator algorithm: big-endian MC_Protocol/MC_Requests layout; Ed25519 signature on
14 ASCII bytes `MCP2-SIGNED-V2`, two NUL, then160-byte header; body hash is SHA-256.
Request IDs/scopes are repeated bytes for deterministic nonproduction fixtures.
