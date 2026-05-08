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
  - `unknown` 是 admission-time projection，不是持久化 `ResourceHealthEvidence.status`。
  - `stale` / `invalid` 不定义自动刷新、重新登录或修复流程。
  - `SessionHealth` 不得写入 `ResourceRecord.status`，也不得扩张 `AVAILABLE / IN_USE / INVALID` 状态集合。

## ResourceHealthEvidence

- 用途：记录 Core 可消费的资源健康证据，用于 resource admission、diagnostics 与 invalidation 判断。
- 关键字段：
  - `evidence_id`：稳定非空标识。
  - `resource_id`：绑定的 resource。
  - `resource_type`：当前只允许 `account`。
  - `status`：`healthy`、`stale`、`invalid`。
  - `observed_at`：RFC3339 UTC 时间戳。
  - `expires_at`：RFC3339 UTC 时间戳；`status=healthy` 时必须存在。
  - `freshness_policy_ref`：非空 policy 标识，用于说明 `expires_at` 如何被计算；本 FR 不定义自动刷新。
  - `provenance`：`core_validation`、`adapter_diagnostic`、`provider_response_projection`、`operator_assertion` 等来源分类。
  - `task_id`、`lease_id`、`bundle_id`：有执行上下文时必须绑定；库存前置检查可显式为空。
  - `adapter_key`、`capability`、`operation`：用于证明 evidence 适用的 execution slice。
  - `reason`：非空、脱敏的健康原因。
  - `redaction_status`：证明 payload 已脱敏。
  - `diagnostic_ref`：可选，只能引用脱敏诊断或 trace，不得内嵌 secret。
- 约束：
  - 缺少 provenance、observed_at、resource binding 或 redaction status 时必须 `invalid_contract`。
  - `healthy` evidence 缺少 `expires_at` 或 `freshness_policy_ref` 时不得作为 fresh credential 证明，且必须按 evidence contract invalid fail-closed。
  - evidence truth 不得携带 `evaluated_at`；`evaluated_at` 属于 admission decision。
  - evidence 不得包含 raw credential material；未脱敏 evidence 必须 `invalid_contract`。
  - evidence 可以引用 `ResourceLease` / `ResourceTraceEvent`，但不得替代它们。
  - `invalid_contract` evidence 不是 `SessionHealth=invalid`，不得作为 session invalidation 依据。

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
  - `evaluated_at`：RFC3339 UTC admission evaluation time。
  - `projected_session_health`：`healthy`、`stale`、`invalid`、`unknown`。
  - `decision_status`：`admitted`、`rejected`、`invalid_contract`。
  - `failure_reason`
  - `fail_closed`
- 约束：
  - 所有要求健康 credential 的 admission 都必须能追溯到有效 evidence 或显式 fail-closed。
  - `rejected` 表示资源或健康前提不足；`invalid_contract` 表示 evidence、metadata 或上下文违反契约。
  - 当 `evaluated_at >= evidence.expires_at` 时，admission 必须把 `healthy` evidence 投影为 `projected_session_health=stale`。
  - 没有可验证 evidence 时，admission 必须投影为 `projected_session_health=unknown` 并 fail-closed。
  - pre-admission `invalid` evidence 没有 active lease 时只能产生 `rejected` / `invalid_contract` admission result，不得直接推进 `ResourceRecord.status`。
  - malformed、unredacted 或 context-mismatched evidence 必须产生 `invalid_contract`，不得映射为 `credential_session_invalid`。
  - admission failure reasons 可以包括 `credential_session_stale`、`credential_session_unknown`、`pre_admission_session_invalid`、`credential_material_contract_invalid`、`health_evidence_contract_invalid`、`health_context_mismatch`。

## ResourceInvalidationReason

- 用途：把 health evidence 映射到 Core-owned invalidation reason。
- 最小 reason：
  - `credential_session_invalid`
- 约束：
  - reason 必须非空、平台中立、可脱敏记录。
  - 只有 active lease 持有的 resource 可以通过既有 `release(target_status_after_release=INVALID)` 进入 `INVALID`。
  - 没有 active lease 的 pre-admission invalid evidence 在本 FR 内只拒绝 admission；直接库存 invalidation carrier 需要后续 Work Item 批准。
  - `stale` 不属于最小 invalidation reason；它只能拒绝 admission，除非后续 evidence 明确升级为 `invalid`。
  - contract-invalid evidence 不属于 invalidation reason；它只能导致 admission `invalid_contract` 或 fail-closed。

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
