# CHORE-0370 v1.1 Operation Taxonomy Runtime Carrier

## 关联信息

- Issue: #370
- item_key: CHORE-0370-v1-1-operation-taxonomy-runtime
- item_type: CHORE
- release: v1.1.0
- sprint: 2026-S23
- active 收口事项: CHORE-0370-v1-1-operation-taxonomy-runtime
- 状态: active
- 关联 spec: docs/specs/FR-0368-operation-taxonomy-contract

## Metadata

- Parent FR: #368
- Phase: #367
- Class: implementation
- Workspace: `/Users/mc/code/worktrees/syvert/issue-370-v1-1-operation-taxonomy-runtime-carrier`
- Branch: `issue-370-v1-1-operation-taxonomy-runtime-carrier`

## Objective

Implement the runtime carrier for the FR-0368 Operation Taxonomy Contract without migrating existing Adapter or Provider consumers in this PR.

This Work Item adds a Core-facing taxonomy registry and validator so later Work Items can consume a single stable lookup instead of duplicating approved slice constants.

## Scope

Included:

- Add `syvert/operation_taxonomy.py`.
- Register the single stable v1.0.0 baseline: `content_detail / content_detail_by_url / url / hybrid`.
- Register the v1.x candidate families as `lifecycle=proposed` and `runtime_delivery=false`.
- Provide entry validation, registry validation, stable operation lookup, and fail-closed candidate rejection.
- Add runtime tests for stable lookup, proposed candidate rejection, duplicate operation conflict, invalid lifecycle, operation/capability mismatch, deprecated rejection, and forbidden taxonomy fields.

Excluded:

- Migrating `AdapterCapabilityRequirement`, `ProviderCapabilityOffer`, or `AdapterProviderCompatibilityDecision` consumers. That belongs to #371.
- Promoting any proposed candidate to a stable executable runtime capability.
- Adding provider selector, fallback, marketplace, platform-private object, SDK surface, or upper workflow semantics.

## Contract Inputs

- Formal spec suite: `docs/specs/FR-0368-operation-taxonomy-contract/`
- Stable baseline: `content_detail_by_url` remains the only stable runtime operation.
- Candidate families remain proposed only:
  - `content_search`
  - `content_list`
  - `comment_collection`
  - `creator_profile`
  - `media_asset_fetch`
  - `media_upload`
  - `content_publish`
  - `batch_execution`
  - `scheduled_execution`
  - `dataset_sink`

## Validation

Required before merge:

- `python3 -m unittest tests.runtime.test_operation_taxonomy`
- `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_cli_http_same_path`
- `python3 scripts/spec_guard.py --mode ci --all`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/governance_gate.py --mode ci --base-sha <base> --head-sha <head> --head-ref issue-370-v1-1-operation-taxonomy-runtime-carrier`

Observed local validation:

- `python3 -m unittest tests.runtime.test_operation_taxonomy` passed, 8 tests.
- `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_cli_http_same_path` passed, 79 tests.
- `python3 scripts/spec_guard.py --mode ci --all` passed.
- `python3 scripts/docs_guard.py --mode ci` passed.
- `python3 scripts/workflow_guard.py --mode ci` passed.
- `python3 scripts/governance_gate.py --mode ci --base-sha <base> --head-sha <head> --head-ref issue-370-v1-1-operation-taxonomy-runtime-carrier` passed locally before first PR push.

## 最近一次 checkpoint 对应的 head SHA

- Local implementation checkpoint before PR update: `7b09d3d6741264d00586149e7ae521fc87630494`
- Current live PR head is governed by PR #375 `headRefOid` and guardian merge gate.

## Risks

- Risk: proposed candidate entries could be mistaken for executable runtime operations.
  - Mitigation: stable lookup requires `lifecycle=stable` and `runtime_delivery=true`; proposed entries are explicitly rejected.
- Risk: duplicate operation slices could make compatibility decisions ambiguous.
  - Mitigation: registry validation returns `invalid_contract` on duplicate operation/target/collection slices.
- Risk: #370 could drift into consumer migration.
  - Mitigation: consumer modules are intentionally untouched in this PR; #371 owns migration.

## Rollback

Revert the PR that introduces `syvert/operation_taxonomy.py`, `tests/runtime/test_operation_taxonomy.py`, and this exec-plan. Since no consumer imports are changed in #370, rollback does not alter the v1.0.0 runtime baseline.
