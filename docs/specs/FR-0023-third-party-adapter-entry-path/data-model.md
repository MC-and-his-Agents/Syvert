# FR-0023 data model

## ThirdPartyAdapterManifest

用途：第三方 Adapter 接入审查与 contract test entry 的 primary carrier。

最小字段：

- `adapter_key`
  - 语义：稳定 Adapter identity。
  - 约束：非空、唯一、可被 registry 与 contract test 引用；不得携带 provider 产品名、账号标识、环境名或运行时选择策略。
- `sdk_contract_id`
  - 语义：Adapter 面向的 Syvert SDK / runtime contract 版本。
  - 约束：不承载 provider compatibility contract。
- `supported_capabilities`
  - 语义：Adapter 对 Core 暴露的 capability family。
  - 约束：不得通过本字段批准新业务能力；超出 approved slice 的能力必须另有 formal spec / evidence。
- `supported_targets`
  - 语义：Adapter 支持的 target type。
- `supported_collection_modes`
  - 语义：Adapter 支持的 collection mode。
- `resource_requirement_declarations`
  - 语义：Adapter capability 的资源依赖声明。
  - 约束：必须消费 `FR-0027` `AdapterResourceRequirementDeclarationV2`，不得使用 provider offer 或 adapter 私有字段替代。
- `resource_proof_admission_refs`
  - 语义：第三方真实 `adapter_key` 尚未被 `FR-0027` approved proof `reference_adapters` 覆盖时，manifest 用来声明 adapter-specific proof admission 的稳定引用集合。
  - 约束：字段必须存在；当 `resource_requirement_declarations[*].adapter_key` 不在其 profile proof `reference_adapters` 中时必须为非空集合。每个 ref 必须唯一命中一个 `ThirdPartyResourceProofAdmission`，且 admission 的 `adapter_key`、`capability`、`execution_path`、`resource_dependency_mode` 与 `required_capabilities` 必须和 manifest / declaration / fixture 完全一致。
- `resource_proof_admissions`
  - 语义：manifest-owned inline admission entries，是 `resource_proof_admission_refs` 的唯一解析来源。
  - 约束：字段必须存在；contract test entry 只能在当前 manifest 的该字段内解析 admission，不得从全局 registry、fixture side channel、adapter 私有代码或 reviewer 会话上下文补齐。
- `result_contract`
  - 语义：成功结果形态。
  - 约束：必须声明 `raw` 与 `normalized`，且 normalized result 由 Adapter 生成。
- `error_mapping`
  - 语义：目标系统错误到 Syvert failed envelope / error code 的映射说明。
  - 约束：不得新增 provider-specific failed envelope category。
- `fixture_refs`
  - 语义：contract test 可解析的 fixture 引用集合。
  - 约束：至少覆盖一个成功样本和一个失败映射样本。
- `contract_test_profile`
  - 语义：Adapter contract test 准入组合。
  - 约束：只表达测试 profile，不表达 provider selector、fallback 或 runtime routing。

禁止字段：

- `provider_offer`
- `compatibility_decision`
- `provider_key`
- `provider_registry`
- `provider_selector`
- `provider_marketplace`
- `provider_fallback`
- `provider_priority`
- `provider_score`
- `provider_product_allowlist`

## ThirdPartyResourceProofAdmission

用途：在不修改 `FR-0027` 双参考 approved proof 本身的前提下，为第三方 contract entry 中的真实 `adapter_key` 提供 adapter-specific resource proof coverage。

解析来源：只能来自当前 `ThirdPartyAdapterManifest.resource_proof_admissions`。`resource_proof_admission_refs` 中的每个 ref 必须在该 manifest-owned carrier 中唯一命中一条 entry；carrier 中不得存在未被当前 uncovered declaration profile 消费的多余 entry。

字段：

- `admission_ref`
  - 类型：`string`
  - 约束：稳定、非空、在当前 admission carrier 中唯一；是 manifest `resource_proof_admission_refs` 的 canonical target。
