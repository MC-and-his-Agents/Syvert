# FR-0023 Third-party Adapter entry path

## 关联信息

- item_key：`FR-0023-third-party-adapter-entry-path`
- Issue：`#295`
- item_type：`FR`
- release：`v0.8.0`
- sprint：`2026-S21`

## 背景与目标

- 背景：`v0.7.0` 已通过 `FR-0021` 把 provider port 收敛为 adapter-owned 内部边界；`FR-0027` 已冻结 `v0.8.0` 当前双参考 slice 的多 profile resource requirement contract。`v1.0.0` 前仍需要把第三方作者默认如何以 Adapter 方式接入 Syvert 写成稳定、可审查、可测试的 formal truth，避免社区接入被误导为 provider 产品直接接 Core、Core provider registry 或 marketplace。
- 目标：冻结第三方 Adapter 的最小 public metadata、Adapter-only 稳定接入路径、manifest / fixture / contract test 准入条件与 reference adapter 升级约束，使后续 `#310/#311/#312` 可以围绕同一 governing artifact 推进 contract test、SDK 文档和父 FR closeout。

## 范围

- 本次纳入：
  - 冻结第三方 Adapter 必须暴露的最小 public metadata。
  - 冻结 Adapter-only 稳定接入路径：第三方接入主入口是 Adapter public runtime surface，而不是 provider 产品、provider registry 或 Core extension point。
  - 冻结 manifest / fixture / contract test 的最小准入语义。
  - 冻结第三方真实 `adapter_key` 消费 `FR-0027` approved resource profile proof 时的 adapter-specific admission bridge。
  - 冻结 reference adapter 升级约束，使小红书、抖音继续作为第三方接入路径的可比较 baseline。
  - 消费 `FR-0027` 多 profile resource requirement contract 作为资源声明既有前提，不在本 FR 重写资源声明模型。
- 本次不纳入：
  - Provider capability offer。
  - Adapter / Provider compatibility decision。
  - 真实外部 provider 样本。
  - provider registry、provider selector、provider marketplace、provider 产品白名单或 provider fallback。
  - runtime 实现、contract test harness 实现、SDK 代码实现或 reference adapter 代码迁移。

## 需求说明

- 功能需求：
  - 第三方 Adapter 的 canonical 接入对象必须是 Adapter，而不是 Provider、Provider Port、Core plugin 或 provider 产品注册项。
  - 第三方 Adapter 必须暴露最小 public metadata，至少包含：
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
  - `adapter_key` 必须是稳定、非空、可被 registry 和 contract test 唯一引用的字符串；它不得携带 provider 产品名、账号标识、环境名或运行期选择策略。
  - `sdk_contract_id` 必须标识 Adapter 面向的 Syvert SDK / runtime contract 版本；当前 `v0.8.0` 接入路径不得把 provider compatibility contract 混入该字段。
  - `supported_capabilities`、`supported_targets` 与 `supported_collection_modes` 必须描述 Adapter 对 Core 暴露的能力、目标类型与采集模式；当前 reference baseline 至少覆盖 `content_detail_by_url` 经 Adapter family 投影后的 `content_detail` approved slice。
  - `resource_requirement_declarations` 必须消费 `FR-0027` 冻结的多 profile resource requirement contract；第三方 Adapter 不得在本 FR 下使用私有资源字段、provider offer 或 provider selector 替代该声明。
  - `result_contract` 必须声明 Adapter 成功结果继续返回 `raw payload` 与 `normalized result`；normalized result 仍由 Adapter 负责，不得由 Core、Provider 或 registry 生成。
  - `error_mapping` 必须说明 Adapter 如何把目标系统错误映射为 Syvert 既有失败 envelope / error code；不得新增 provider-specific failed envelope category。
  - `fixture_refs` 必须指向 contract test 可消费的最小 fixture 集合；fixture 可为 mock / deterministic 样本，但必须足以验证 metadata、manifest、resource declaration、success payload 与 error mapping。
  - `resource_proof_admissions` 是 manifest-owned inline carrier；contract test entry 只能在当前 manifest 的 `resource_proof_admissions` 中解析 `resource_proof_admission_refs`，不得从全局 runtime registry、fixture side channel、adapter 私有代码或 reviewer 会话上下文补齐 admission entry。
  - 当第三方 Adapter 的真实 `adapter_key` 尚未被 `FR-0027` approved proof 的 `reference_adapters` 覆盖时，manifest 必须声明 adapter-specific `resource_proof_admission_refs`；每个 admission ref 必须唯一命中当前 manifest 中的一个 `ThirdPartyResourceProofAdmission`，该 admission 必须把真实第三方 `adapter_key` 绑定到一个 `FR-0027` 已批准的 shared profile proof、同一 execution slice、同一 profile tuple 与本 contract entry 的 fixture / manifest 证据。
  - `resource_proof_admission_refs` 不得修改 `FR-0027` 既有 approved proof 的 `reference_adapters`，也不得让第三方 declaration 裸借用 `xhs` / `douyin` proof；它只在第三方 contract entry 中提供 adapter-specific proof coverage bridge。
  - `contract_test_profile` 必须声明该 Adapter 进入 contract test 的最小 profile，例如 `adapter_only_content_detail_v0_8`；profile 只表达测试准入组合，不表达 provider 选择或业务支持承诺。
  - manifest 必须是第三方 Adapter 接入审查和 contract test 的 primary carrier；manifest 内必须能追溯到上述最小 public metadata、fixture refs 与 contract test profile。
  - fixture 必须覆盖至少一个成功样本和一个失败映射样本；若 Adapter 声明需要资源，则 fixture / manifest 必须同时覆盖 `FR-0027` 合法 profile 的可验证输入。
  - contract test 准入必须先校验 manifest shape、metadata 完整性、`FR-0027` resource declaration 合法性、fixture 可解析性，再进入 Adapter `execute()` 行为验证。
  - Adapter-only 接入路径允许 Adapter 内部自行使用 native transport、HTTP、browser bridge 或 adapter-owned provider port；这些实现细节不得出现在 Core registry、TaskRecord、resource lifecycle 或 Adapter public metadata 中。
  - reference adapters 升级时必须继续保留第三方接入 baseline：小红书、抖音的 public metadata、manifest、fixtures 与 contract test profile 必须能作为第三方 Adapter 作者的最小参照。
