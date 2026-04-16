# CHORE-0118 Version Gate Result Model

本文件冻结 `#118` 已落地的统一 version gate / source report 结果模型，供 closeout、release gate 与后续 `FR-0007` 子事项实现直接消费。

本文件不改写 [`spec.md`](../../specs/FR-0007-release-gate-and-regression-checks/spec.md) 的 requirement；它只把当前实现已落地且需要被下游稳定消费的结果字段、来源归因与 fail-closed 语义显式化。

## 1. top-level version gate result

统一入口 `orchestrate_version_gate()` 输出一个 JSON-serializable mapping，字段如下：

- `version`
  - 非空字符串
  - 缺失或空值必须 fail-closed
- `reference_pair`
  - 非空字符串列表
  - 对 `v0.2.0`，冻结集合必须为 `xhs` + `douyin`
- `verdict`
  - `pass` / `fail`
- `safe_to_release`
  - `true` / `false`
  - 仅当 `verdict=pass` 时为 `true`
- `summary`
  - 非空字符串摘要
- `source_reports`
  - 固定包含三个 key：
    - `harness`
    - `real_adapter_regression`
    - `platform_leakage`
- `failures`
  - 列表；每项必须包含：
    - `source`
    - `code`
    - `message`
    - `details`

## 2. source report envelope

三类 source report 的外层 envelope 统一为：

- `source`
  - 只允许：
    - `harness`
    - `real_adapter_regression`
    - `platform_leakage`
- `version`
  - 非空字符串
- `verdict`
  - `pass` / `fail`
- `summary`
  - 非空字符串
- `evidence_refs`
  - 非空字符串列表
  - mapping-shaped malformed payload 必须 fail-closed
- `details`
  - mapping
  - 必须包含 `failures`

若 source report 在进入 orchestrator 前已经被判定为 `fail`，其 `details.failures` 不得在编排层被抹除或洗回 `pass`。
synthetic fail-closed source report 也必须保持同一 envelope 形状，并提供确定性的内部 evidence ref。
已经由公开 builder / validator 产出的 failed source report 再次进入 orchestrator 时，语义上相同的 failure 不得重复累计。

## 3. harness source details

`build_harness_source_report()` 消费的是 `FR-0006` 已批准 validator 输出形状：

- `sample_id`
  - 非空字符串
- `verdict`
  - 只允许：
    - `pass`
    - `legal_failure`
    - `contract_violation`
    - `execution_precondition_not_met`
- `reason`
  - 必须是 `{code, message}` 对象
- `observed_status`
  - `success` / `failed` / `null`
- `observed_error`
  - `null` 或 `{category, code, message, details}`

`details` 至少包含：

- `required_sample_ids`
- `observed_sample_ids`
- `validation_results`
- `failures`

进入 orchestrator 的 harness source report 若缺失、malformed、或与 `validation_results` 不一致的 `observed_sample_ids`，必须在 ingress 层 fail-closed，而不是被重建为可信 `pass`。

`evidence_refs` 由 builder 基于已验证 `sample_id` 确定性生成，格式固定为 `harness_validation:<sample_id>`；若输入在规范化阶段已 fail-closed 且无可用 `sample_id`，则改为生成确定性的 synthetic evidence ref，而不是返回空列表。

## 4. real-adapter regression source details

`validate_real_adapter_regression_source_report()` 输入必须包含：

- `version`
- `reference_pair`
- `operation`
- `adapter_results`
- `evidence_refs`
- 若使用 `FR-0004` 批准的 adapter-facing 投影表示，则必须额外携带 `target_type`

`details` 至少包含：

- `reference_pair`
- `operation`
- `target_type`
- `semantic_operation`
- `adapter_results`
- `failures`

对 `v0.2.0`：

- `reference_pair` 必须冻结为 `xhs` + `douyin`
- `semantic_operation` 必须冻结为 `content_detail_by_url`
- 允许的 operation surface 只包括：
  - `operation=content_detail_by_url`，并归一化到 `target_type=url`
  - `operation=content_detail` 且 `target_type=url`
- 每个 adapter 至少一条 success case
- 每个 adapter 至少一条允许失败 case
- 允许失败类别只允许 `invalid_input` / `platform`
- 若输入缺失或 malformed 导致 fail-closed，validator 仍必须返回非空 `evidence_refs`，以便 orchestrator 保留原始 failure code。

## 5. platform leakage source details

`validate_platform_leakage_source_report()` 输入必须包含：

- `version`
- `boundary_scope`
- `verdict`
- `findings`
- `evidence_refs`

`details` 至少包含：

- `boundary_scope`
- `report_verdict`
- `findings`
- `failures`

`details.findings` 必须保留 validator 可再次消费的 finding 形状：`{code, message, boundary, evidence_ref}`，而不是只保留归一化后的 failure envelope。

对 `v0.2.0`，`boundary_scope` 至少覆盖：

- `core_runtime`
- `shared_input_model`
- `shared_error_model`
- `adapter_registry`
- `shared_result_contract`
- `version_gate_logic`
- 若输入缺失或 malformed 导致 fail-closed，validator 仍必须返回非空 `evidence_refs`，以便 orchestrator 保留原始 failure code。

## 6. fail-closed rules

以下任一情况都必须得到 top-level `verdict=fail`：

- 缺 `version`
- 缺 `reference_pair`
- 缺任一 source report
- source report 缺 `evidence_refs`
- source report 缺 `details.failures`
- harness 输入 malformed 或 verdict/观测不一致
- harness source report ingress 缺失或伪造 `observed_sample_ids`
- real regression 使用未冻结 reference pair 或未冻结 operation surface
- real regression 所在版本缺少 formal-spec 冻结的 operation surface
- platform leakage 缺边界、缺 findings 依据或结果不可追溯
- 未知版本缺少 formal-spec 冻结的 reference pair

## 7. compatibility note

本结果模型的兼容面固定在 `syvert.version_gate` 模块级入口上，而不是 `syvert.__init__` 包根导出。
