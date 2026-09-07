> Edition note: this document describes inherited v2 components. For the current resilience extension, implementation limits and evidence, start with `assurance/docs/resilience.ja.md` in the source bundle. Earlier qualification counts do not apply to the new sources.

# Architecture v2

See implementation-status.ja.md, protocol.md, proof-boundary.md and qualification-gap.md.
Three independently buildable source trees share a pinned protocol/runtime snapshot.
Stateful effects are real Ada runtime code, not formally verified effects. Approval, observation and execution have separate trust roles.