- 契约需求：
  - Core 与 registry 只能发现 Adapter public metadata；不得发现 provider key、provider offer、provider priority、provider selector、provider fallback 或 provider marketplace 字段。
  - manifest 中出现 provider offer、compatibility decision、provider registry、selector、marketplace、fallback priority、打分或排序字段时，必须视为越过 `FR-0023` 范围。
  - manifest / fixture / contract test 中出现无法按 `FR-0027` 校验的 resource requirement declaration 时，必须 fail-closed，不得用 adapter 私有注释或 provider 能力声明补足。
  - 对第三方真实 `adapter_key` 的 resource declaration 准入必须把 `ThirdPartyResourceProofAdmission` 纳入 proof binding 判定，而不是在完整 `FR-0027` adapter coverage 校验失败后再补救：
    - declaration / profile 必须满足 `FR-0027` 的 shape、approved shared profile proof lookup、tuple、execution path、single proof ref 与 fail-closed 规则。
    - `FR-0027` 的 adapter coverage 子条件必须由以下两种方式之一满足：declaration `adapter_key` 已在被引用 proof 的 `reference_adapters` 中；或存在覆盖该 `adapter_key`、同一 approved proof、同一 tuple 与同一 execution path 的 `ThirdPartyResourceProofAdmission`。
    - adapter coverage 必须逐 profile 判定；每个未被 `FR-0027` proof `reference_adapters` 直接覆盖的 declaration profile 都必须有且只能有一个 matching admission，且 admission `base_profile_ref` 必须等于该 profile 的唯一 `evidence_refs[0]`。
    - manifest 中出现未被任何 uncovered declaration profile 消费的多余 admission，或某个 uncovered profile 找不到 matching admission / 命中多个 admission，必须 fail-closed。
    - 若两种 adapter coverage 方式都不成立，必须按 `invalid_resource_requirement` fail-closed。
  - `ThirdPartyResourceProofAdmission` 只能把第三方 Adapter 当前 contract entry 的 manifest、fixtures 与 contract profile 证据绑定到一个已批准的 `FR-0027` shared profile tuple；其 `admission_evidence_refs` 必须全部符合 `FR-0023` canonical evidence ref schema，并能从当前 manifest、fixture 与 contract profile 字段机器推导；不得引用泛化的后续 implementation evidence 替代当前准入证明，不得批准新共享能力词汇、不得把 `rejected` / `adapter_only` profile 升格为 shared、不得绕过 `FR-0027` proof coverage。
  - contract test profile 必须绑定 Adapter public contract，而不是绑定某个真实外部 provider 产品。
  - reference adapter 迁移不得降低既有 `raw + normalized` 成功 payload、error mapping、resource declaration 与 constructor/test seam 的可验证性。
  - `FR-0023` 不批准新的 shared capability 词汇；若后续 Adapter 需要新增能力词汇，必须先进入独立 formal spec / evidence 链路。
