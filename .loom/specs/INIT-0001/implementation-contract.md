# Implementation Contract

## Work Item

- Item: INIT-0001 / Syvert Work Item #258
- Execution Entry: PR #259 on branch `issue-258-loom-official-adoption`

## Approved Spec

- Spec Path: `.loom/specs/INIT-0001/spec.md`
- Spec Review Entry: `.loom/reviews/INIT-0001.spec.json`

## Implementation Scope

- In Scope:
  - `.loom` carrier, companion, shadow, work item, status, review, spec, and vendored runtime.
  - Syvert docs that declare Loom consumption boundary.
  - Syvert governance gate structural coverage for `.loom/**`.
  - Regression tests for GitHub parser and Loom carrier guard.
- Out Of Scope:
  - Removing Syvert guardian or integration contract.
  - Replacing Syvert release/sprint/item_key semantics.
  - De-vendoring `.loom/bin` before Loom supports external-runtime companion.

## Validation Plan

- Automated Checks:
  - py_compile for `.loom/bin` and Syvert scripts.
  - docs guard, workflow guard, governance gate, and spec guard.
  - governance unittest discovery.
  - `python3 .loom/bin/loom_init.py verify --target .`
  - `python3 .loom/bin/loom_flow.py governance-profile status --target .`
  - `python3 .loom/bin/loom_flow.py runtime-parity validate --target .`
  - `python3 .loom/bin/loom_flow.py shadow-parity --target . --blocking`
- Manual Verification:
  - Guardian review.
  - Controlled merge and post-merge main-truth closeout.

## Risks And Rollback

- Risks:
  - Vendored runtime can drift from upstream Loom.
  - `.loom/**` scope can admit runtime changes unless structural gates stay active.
  - GitHub host reads can fail due auth or host signal drift.
- Rollback Boundary:
  - Revert PR #259 to remove the carrier, or follow up with external-runtime companion migration while preserving Syvert-owned residue.

## Host Binding

- Pull Request: #259
- Reviewed Head: managed by `.loom/reviews/INIT-0001.json` and `.loom/reviews/INIT-0001.spec.json`
