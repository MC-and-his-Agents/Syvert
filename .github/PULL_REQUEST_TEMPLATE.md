## 摘要

- PR Class: `{{PR_CLASS}}`
- 变更目的：
- 主要改动：

## Issue 摘要

{{ISSUE_SUMMARY}}

## 关联事项

- Issue: {{ISSUE}}
- item_key: `{{ITEM_KEY}}`
- item_type: `{{ITEM_TYPE}}`
- release: `{{RELEASE}}`
- sprint: `{{SPRINT}}`
- Closing: {{CLOSING}}

## Review Artifacts

- Active exec-plan:
- Governing spec / bootstrap contract:
- Review artifact:
- Validation evidence:

## 风险

- 风险级别：`{{RISK_LEVEL}}`
- 审查关注：

## 验证

{{VALIDATION_SUGGESTION}}

## integration_check

Canonical integration contract source: `scripts/policy/integration_contract.json` / `scripts/integration_contract.py`

- integration_touchpoint（`none` / `check_required` / `active` / `blocked` / `resolved`）:
- shared_contract_changed（`no` / `yes`）:
- integration_ref:
- external_dependency（`none` / `syvert` / `webenvoy` / `both`）:
- merge_gate（`local_only` / `integration_check_required`）:
- contract_surface（`none` / `execution_provider` / `ids_trace` / `errors` / `raw_normalized` / `diagnostics_observability` / `runtime_modes`）:
- joint_acceptance_needed（`no` / `yes`）:
- integration_status_checked_before_pr（`no` / `yes`）:
- integration_status_checked_before_merge（`no` / `yes`）:

补充说明：

- 按 canonical contract 填写并校验 `integration_check`。
- `merge_gate` 的触发条件、`integration_ref` 的可核查格式与归一规则，以 canonical contract 为准。
- `integration_check_required` 的最终复核发生在 merge gate，不要把 merge-time recheck 写成 reviewer 已完成动作。

## 回滚

- 回滚方式：{{ROLLBACK}}

## Loom Runtime Locator

- Loom companion: `.loom/companion/README.md`
- Loom runtime: `.loom/bin/loom_flow.py`

## Summary

- Loom-compatible summary: see `## 摘要`.

## Validation

- Loom-compatible validation: see `## 验证`.

## Risks And Follow-ups

- Loom-compatible risks and follow-ups: see `## 风险`.

## Related Work

- Loom-compatible related work: see `## 关联事项`.
