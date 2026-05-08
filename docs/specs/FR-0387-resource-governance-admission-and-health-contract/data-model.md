# FR-0387 数据模型

## CredentialMaterial

- 用途：表达 `account` resource material 中可由 Core 管理、脱敏、注入和健康判定的 credential/session 边界。
- 约束：
  - 只能附着在 `resource_type=account` 的 resource material 上。
  - 不新增共享资源类型，不替代 `ResourceRecord.material`。
  - raw secret、cookie、token、header value、session dump 与 sign request 参数不得进入 public carrier。
  - Adapter 可以在执行内把 material 派生为平台私有 session config；派生物不得回写为共享 truth。

## SessionHealth

- 用途：表达 account credential/session 是否足以进入需要健康凭据的 resource admission。
- 最小状态：
  - `healthy`：有有效 evidence 证明当前 credential/session 可继续用于目标 execution slice。
  - `stale`：证据已过期、接近过期或不足以证明 freshness。
  - `invalid`：已被平台反馈、Adapter 诊断或 Core 判定为不可继续使用。
  - `unknown`：没有可验证 evidence，或 evidence 无法绑定到当前 resource / lease / task context。
- 约束：
  - `unknown` 不等于 `healthy`。
  - `stale` / `invalid` 不定义自动刷新、重新登录或修复流程。
  - `SessionHealth` 不得写入 `ResourceRecord.status`，也不得扩张 `AVAILABLE / IN_USE / INVALID` 状态集合。

## ResourceHealthEvidence

- 用途：记录 Core 可消费的资源健康证据，用于 resource admission、diagnostics 与 invalidation 判断。
- 关键字段：
  - `evidence_id`：稳定非空标识。
  - `resource_id`：绑定的 resource。
  - `resource_type`：当前只允许 `account`。
  - `status`：`healthy`、`stale`、`invalid`、`unknown`。
  - `observed_at`：RFC3339 UTC 时间戳。
  - `provenance`：`core_validation`、`adapter_diagnostic`、`provider_response_projection`、`operator_assertion` 等来源分类。
  - `task_id`、`lease_id`、`bundle_id`：有执行上下文时必须绑定；库存前置检查可显式为空。
  - `adapter_key`、`capability`、`operation`：用于证明 evidence 适用的 execution slice。
  - `reason`：非空、脱敏的健康原因。
  - `redaction_status`：证明 payload 已脱敏。
  - `diagnostic_ref`：可选，只能引用脱敏诊断或 trace，不得内嵌 secret。
- 约束：
  - 缺少 provenance、observed_at、resource binding 或 redaction status 时必须 invalid。
  - evidence 不得包含 raw credential material。
  - evidence 可以引用 `ResourceLease` / `ResourceTraceEvent`，但不得替代它们。

## ResourceAdmissionDecision

- 用途：表达 Core 在 resource admission 时如何消费 resource availability 与 health evidence。
- 关键字段：
  - `decision_id`
  - `task_id`
  - `adapter_key`
  - `capability`
  - `operation`
  - `requested_slots`
  - `resource_ids`
  - `health_evidence_refs`
  - `decision_status`：`admitted`、`rejected`、`invalid_contract`。
  - `failure_reason`
  - `fail_closed`
- 约束：
  - 所有要求健康 credential 的 admission 都必须能追溯到有效 evidence 或显式 fail-closed。
  - `rejected` 表示资源或健康前提不足；`invalid_contract` 表示 evidence、metadata 或上下文违反契约。

## ResourceInvalidationReason

- 用途：把 health evidence 映射到 Core-owned invalidation reason。
- 最小 reason：
  - `credential_session_invalid`
  - `credential_session_stale`
  - `credential_material_contract_invalid`
  - `health_evidence_contract_invalid`
  - `health_context_mismatch`
- 约束：
  - reason 必须非空、平台中立、可脱敏记录。
  - 最终 resource state 仍通过既有 `release(target_status_after_release=INVALID)` 或后续已批准 runtime carrier 进入 `INVALID`。

## 生命周期

- 创建：
  - `CredentialMaterial` 随 account resource bootstrap 或后续已批准 runtime carrier 进入 resource material。
  - `ResourceHealthEvidence` 由 Core validation、Adapter diagnostic projection 或已批准 operator assertion 创建。
- 更新：
  - 新 evidence 追加或替代 admission 参考；不得原地改写历史 evidence 来伪造 freshness。
  - `SessionHealth` 是 evidence projection，不是独立 lifecycle state。
- 失效/归档：
  - `invalid` evidence 可以触发 Core-owned invalidation。
  - 恢复 `INVALID` resource、刷新 credential 或重新登录不在本 FR 范围内。
