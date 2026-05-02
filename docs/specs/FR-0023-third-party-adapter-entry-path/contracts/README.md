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
- `resource_proof_admission_refs`
- `resource_proof_admissions`
- `result_contract`
- `error_mapping`
- `fixture_refs`
- `contract_test_profile`

### validation rules

- `adapter_key` 必须稳定、非空、唯一，并且不得携带 provider 产品名、账号标识、环境名或运行期选择策略。
- `sdk_contract_id` 只标识 Adapter SDK / runtime contract 版本，不承载 provider compatibility contract。
- `supported_capabilities`、`supported_targets`、`supported_collection_modes` 必须描述 Adapter 对 Core 暴露的能力边界。
- `resource_requirement_declarations` 必须消费 `FR-0027` 的多 profile resource requirement contract。
- `resource_proof_admission_refs` 字段必须存在；当第三方真实 `adapter_key` 未被 `FR-0027` proof `reference_adapters` 覆盖时必须为非空集合，并且必须唯一命中合法 `ThirdPartyResourceProofAdmission`。
- `resource_proof_admissions` 是 manifest-owned inline carrier，也是 `resource_proof_admission_refs` 的唯一解析来源；不得由全局 runtime registry、fixture side channel、adapter 私有代码或 reviewer 会话上下文补齐。
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
- manifest 不得让第三方真实 `adapter_key` 裸借用只覆盖 `xhs` / `douyin` 的 `FR-0027` proof；若需要通过第三方 contract entry，必须声明 adapter-specific `resource_proof_admission_refs` 与 manifest-owned `resource_proof_admissions`。

## Third-party resource proof admission contract

- canonical carrier：`ThirdPartyResourceProofAdmission`
- 目的：为第三方 Adapter contract entry 中的真实 `adapter_key` 提供 adapter-specific proof coverage bridge，同时保持 `FR-0027` approved shared profile proof、tuple 与 execution path 仍是 governing truth。

### required fields

- `admission_ref`
- `adapter_key`
- `base_profile_ref`
- `capability`
- `execution_path`
- `resource_dependency_mode`
- `required_capabilities`
- `admission_evidence_refs`
- `decision`

### validation rules

- `ThirdPartyResourceProofAdmission` entry 只能来自当前 manifest 的 `resource_proof_admissions`；`resource_proof_admission_refs` 必须在该 carrier 内唯一解析，缺失、重复、跨 carrier lookup 或依赖 reviewer 会话上下文均必须 fail-closed。
- `admission_ref` 必须稳定、唯一，并可被 manifest `resource_proof_admission_refs` 精确引用。
- `adapter_key` 必须等于 manifest `adapter_key`、declaration `adapter_key` 与 fixture 所属 Adapter identity；不得为 `xhs`、`douyin` 或 provider 产品名伪装。
- `base_profile_ref` 必须唯一命中 `FR-0027` approved shared profile proof，且该 proof 必须为 `shared + approve_profile_for_v0_8_0`。
- `capability`、`execution_path`、`resource_dependency_mode` 与 `required_capabilities` 必须与 `base_profile_ref` 命中的 `FR-0027` proof 完全一致。
- 当前只允许 admission 到 `FR-0027` 已批准的 shared tuple：`required + [account]` 或 `required + [account, proxy]`；不得 admission 到 `proxy` rejected profile、`none` rejected profile 或 adapter-only profile。
- `admission_evidence_refs` 必须回指当前第三方 manifest、fixture 与 contract test profile evidence；不得引用 provider offer、真实 provider 样本、adapter 私有注释或泛化的后续 implementation evidence 补足 proof。
- `decision` 当前只允许 `admit_third_party_profile_for_contract_test_v0_8_0`。
- 任一 proof 不可解析、不唯一、不对齐、不覆盖当前真实第三方 adapter admission，或缺少 fixture / manifest evidence 时，必须按 `invalid_resource_requirement` fail-closed。
- admission 参与 proof binding 判定本身；contract entry 不得先执行会因 `reference_adapters` 不含第三方 key 而失败的完整 `FR-0027` adapter coverage 校验，再把 admission 放到后置步骤。
- `FR-0027` 的 shape、single proof ref、approved shared profile proof lookup、tuple、execution path 与 fail-closed 规则仍必须原样校验；admission 只覆盖 adapter coverage 子条件。
- 每个未被 `FR-0027` proof `reference_adapters` 直接覆盖的 declaration profile 必须有且只能有一个 matching admission，且 `admission.base_profile_ref == profile.evidence_refs[0]`。
- manifest 中存在未被任何 uncovered declaration profile 消费的多余 admission，或某个 uncovered profile 找不到 matching admission / 命中多个 admission，必须按 `invalid_resource_requirement` fail-closed。

## Fixture contract

- fixture 至少包含一个成功样本与一个失败映射样本。
- 成功样本必须能验证 `raw + normalized` payload shape。
- 失败映射样本必须能验证 Adapter error mapping。
- 若 Adapter 声明资源依赖，fixture / manifest 必须能触发或证明与 `FR-0027` 合法 profile 对齐的输入。
- fixture 可以使用 deterministic mock 数据；真实外部系统可用性不是本 FR 的准入条件。

## Contract test entry order

1. 校验 manifest shape。
2. 校验 public metadata required fields。
3. 校验 declaration `adapter_key` 与 manifest `adapter_key` 一致。
4. 校验 `FR-0027` declaration shape、single proof ref、approved shared profile proof lookup、tuple 与 execution path 对齐。
5. 判定 proof adapter coverage：若 declaration profile 的 `adapter_key` 不在该 profile 命中的 `FR-0027` proof `reference_adapters` 中，则必须在同一 proof binding 决策中校验当前 manifest-owned `ThirdPartyResourceProofAdmission` 为该 profile 提供 adapter-specific proof coverage。
6. 校验 fixture refs 可解析，并覆盖成功 payload、失败映射与 resource profile input。
7. 校验 Adapter `execute()` 行为与 manifest / fixture 声明一致。

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
- Bare reuse of `xhs` / `douyin` resource proof by an uncovered third-party `adapter_key`
