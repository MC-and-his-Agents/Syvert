# CHORE-0371 v1.1 Contract Consumer Migration

## 关联信息

- Issue: #371
- item_key: CHORE-0371-v1-1-contract-consumer-migration
- item_type: CHORE
- release: v1.1.0
- sprint: 2026-S23
- active 收口事项: CHORE-0371-v1-1-contract-consumer-migration
- 状态: active
- 关联 spec: docs/specs/FR-0368-operation-taxonomy-contract

## Metadata

- Parent FR: #368
- Phase: #367
- Class: implementation
- Workspace: `/Users/mc/code/worktrees/syvert/issue-371-v1-1-contract-consumers-taxonomy-carrier`
- Branch: `issue-371-v1-1-contract-consumers-taxonomy-carrier`

## Objective

Migrate existing Adapter and Provider contract consumers to read the stable operation slice from the operation taxonomy runtime carrier, without changing v1.0.0 behavior.

## Scope

Included:

- Derive legacy approved slice exports from `stable_operation_entry()`.
- Keep compatibility exports for existing tests and documentation references.
- Preserve the only accepted stable contract: `content_detail / content_detail_by_url / url / hybrid`.
- Add consumer regression tests proving proposed candidates cannot pass requirement, offer, or compatibility decision validation.

Excluded:

- Changing resource profile matching semantics.
- Promoting proposed candidate families to executable runtime operations.
- Adding provider selector, fallback, marketplace, platform-private object, or workflow semantics.

## Validation

Required before merge:

- `python3 -m unittest tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard tests.runtime.test_real_provider_sample_evidence tests.runtime.test_operation_taxonomy_consumers`
- `python3 -m unittest tests.runtime.test_operation_taxonomy tests.runtime.test_real_adapter_regression tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_cli_http_same_path`
- `python3 scripts/spec_guard.py --mode ci --all`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/governance_gate.py --mode ci --base-sha <base> --head-sha <head> --head-ref issue-371-v1-1-contract-consumers-taxonomy-carrier`

## 最近一次 checkpoint 对应的 head SHA

- Initial branch checkpoint: `952dd7117b65f20b4df53692d03a669f0678eb7c`
- Current live PR head is governed by PR `headRefOid` and guardian merge gate after PR creation.

## Risks

- Risk: derived constants could silently change existing v1.0.0 behavior.
  - Mitigation: consumer tests continue to assert baseline success and proposed candidate rejection.
- Risk: compatibility decision could return `matched` for proposed candidates.
  - Mitigation: added regression expects `invalid_contract` and empty matched profiles.

## Rollback

Revert the PR that modifies the three consumer modules and adds `tests/runtime/test_operation_taxonomy_consumers.py`. The taxonomy carrier from #370 remains intact.