- 非功能需求：
  - formal spec 必须保持 Core / Adapter / Provider 分层清晰：Core 负责运行时语义，Adapter 负责目标系统语义，Provider 相关内容在本 FR 中只可作为 Adapter 内部实现细节存在。
  - contract test 准入必须可由本地脚本或 CI 判定，不依赖 reviewer 口头解释或真实外部服务可用性。
  - 第三方 Adapter 接入路径必须 fail-closed；任何 metadata、manifest、fixture、resource declaration 或 result contract 无法证明合法时，都不得被 registry 或 contract test 视为通过。

## 约束

- 阶段约束：
  - 本 FR 服务 `v0.8.0` 的第三方 Adapter 稳定接入路径，不完成 `v0.8.0` 中 Adapter / Provider compatibility decision 的全部目标。
  - 本 FR 只冻结 Adapter-only 主入口和 contract test 准入，不接入真实外部 provider 样本。
  - `FR-0027` 是本 FR 的资源声明前置 truth；本 FR 不重写 `FR-0013` / `FR-0014` / `FR-0015` 的历史语义。
- 架构约束：
  - Core 不得新增 provider-facing registry、selector、marketplace、routing hint 或 TaskRecord provider 字段。
  - Adapter public metadata 不得把 provider offer 或 compatibility decision 伪装为 Adapter capability metadata。
  - manifest 与 fixture 是接入准入 carrier，不是 runtime 状态真相源，也不是 release / sprint / GitHub 状态替代物。
  - formal spec 与实现 PR 必须分离；`#309` 不修改 runtime、tests、SDK 代码或 reference adapter 实现。

## GWT 验收场景

### 场景 1：第三方 Adapter 通过 manifest 进入 contract test

Given 一个第三方 Adapter manifest 声明了 `adapter_key`、`sdk_contract_id`、能力 / target / collection mode、`FR-0027` resource requirement、`raw + normalized` result contract、error mapping、fixture refs 与 `adapter_only_content_detail_v0_8` contract test profile  
When contract test entry 校验该 manifest  
Then 它必须能在不读取 provider offer、provider selector 或真实外部 provider 样本的前提下判定该 Adapter 是否可进入 Adapter-only contract test

### 场景 2：Core registry 只发现 Adapter public metadata

Given registry discovery 消费一个第三方 Adapter  
When 调用方查询该 Adapter 的 public metadata  
Then 返回内容只能包含 Adapter key、能力、target、collection mode、resource requirement declaration 与 result / error contract，不得包含 provider key、provider offer、provider priority、selector、marketplace 或 fallback 字段

### 场景 3：资源声明消费 FR-0027 前提

Given 第三方 Adapter manifest 的 `resource_requirement_declarations` 包含多个合法 profile  
When contract test entry 校验该声明  
Then 它必须按 `FR-0027` 的多 profile contract 校验 profile shape、evidence refs、approved tuple 与 fail-closed 口径，而不是使用本 FR 内的新资源声明模型

### 场景 3A：真实第三方 adapter_key 通过 adapter-specific proof admission

Given 第三方 Adapter manifest 使用真实 `adapter_key=community_content_adapter`，其 `resource_requirement_declarations` 声明 `content_detail_by_url + url + hybrid` 的 `account` profile，且 manifest 同时声明 `resource_proof_admission_refs=[fr-0023:third-party-proof-admission:community-content-adapter:content-detail-by-url-hybrid:account]`
When contract test entry 校验该 manifest
Then 它必须先确认该 admission ref 绑定到 `FR-0027` 已批准的 `fr-0027:profile:content-detail-by-url-hybrid:account` shared proof、同一 tuple、同一 execution path 与当前 fixture / manifest 证据，再把 `community_content_adapter` 视为当前 contract entry 下被 proof coverage 覆盖的真实第三方 `adapter_key`

### 场景 3C：admission 参与 proof binding 判定

