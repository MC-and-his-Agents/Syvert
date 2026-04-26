# Syvert Loom Companion

This companion lets Loom read Syvert governance surfaces without replacing Syvert repo-native governance.

Loom owns the reusable governance runtime and GitHub profile semantics. Syvert keeps product, release/sprint, guardian, integration contract, and adapter/runtime rules as repo-owned residue.

## Runtime Boundary

- Loom core consumed: Work Item admission, gate chain, status control plane, maturity upgrade, closeout/reconciliation, shadow parity boundary.
- GitHub profile consumed: Phase / FR / Work Item / PR / merge commit binding, parent/sub-issue tree, ProjectV2 budget guard, host drift reconciliation.
- Syvert residue retained: product roadmap, release/sprint/item_key context, guardian implementation, integration contract fields, adapter/runtime resource lifecycle.

## Entry Points

- Repo interface: `.loom/companion/repo-interface.json`
- Interop contract: `.loom/companion/interop.json`
- Loom bootstrap result: `.loom/bootstrap/init-result.json`
- Loom runtime: `.loom/bin/loom_flow.py`
