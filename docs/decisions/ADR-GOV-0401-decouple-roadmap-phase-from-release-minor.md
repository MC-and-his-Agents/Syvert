# ADR-GOV-0401 Decouple Roadmap Phase From Release Minor

## 关联信息

- Issue：`#401`
- item_key：`GOV-0401-decouple-roadmap-phase-from-release-minor`
- item_type：`GOV`
- release：`v1.x`
- sprint：`2026-S24`

## Status

Accepted

## Decision

Treat roadmap capability-track naming and release minor numbering as explicitly decoupled governance axes.

This decision requires:

- `docs/roadmap-v1-to-v2.md` to stop using numbered `Phase N` capability headings.
- `docs/process/version-management.md` to state that capability track, GitHub `Phase`, FR, and Work Item cannot implicitly bind to `MINOR`.
- `scripts/version_guard.py` and governance tests to reject reintroduction of numbered roadmap phase headings and loss of track-versus-minor semantics.
- Existing `v1.1.0` and `v1.2.0` published release truth to remain unchanged as historical releases, not future mapping rules.

## Rationale

The roadmap already states that `v1.x` is not a countdown from `v1.1.0` to `v2.0.0`, and that capability streams define dependency ordering rather than release numbering. Keeping numbered `Phase N` headings leaves a persistent inference path for agents and reviewers to misread roadmap structure as a minor-version sequence. The safer governance fix is to rename the roadmap headings, strengthen the version rule, and add a mechanical guard.

## Consequences

- Future roadmap work cannot justify `Phase N -> v1.N` by title shape alone.
- Release numbering stays a closeout decision, not a roadmap-heading side effect.
- Historical `v1.1.0` and `v1.2.0` releases remain published truth without being elevated into a standing mapping convention.