- `adapter_key`
  - 类型：`string`
  - 约束：必须是真实第三方 Adapter identity；必须与 manifest `adapter_key`、`resource_requirement_declarations[*].adapter_key` 与 fixture `manifest_ref` 一致；不得为 `xhs`、`douyin` 或 provider 产品名伪装。
- `base_profile_ref`
  - 类型：`string`
  - 约束：必须唯一命中一个 `FR-0027` `ApprovedSharedResourceRequirementProfileEvidenceEntry.profile_ref`，且该 entry 必须为 `shared + approve_profile_for_v0_8_0`。
- `capability`
  - 类型：`string`
  - 约束：当前只允许 `content_detail`；必须与 manifest 和 declaration 一致。
- `execution_path`
  - 类型：`object`
  - 约束：必须与 `FR-0027` 当前 approved execution slice 完全一致：`operation=content_detail_by_url`、`target_type=url`、`collection_mode=hybrid`。
- `resource_dependency_mode`
  - 类型：`enum`
  - 允许值：`required`
  - 约束：必须与 `base_profile_ref` 命中的 `FR-0027` profile tuple 一致；不得把 `none` rejected profile 或 adapter-only profile 升格。
- `required_capabilities`
  - 类型：`string[]`
  - 约束：必须与 `base_profile_ref` 命中的 approved tuple 完全一致；当前只允许 `account` 或 `account, proxy` 两类已批准 shared tuple。
- `admission_evidence_refs`
  - 类型：`string[]`
  - 约束：非空、去重；必须回指当前第三方 manifest、fixtures 与 contract test profile 证据，证明该真实 Adapter 在同一 execution slice 下可被当前 contract entry 验证；所有 ref 必须符合 `AdmissionEvidenceRef` schema，且能从当前 manifest / fixture / profile 字段机器推导；不得使用泛化的后续 implementation evidence 替代当前准入证明。
- `decision`
  - 类型：`enum`
  - 允许值：`admit_third_party_profile_for_contract_test_v0_8_0`

判定规则：

- `base_profile_ref` 不可解析、不唯一、不是 `shared + approve_profile_for_v0_8_0`，或 tuple / execution path 与 admission 不一致 -> `invalid_resource_requirement`
- admission `adapter_key` 与 manifest / declaration / fixture 不一致 -> `invalid_resource_requirement`
- admission 只覆盖 `FR-0027` proof binding 中的 adapter coverage 子条件；profile shape、single proof ref、approved shared proof lookup、tuple 与 execution path 仍必须按 `FR-0027` 原规则校验
- 每个未被 `FR-0027` proof `reference_adapters` 覆盖的 declaration profile 必须有且只能有一个 matching admission，且 `admission.base_profile_ref == profile.evidence_refs[0]`
- manifest 中存在未被任何 uncovered declaration profile 消费的 admission，或 `resource_proof_admission_refs` 引用缺失 / 重复 / 未命中 entry -> `invalid_resource_requirement`
- `admission_evidence_refs` 必须至少包含当前 manifest evidence ref、当前 contract profile evidence ref、至少一个 success fixture evidence ref 与至少一个 error_mapping fixture evidence ref；任一 ref 无法按 `AdmissionEvidenceRef` schema 从当前 contract entry 派生 -> `invalid_resource_requirement`
- admission 试图批准新共享能力、provider offer、compatibility decision、priority、fallback 或真实 provider 样本 -> contract violation
- 缺少合法 admission 时，第三方真实 `adapter_key` 不得裸借用 `xhs` / `douyin` reference proof

## AdmissionEvidenceRef

用途：为 `ThirdPartyResourceProofAdmission.admission_evidence_refs` 提供可机器校验的当前 contract entry evidence identity。

允许格式：

- Manifest evidence ref
  - 格式：`fr-0023:manifest:{adapter_key}:{contract_test_profile}`
  - 派生来源：当前 `ThirdPartyAdapterManifest.adapter_key` 与 `ThirdPartyAdapterManifest.contract_test_profile`
