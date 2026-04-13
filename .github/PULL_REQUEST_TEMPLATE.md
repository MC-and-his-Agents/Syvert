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

## 风险

- 风险级别：`{{RISK_LEVEL}}`
- 审查关注：

## 验证

{{VALIDATION_SUGGESTION}}

## integration_check

- integration_applicable（`yes` / `no`）:
- integration_ref:
- shared_contract_changed（`yes` / `no`）:
- external_dependency（`none` / `syvert` / `webenvoy` / `both`）:
- contract_surface（`none` / `execution_provider` / `ids_trace` / `errors` / `raw_normalized` / `diagnostics_observability` / `runtime_modes`）:
- joint_acceptance_needed（`yes` / `no`）:
- integration_status_checked_before_pr（`yes` / `no`）:
- integration_status_checked_before_merge（`yes` / `no`）:

补充说明：

- `integration_applicable=yes` 时，`integration_ref` 不得为空。
- `shared_contract_changed=yes` 或 `external_dependency != none` 时，当前事项的 `merge_gate` 必须收口为 `integration_check_required`。
- 进入 merge gate 前必须再次核对 `integration_ref` 对应 integration issue / project item 的当前状态与依赖关系。

## 回滚

- 回滚方式：{{ROLLBACK}}
