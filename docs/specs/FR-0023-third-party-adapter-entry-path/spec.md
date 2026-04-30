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
  - `#311` 必须基于本 FR 更新 SDK docs 与 migration 说明，使第三方 Adapter 作者能按 manifest / fixture / contract test 路径接入。
  - `#312` 必须以本 FR formal spec、contract test entry、SDK docs / migration 与 GitHub 状态作为 parent closeout 输入。
  - `data-model.md` 与 `contracts/README.md` 是本 FR 中 manifest、fixture、contract test profile 与 reference adapter baseline 的约束补充；若与 `spec.md` 发生冲突，以 `spec.md` 的目标与边界为准，并回到 spec review 修正。
