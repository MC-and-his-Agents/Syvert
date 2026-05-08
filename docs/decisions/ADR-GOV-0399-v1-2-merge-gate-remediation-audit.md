# ADR-GOV-0399 v1.2 Merge Gate Remediation Audit

## 关联信息

- Issue：`#399`
- item_key：`GOV-0399-v1-2-merge-gate-remediation-audit`
- item_type：`GOV`
- release：`v1.2.0`
- sprint：`2026-S24`

## Status

Accepted

## Decision

Treat the #395/#397/#398 merges without a latest guardian `APPROVE` / `safe_to_merge=true` verdict as a confirmed merge-gate violation. The remediation path is a post-closeout audit and metadata hotfix, not an automatic revert or `v1.2.0` tag rewrite.

This remediation must:

- Record the violation in a dedicated GOV Work Item and repository artifact.
- Re-run high-risk runtime / consumer / evidence regressions for #395.
- Reconcile #397/#398 release truth carriers against GitHub PR, tag, and Release facts.
- Fix any repository truth drift found during the audit.
- Fail closed if the #399 PR cannot obtain the normal merge gate.

## Rationale

The violation is procedural, but the highest code-quality risk is concentrated in #395 because it introduced replayable evidence tests and artifacts. The release closeout PRs #397/#398 are metadata-only, so their risk is stale or inconsistent truth carriers rather than runtime behavior. Reverting `v1.2.0` or rewriting the release tag would add release-truth risk unless the audit finds a runtime or published-anchor defect.

## Consequences

- `v1.2.0` remains published unless a later HOTFIX audit proves a release-blocking runtime defect.
- Stale release / sprint / GOV-0396 wording is corrected in #399.
- Future guardian stalls must not be converted into merge permission; they must block merge and be handled by tooling remediation.
