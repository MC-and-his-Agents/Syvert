# GOV-0399 v1.2 Merge Gate Remediation Audit Evidence

## Purpose

This artifact records the post-closeout audit for the v1.2.0 merge-gate violation. It separates process non-compliance from code-quality risk and records the remediation evidence used before opening the #399 PR.

## Violation Scope

Audit command used for each PR:

- `gh pr view <pr> --json number,mergedAt,mergeCommit,reviews,comments,url`

| PR | Merge time | Merge commit | PR review records | Pre-merge provenance |
| --- | --- | --- | --- | --- |
| `#395` | `2026-05-08T15:40:24Z` | `eaec42d70ed432b7334eab19ef5ec5f69544f855` | `reviews=[]` | `https://github.com/MC-and-his-Agents/Syvert/pull/395#issuecomment-4407714609` |
| `#397` | `2026-05-08T15:47:57Z` | `55ad1e5d336907fac6a990bd1742a6e351b92b97` | `reviews=[]` | `https://github.com/MC-and-his-Agents/Syvert/pull/397#issuecomment-4407767118` |
| `#398` | `2026-05-08T15:53:00Z` | `4144d20c9740ada94b0bc213db5842b464b07e4b` | `reviews=[]` | `https://github.com/MC-and-his-Agents/Syvert/pull/398#issuecomment-4407801843` |

Source interpretation:

- #395 provenance comment states the latest `pr_guardian.py merge-if-safe 395 --refresh-review --delete-branch` attempt was stopped after 2+ minutes with 0% CPU/no output, then records merge readiness based on local changed-file review and validation evidence.
- #397 provenance comment records a local release closeout review and merge-ready conclusion; `reviews=[]` shows no GitHub PR review record carrying guardian `APPROVE`.
- #398 provenance comment records a local published-truth review and merge-ready conclusion; `reviews=[]` shows no GitHub PR review record carrying guardian `APPROVE`.
- These source locators are sufficient to independently verify the remediation conclusion: all three PRs were merged without a latest guardian `APPROVE` / `safe_to_merge=true` verdict.

## Audit Surface

| Surface | Files / refs | Result |
| --- | --- | --- |
| `#395` evidence replay | `tests/runtime/test_resource_governance_evidence.py`, `docs/exec-plans/artifacts/CHORE-0392-v1-2-resource-governance-evidence.md` | No runtime blocker found |
| Resource health runtime | `syvert/resource_health.py`, `tests/runtime/test_resource_health.py` | Existing tests cover admission, freshness, context binding, invalidation, co-leased proxy reuse, and fail-closed paths |
| Consumer boundary | Adapter requirement / provider offer / compatibility / no-leakage tests | Regression passed |
| Release truth | `docs/releases/v1.2.0.md`, `docs/sprints/2026-S24.md`, GOV-0396 evidence carrier | Stale phase B wording found and fixed in #399 |

## Quality Risk Findings

### Finding 1: merge gate was bypassed

- Severity：process blocker
- Status：confirmed
- Provenance：`gh pr view` review snapshots plus the pre-merge local-review comments listed in the Violation Scope table.
- Remediation：recorded in #399 and this artifact. #399 PR must not merge without a valid merge gate.

### Finding 2: v1.2.0 release truth retained stale phase B wording

- Severity：metadata correctness
- Status：fixed in #399 for in-scope truth carriers
- Evidence：the release index, sprint index, and GOV-0396 evidence now state that #397/#398 are merged and `#380/#387/#396` are closed completed. The historical GOV-0396 exec-plan still contains phase-B-in-progress wording because #399 cannot edit a foreign exec-plan without violating the current Work Item boundary; this residual is recorded here instead of being silently modified.

### Finding 3: runtime / evidence correctness risk from #395

- Severity：review risk
- Status：no blocker found
- Evidence：383 high-risk tests passed; the #392 evidence artifact is rebuilt from runtime behavior and compared to the JSON snapshot.

## Validation

- `python3 -m unittest tests.runtime.test_resource_governance_evidence tests.runtime.test_resource_health tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_resource_lifecycle tests.runtime.test_resource_lifecycle_store tests.runtime.test_resource_trace_store tests.runtime.test_resource_bootstrap tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_platform_leakage`
  - `Ran 383 tests in 85.205s`
  - `OK`
- `python3 scripts/version_guard.py --mode ci`
  - pass
- `python3 scripts/docs_guard.py --mode ci`
  - pass
- `python3 scripts/spec_guard.py --mode ci --all`
  - pass
- `python3 scripts/workflow_guard.py --mode ci`
  - pass
- `git rev-parse v1.2.0`
  - `1096452ed5ebb41c63005125aa525061c594effb`
- `git rev-parse v1.2.0^{}`
  - `55ad1e5d336907fac6a990bd1742a6e351b92b97`
- `gh release view v1.2.0 --json url,isDraft,isPrerelease,publishedAt,tagName --jq .`
  - non-draft, non-prerelease, published at `2026-05-08T15:49:00Z`

## Decision

Do not rewrite `v1.2.0` tag or GitHub Release based on the current evidence. Complete #399 as a remediation audit and metadata hotfix PR. If subsequent review finds a runtime defect, create a HOTFIX Work Item and handle it as a patch release.
