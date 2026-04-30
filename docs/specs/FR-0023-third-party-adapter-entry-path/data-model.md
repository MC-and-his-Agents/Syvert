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

## AdapterContractFixture

用途：为 contract test 提供 deterministic 样本，使第三方 Adapter 准入不依赖真实外部服务。

最小语义：

- `fixture_id`
  - 语义：fixture 稳定标识。
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

准入顺序：

1. manifest shape。
2. public metadata required fields。
3. `FR-0027` resource requirement declaration。
4. fixture refs 与 fixture coverage。
5. Adapter `execute()` 行为。

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