Given 第三方 declaration 的 `adapter_key=community_content_adapter` 不在 `FR-0027` proof `reference_adapters` 中，但存在同一 manifest 声明的合法 `ThirdPartyResourceProofAdmission`
When contract test entry 校验 resource declaration
Then 它必须先完成 `FR-0027` proof lookup、tuple 与 execution path 对齐，再用 admission 覆盖 adapter coverage 子条件；不得先执行会因 `reference_adapters` 不含该 key 而失败的完整 registry proof validation，再把 admission 放在不可达的后置步骤中

### 场景 3D：每个 uncovered profile 都必须有唯一 admission

Given 第三方 manifest 声明两个 resource profiles，其中 `account` 与 `account,proxy` 两个 profile 都引用只覆盖 `xhs,douyin` 的 `FR-0027` proof
When contract test entry 解析 `resource_proof_admission_refs`
Then 每个 profile 都必须有且只能有一个 `base_profile_ref == profile.evidence_refs[0]` 的 manifest-owned admission；若任一 profile 缺少 admission、命中多个 admission，或 manifest 中存在未被 profile 消费的多余 admission，必须 fail-closed

### 场景 3E：admission evidence refs 必须可由当前 contract entry 机器推导

Given 第三方 manifest 使用 `adapter_key=community_content_adapter` 与 `contract_test_profile=adapter_only_content_detail_v0_8`，并声明 success / error_mapping fixtures
When contract test entry 校验 `ThirdPartyResourceProofAdmission.admission_evidence_refs`
Then 每个 ref 必须匹配 `fr-0023:manifest:community_content_adapter:adapter_only_content_detail_v0_8`、`fr-0023:contract-profile:community_content_adapter:adapter_only_content_detail_v0_8` 或当前 fixture 派生的 `fr-0023:fixture:community_content_adapter:<fixture_id>`；若 ref 无法由当前 manifest / fixture / profile 字段推导，必须 fail-closed

### 场景 3B：裸借用 reference proof 必须阻断

Given 第三方 Adapter manifest 使用真实 `adapter_key=community_content_adapter`，但 profile `evidence_refs` 只引用当前 `FR-0027` 中 `reference_adapters=[xhs,douyin]` 的 proof，且没有 adapter-specific `resource_proof_admission_refs`
When contract test entry 校验该 manifest
Then 它必须按 `invalid_resource_requirement` fail-closed，因为第三方 declaration 不能裸借用未覆盖自己的 reference adapter proof

### 场景 4：fixture 覆盖成功与失败映射

Given 第三方 Adapter manifest 指向一组 fixture  
When contract test 解析 fixture  
Then fixture 必须至少能验证一个 `raw + normalized` 成功 payload 和一个 Adapter error mapping；若任一 fixture 缺失或不可解析，Adapter 不得进入通过状态

### 场景 5：reference adapter 升级保持基线

Given 小红书、抖音 reference adapters 后续升级 public metadata、manifest、fixture 或 contract test profile  
When reviewer 审查升级 PR  
Then 这些 reference adapters 必须继续展示第三方 Adapter 可复用的 Adapter-only 接入路径，并保持当前 approved slice 的 `raw + normalized`、error mapping 与 `FR-0027` resource declaration 可验证

### 场景 6：provider 字段越界

Given 某个 manifest 声明了 provider offer、provider selector、provider fallback priority 或 compatibility decision  
When contract test entry 或 spec review 校验该 manifest  
Then 它必须被判定为越过 `FR-0023` 范围，不能通过 Adapter-only 接入准入

## 异常与边界场景

