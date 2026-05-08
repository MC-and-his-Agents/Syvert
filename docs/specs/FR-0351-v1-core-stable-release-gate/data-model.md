# FR-0351 data model

## CoreStableReleaseGateReport

`CoreStableReleaseGateReport` 是 `v1.0.0` release closeout 可以生成或引用的最小报告形状。本文只冻结语义，不要求本事项实现代码。

字段：

- `release`：固定为 `v1.0.0`。
- `gate_version`：gate checklist 版本，初始值为 `FR-0351`.
- `overall_status`：`pass` 或 `fail`。
- `gate_items`：`CoreStableReleaseGateItem` 列表。
- `evidence_refs`：指向 formal spec、release gate artifact、GitHub issue / PR、Git tag、GitHub Release 或 exec-plan artifact 的引用。
- `generated_at`：生成时间。

## CoreStableReleaseGateItem

字段：

- `gate_id`：gate item 标识。
- `required`：布尔值。
- `status`：`pass`、`fail` 或 `not_applicable`。
- `summary`：简短结论。
- `evidence_refs`：证明该 gate item 的证据引用。
- `failure_reason`：`status=fail` 时必填。
- `not_applicable_reason`：`status=not_applicable` 时必填。

## required gate ids

- `core_adapter_provider_boundary`
- `dual_reference_baseline`
- `third_party_adapter_entry`
- `provider_compatibility_sample`
- `provider_no_leakage`
- `api_cli_same_core_path`
- `release_truth_alignment`
- `application_boundary`
- `packaging_boundary`

## status rules

- 所有 required gate item 必须存在。
- required gate item 不允许使用 `not_applicable` 跳过。
- 任一 required gate item 为 `fail` 时，`overall_status=fail`。
- 任一 required gate item 缺少 evidence refs 时，`overall_status=fail`。
- `provider_compatibility_sample` 的 evidence 必须来自 `v0.9.0` 或之后的真实 provider sample Work Item，不得只引用 `FR-0026` fixture。

