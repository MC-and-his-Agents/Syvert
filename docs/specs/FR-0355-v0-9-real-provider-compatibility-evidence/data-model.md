# FR-0355 数据模型

## 实体清单

- `RealProviderCompatibilityEvidenceReport`
  - 用途：`v0.9.0` closeout 汇总真实外部 provider sample evidence，并为 `FR-0351` 的 `provider_compatibility_sample` gate item 提供输入。
- `ExternalProviderSample`
  - 用途：描述样本来源、Adapter binding、approved slice 与 provider support boundary。
- `CompatibilityDecisionEvidenceMatrix`
  - 用途：汇总 `matched`、`unmatched`、`invalid_contract` 三类 decision 结果与对应验证入口。
- `CoreSurfaceNoLeakageEvidence`
  - 用途：证明 provider identity 没有进入 Core-facing surfaces。

## 关键字段

### RealProviderCompatibilityEvidenceReport

- `release`：固定为 `v0.9.0`。
- `fr_ref`：固定为 `FR-0355`。
- `consumed_gate_ref`：固定为 `FR-0351:provider_compatibility_sample`。
- `approved_slice`：固定为 `content_detail_by_url + url + hybrid`。
- `sample_origin`：必须表达 `external_provider_sample`。
- `provider_support_claim`：必须为 `false`。
- `decision_matrix_ref`：指向 implementation / evidence artifact 的 decision matrix。
- `no_leakage_ref`：指向 provider no-leakage evidence。
- `dual_reference_ref`：指向双参考 regression evidence。
- `third_party_adapter_entry_ref`：指向第三方 Adapter-only contract entry evidence。
- `api_cli_same_core_path_ref`：指向 API / CLI same Core path evidence。
- `status`：允许 `pass`、`fail`。

### ExternalProviderSample

- `sample_id`：稳定、非空、可审计。
- `adapter_key`：必须绑定单一 Adapter。
- `provider_identity_scope`：必须为 `adapter_bound`。
- `provider_key_redaction`：必须说明 provider identity 是否脱敏。
- `requirement_ref`：引用 `FR-0024` compatible requirement。
- `offer_ref`：引用 `FR-0025` compatible offer。
- `decision_ref`：引用 `FR-0026` decision。
- `profile_proof_refs`：引用 `FR-0027` profile proof。
- `forbidden_claims`：不得包含 provider product support、SLA、marketplace、selector 或 fallback。

### CompatibilityDecisionEvidenceMatrix

- `matched_case_ref`：必须存在。
- `unmatched_case_ref`：必须存在。
- `invalid_contract_case_ref`：必须存在。
- `validator_commands`：记录可复验命令或 artifact。
- `fail_closed_reason`：当 status 为 `fail` 时必须存在。

### CoreSurfaceNoLeakageEvidence

- `registry_discovery_checked`：必须为 `true`。
- `core_routing_checked`：必须为 `true`。
- `task_record_checked`：必须为 `true`。
- `resource_lifecycle_checked`：必须为 `true`。
- `failed_envelope_checked`：必须为 `true`。
- `provider_identity_in_core_surface`：必须为 `false`。

## 生命周期

- 创建：implementation / evidence Work Item 在新增 external provider sample fixture 与测试后创建 evidence artifact。
- 更新：仅当 sample、decision matrix、no-leakage 或 release closeout 证据变化时更新。
- 失效/归档：如果后续 provider sample 被证明依赖私密不可复验环境、声明 provider 产品正式支持或越过 approved slice，必须标记为失效并另建 Work Item 修正。