- 异常场景：
  - manifest 缺少任一最小 public metadata 字段时，必须 fail-closed。
  - `adapter_key` 不稳定、为空、重复，或混入 provider 产品名 / 环境名 / 账号标识时，必须阻断准入。
  - `resource_requirement_declarations` 无法按 `FR-0027` 校验时，必须阻断准入。
  - 第三方真实 `adapter_key` 未被 `FR-0027` proof `reference_adapters` 覆盖，且缺少合法 `ThirdPartyResourceProofAdmission` 时，必须阻断准入。
  - `ThirdPartyResourceProofAdmission` 绑定到 `rejected` / `adapter_only` profile、tuple 不一致、execution path 不一致、当前 fixture / manifest 证据不可解析，或 admission `adapter_key` 与 manifest / declaration 不一致时，必须阻断准入。
  - `resource_proof_admission_refs` 无法在当前 manifest 的 `resource_proof_admissions` 中唯一解析、profile coverage 缺失、coverage 重复或 admission 未被任何 uncovered profile 消费时，必须阻断准入。
  - `admission_evidence_refs` 缺少当前 manifest evidence ref、contract profile evidence ref、至少一个 success fixture evidence ref 或至少一个 error_mapping fixture evidence ref，或包含任何无法由当前 contract entry 字段推导的 ref 时，必须阻断准入。
  - contract test entry 若把 admission 放在完整 `FR-0027` adapter coverage 校验之后，导致真实第三方 `adapter_key` 永远先被 reference proof 阻断，必须视为实现顺序错误。
  - 第三方 contract entry 使用 `xhs`、`douyin` 或其它 provider 产品名伪装第三方 `adapter_key` 时，必须阻断准入；reference adapter baseline 可继续使用其自身 key，但不得作为第三方样例 identity。
  - fixture refs 不可解析、fixture 缺失成功样本或失败映射样本时，必须阻断准入。
  - success payload 不同时包含 `raw` 与 `normalized`，或 normalized result 由 provider / Core 声明负责时，必须阻断准入。
  - manifest、metadata 或 registry discovery 暴露 provider offer、selector、marketplace、fallback、priority、score 或 compatibility decision 时，必须视为 scope drift。
- 边界场景：
  - Adapter 内部可以继续使用 adapter-owned provider port 或 native provider；只要 provider 细节不进入 Core-facing metadata、registry、TaskRecord、resource lifecycle 或 contract test profile，即不构成本 FR 的 provider 接入。
  - contract test profile 可以表达测试矩阵名称，但不得表达运行时 provider 选择策略。
  - fixture 可以使用 deterministic mock 数据，不要求真实外部系统可访问；真实 provider 样本属于后续独立 FR。
  - 本 FR 不批准新的业务 capability；第三方 Adapter 若声明超出当前 approved slice 的能力，必须先有对应 formal spec / evidence 输入。

## 验收标准

- [ ] formal spec 明确第三方接入主入口是 Adapter public runtime surface，而不是 Provider / Core plugin / provider registry。
- [ ] formal spec 明确最小 public metadata 字段集合及字段边界。
- [ ] formal spec 明确 manifest 是第三方 Adapter 接入审查与 contract test 的 primary carrier。
- [ ] formal spec 明确 fixture 至少覆盖成功 payload 与失败映射样本。
- [ ] formal spec 明确 contract test 准入顺序：manifest shape、metadata、`FR-0027` resource declaration、fixture、Adapter execute 行为。
- [ ] formal spec 明确第三方真实 `adapter_key` 的 resource proof admission bridge：不能裸借用 reference proof，必须通过 adapter-specific admission ref 获得 proof coverage。
- [ ] formal spec 明确 Adapter-only 接入路径不得包含 provider offer、compatibility decision、provider registry / selector / marketplace 或 runtime 实现。
- [ ] formal spec 明确 reference adapter 升级必须保持第三方接入 baseline 可验证。
- [ ] formal spec 为 `#310/#311/#312` 提供可执行进入条件。

## 依赖与外部前提

- 外部依赖：
  - `FR-0021` 已冻结 adapter-owned provider port 只作为仓内 / Adapter 内部边界，不是 Core-facing provider SDK。
  - `FR-0027` 已冻结多 profile resource requirement contract；本 FR 直接消费其 declaration / matcher / evidence 边界。
  - `#291` 已把 `v0.8.0+` 开放 Adapter / Provider compatibility 路线写入 planning / decision truth。
- 上下游影响：
  - `#310` 必须基于本 FR 实现或完善 contract test entry，不得扩大到 provider offer / compatibility decision。
  - `#310` 的第三方 contract entry 通过样例必须使用真实第三方 `adapter_key`，并消费本 FR 的 `ThirdPartyResourceProofAdmission`，不得把第三方样例伪装为 `xhs` / `douyin`，也不得跳过 `FR-0027` proof coverage。
  - `#311` 必须基于本 FR 更新 SDK docs 与 migration 说明，使第三方 Adapter 作者能按 manifest / fixture / contract test 路径接入。
  - `#312` 必须以本 FR formal spec、contract test entry、SDK docs / migration 与 GitHub 状态作为 parent closeout 输入。
  - `data-model.md` 与 `contracts/README.md` 是本 FR 中 manifest、fixture、contract test profile 与 reference adapter baseline 的约束补充；若与 `spec.md` 发生冲突，以 `spec.md` 的目标与边界为准，并回到 spec review 修正。
