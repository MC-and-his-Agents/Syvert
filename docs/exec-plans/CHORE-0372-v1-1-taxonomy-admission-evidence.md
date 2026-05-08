# CHORE-0372 v1.1 Taxonomy Admission Evidence

## 关联信息

- Issue: #372
- item_key: CHORE-0372-v1-1-taxonomy-admission-evidence
- item_type: CHORE
- release: v1.1.0
- sprint: 2026-S23
- active 收口事项: CHORE-0372-v1-1-taxonomy-admission-evidence
- 状态: active
- 关联 spec: docs/specs/FR-0368-operation-taxonomy-contract

## Metadata

- Parent FR: #368
- Phase: #367
- Class: implementation
- Workspace: `/Users/mc/code/worktrees/syvert/issue-372-v1-1-taxonomy-admission-evidence`
- Branch: `issue-372-v1-1-taxonomy-admission-evidence`

## Objective

Add admission evidence proving future capability candidates can be expressed by the taxonomy while remaining non-executable and unable to pollute the stable `content_detail_by_url` baseline.

## Scope

Included:

- Add fake adapter admission fixtures for proposed `content_search` and `comment_collection`.
- Add contract tests proving proposed entries are admitted as taxonomy expressions but rejected by stable runtime lookup.
- Add compatibility evidence proving proposed candidates cannot produce `matched`.
- Extend platform leakage scan coverage to include `syvert/operation_taxonomy.py`.
- Add forbidden taxonomy field coverage for provider selector, fallback, marketplace, application workflow, and platform-private business object fields.

Excluded:

- Runtime implementation of any proposed candidate family.
- Changes to resource profile matching or Provider selection.
- Release tag, GitHub Release, or published truth writeback. That belongs to #373.

## Validation

Required before merge:

- `python3 -m unittest tests.runtime.test_operation_taxonomy_admission_evidence tests.runtime.test_operation_taxonomy tests.runtime.test_operation_taxonomy_consumers`
- `python3 -m unittest tests.runtime.test_platform_leakage tests.runtime.test_version_gate`
- `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_cli_http_same_path`
- `python3 scripts/spec_guard.py --mode ci --all`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/governance_gate.py --mode ci --base-sha <base> --head-sha <head> --head-ref issue-372-v1-1-taxonomy-admission-evidence`

## 最近一次 checkpoint 对应的 head SHA

- Initial branch checkpoint: `5b715296a1c5e7dd6738454bc804a79f887d3bc6`
- Current live PR head is governed by PR `headRefOid` and guardian merge gate after PR creation.

## Risks

- Risk: adding `operation_taxonomy.py` to platform leakage scanning could expose Core-facing platform literals.
  - Mitigation: taxonomy forbidden field names use platform-neutral terms and tests cover platform-private object rejection generically.
- Risk: proposed admission evidence could be read as runtime delivery.
  - Mitigation: fake manifest explicitly sets runtime delivery, stable lookup, and compatibility match as not allowed.

## Rollback

Revert the PR that adds admission fixtures/tests and platform leakage scan target expansion. Runtime taxonomy and consumer migration from #370/#371 remain intact.