- Contract profile evidence ref
  - 格式：`fr-0023:contract-profile:{adapter_key}:{contract_test_profile}`
  - 派生来源：当前 `ThirdPartyAdapterManifest.adapter_key` 与 `ContractTestEntryProfile` 名称
- Fixture evidence ref
  - 格式：`fr-0023:fixture:{adapter_key}:{fixture_id}`
  - 派生来源：当前 `ThirdPartyAdapterManifest.adapter_key` 与 `AdapterContractFixture.fixture_id`

验证规则：

- `admission_evidence_refs` 中的所有 ref 必须匹配上述三类格式之一。
- `adapter_key` segment 必须等于当前 manifest `adapter_key`。
- manifest / contract profile ref 的 `contract_test_profile` segment 必须等于当前 manifest `contract_test_profile`。
- fixture ref 的 `fixture_id` 必须来自当前 manifest `fixture_refs` 可解析出的 fixture 集合。
- 每个 admission 必须至少包含当前 manifest evidence ref、当前 contract profile evidence ref、一个 `case_type=success` 的 fixture evidence ref 与一个 `case_type=error_mapping` 的 fixture evidence ref。
- 不允许引用 PR 号、commit SHA、外部 provider 样本、运行期临时日志、未来 implementation evidence 或 reviewer 会话上下文作为 admission evidence identity。

## AdapterContractFixture

用途：为 contract test 提供 deterministic 样本，使第三方 Adapter 准入不依赖真实外部服务。

最小语义：

- `fixture_id`
  - 语义：fixture 稳定标识。
  - evidence identity：可与 manifest `adapter_key` 派生 `fr-0023:fixture:{adapter_key}:{fixture_id}`。
- `manifest_ref`
  - 语义：回指消费该 fixture 的 manifest 或 adapter key。
- `case_type`
  - 允许值：`success`、`error_mapping`。
- `input`
  - 语义：Adapter execute 行为验证需要的最小输入。
- `expected`
  - 语义：期望输出或错误映射。

成功样本约束：

- `expected` 必须能验证成功 payload 同时包含 `raw` 与 `normalized`。
- 若 manifest 声明资源依赖，样本必须能与 `FR-0027` 合法 profile 对齐。

失败映射样本约束：

- `expected` 必须能验证 Adapter error mapping。
- 不得把 provider selection outcome 当成 Syvert failed envelope。

## ContractTestEntryProfile

用途：描述 contract test entry 应执行的 Adapter-only 测试准入组合。

当前最小 profile：

- `adapter_only_content_detail_v0_8`

evidence identity：

- 与 manifest `adapter_key` 派生 `fr-0023:contract-profile:{adapter_key}:adapter_only_content_detail_v0_8`。

准入顺序：

1. manifest shape。
2. public metadata required fields。
3. `resource_requirement_declarations` 与 manifest `adapter_key` 一致性。
4. `FR-0027` declaration shape、single proof ref、approved shared profile proof lookup、tuple 与 execution path 对齐。
5. proof adapter coverage 判定：直接命中 `FR-0027` proof `reference_adapters`，或由当前 manifest `resource_proof_admission_refs` 命中的 `ThirdPartyResourceProofAdmission` 逐 profile 覆盖。
6. fixture refs 与 fixture coverage。
7. Adapter `execute()` 行为。

约束：

- profile 名称不是 runtime routing hint。
- profile 名称不是 provider selector。
- profile 名称不批准真实外部 provider 样本。

## ReferenceAdapterBaseline

用途：让小红书、抖音继续作为第三方 Adapter 作者可比较的最小接入 baseline。

必须保持可验证的维度：

- public metadata。
- manifest。
- fixture refs。
- contract test profile。
- `FR-0027` resource requirement declaration。
- `raw + normalized` success payload。
- error mapping。

边界：

- reference adapter 内部 provider port / native provider 细节不得进入 public metadata、manifest、registry discovery、TaskRecord、resource lifecycle 或 contract test profile。
- reference adapter baseline 是第三方 Adapter 接入参照，不是 provider 产品支持承诺。
