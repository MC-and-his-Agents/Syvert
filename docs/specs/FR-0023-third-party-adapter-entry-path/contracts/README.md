# FR-0023 contracts

## Adapter-only entry contract

- canonical entry object：`ThirdPartyAdapter`
- canonical entry path：Adapter public runtime surface
- 当前 `v0.8.0` 只冻结 Adapter-only 接入路径；Provider offer、compatibility decision、真实外部 provider 样本、provider registry / selector / marketplace 不属于本 contract。

## Public metadata contract

### required fields

- `adapter_key`
- `sdk_contract_id`
- `supported_capabilities`
- `supported_targets`
- `supported_collection_modes`
- `resource_requirement_declarations`
- `result_contract`
- `error_mapping`
- `fixture_refs`
- `contract_test_profile`

### validation rules

- `adapter_key` 必须稳定、非空、唯一，并且不得携带 provider 产品名、账号标识、环境名或运行期选择策略。
- `sdk_contract_id` 只标识 Adapter SDK / runtime contract 版本，不承载 provider compatibility contract。
- `supported_capabilities`、`supported_targets`、`supported_collection_modes` 必须描述 Adapter 对 Core 暴露的能力边界。
- `resource_requirement_declarations` 必须消费 `FR-0027` 的多 profile resource requirement contract。
- `result_contract` 必须声明成功结果包含 `raw` 与 `normalized`。
- `error_mapping` 必须映射到 Syvert 既有失败 envelope / error code，不新增 provider-specific failed envelope category。
- `fixture_refs` 必须指向 contract test 可解析的 fixture。
- `contract_test_profile` 只表达 Adapter contract test 准入组合，不表达 provider 选择策略。

## Manifest contract

- manifest 是第三方 Adapter 接入审查与 contract test entry 的 primary carrier。
- manifest 必须完整承载 public metadata required fields。
- manifest 必须能追溯到 fixture refs 与 contract test profile。
- manifest 不得包含 provider offer、compatibility decision、provider registry、provider selector、provider marketplace、fallback priority、排序、打分或 provider 产品白名单字段。
- manifest 不得用 adapter 私有注释、provider 能力声明或真实 provider 样本补足 `FR-0027` resource declaration。

## Fixture contract

- fixture 至少包含一个成功样本与一个失败映射样本。
- 成功样本必须能验证 `raw + normalized` payload shape。
- 失败映射样本必须能验证 Adapter error mapping。
- 若 Adapter 声明资源依赖，fixture / manifest 必须能触发或证明与 `FR-0027` 合法 profile 对齐的输入。
- fixture 可以使用 deterministic mock 数据；真实外部系统可用性不是本 FR 的准入条件。

## Contract test entry order

1. 校验 manifest shape。
2. 校验 public metadata required fields。
3. 校验 `FR-0027` resource requirement declaration。
4. 校验 fixture refs 可解析，并覆盖成功 payload 与失败映射。
5. 校验 Adapter `execute()` 行为与 manifest / fixture 声明一致。

## Reference adapter upgrade contract

- 小红书、抖音 reference adapters 必须继续作为第三方 Adapter 接入路径的可比较 baseline。
- reference adapter 升级不得降低 public metadata、manifest、fixture、contract test profile、`raw + normalized` payload、error mapping 或 `FR-0027` resource declaration 的可验证性。
- reference adapter 内部可以继续使用 adapter-owned provider port 或 native provider，但 provider 细节不得进入 Core-facing metadata、registry、TaskRecord、resource lifecycle 或 contract test profile。

## Explicitly forbidden

- Provider capability offer
- Adapter / Provider compatibility decision
- Real external provider sample
- Core provider registry
- Provider selector
- Provider marketplace
- Provider fallback priority
- Provider score / ranking
- Provider product allowlist
- Runtime implementation changes
