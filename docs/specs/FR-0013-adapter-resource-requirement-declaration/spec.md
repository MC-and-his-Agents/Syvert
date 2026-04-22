# FR-0013 Adapter resource requirement declaration

## 关联信息

- item_key：`FR-0013-adapter-resource-requirement-declaration`
- Issue：`#189`
- item_type：`FR`
- release：`v0.5.0`
- sprint：`2026-S18`

## 背景与目标

- 背景：`FR-0010` 已冻结最小资源生命周期，`FR-0012` 已冻结 Core 注入 `ResourceBundle` 与 Adapter 资源边界，但当前仍缺少一层 formal contract 来回答“某个 adapter-facing 执行路径是否依赖受管资源、依赖哪些共享能力”。如果这层声明继续散落在 runtime 常量、reference adapter 私有假设或实现注释里，`v0.5.0` 就无法在双参考适配器压力下收敛资源抽象。
- 目标：为 `v0.5.0` 冻结 `AdapterResourceRequirementDeclaration` 的最小声明 carrier，使后续实现只能围绕已批准的共享能力词汇 `account`、`proxy` 与 `FR-0015` 共享证据推进，而不能把 provider 选择、fallback 或具体技术实现偷渡进 Core。

## 范围

- 本次纳入：
  - 冻结 `AdapterResourceRequirementDeclaration` 作为 canonical declaration carrier
  - 冻结固定字段：`adapter_key`、`capability`、`resource_dependency_mode`、`required_capabilities[]`、`evidence_refs[]`
  - 冻结 `resource_dependency_mode=none|required` 的最小语义
  - 冻结 `required_capabilities[]` 与 `FR-0015` 已批准共享词汇 `account`、`proxy` 的绑定关系
  - 冻结 `evidence_refs[]` 必须绑定到 `FR-0015` 共享证据的要求
  - 冻结当前双参考适配器共享声明基线：`xhs + content_detail -> required [account, proxy]`、`douyin + content_detail -> required [account, proxy]`
- 本次不纳入：
  - `FR-0010` 的资源生命周期主 contract、slot 之外的新资源类型或状态机
  - `FR-0012` 的 Core 注入 bundle / Adapter 执行边界
  - `FR-0014` / `FR-0015` 的正文、证据真相源或新增共享能力词汇
  - `preferred_capabilities`、`optional_capabilities`、`fallback`、`priority`、`provider_selection`
  - Playwright、CDP、Chromium、browser provider、sign service 等技术字段
  - runtime matcher、provider 实现、调度策略与测试代码

## 需求说明

- 功能需求：
  - `AdapterResourceRequirementDeclaration` 必须是 adapter-facing 资源依赖声明的唯一 canonical carrier；后续 formal spec 与实现不得再引入第二套影子声明 schema。
  - 每条声明必须显式携带：`adapter_key`、`capability`、`resource_dependency_mode`、`required_capabilities[]`、`evidence_refs[]`。
  - `resource_dependency_mode` 在 `v0.5.0` 只允许 `none` 或 `required`。
  - 当 `resource_dependency_mode=none` 时，`required_capabilities[]` 必须且只能为空数组；不得借由空值、缺字段或 `null` 表示“无资源依赖”。
  - 当 `resource_dependency_mode=required` 时，`required_capabilities[]` 必须为非空、去重数组；数组值只能来自 `FR-0015` 已批准共享词汇 `account`、`proxy`。
  - 当前双参考适配器共享声明基线固定为：
    - `adapter_key=xhs`、`capability=content_detail`、`resource_dependency_mode=required`、`required_capabilities=[account, proxy]`
    - `adapter_key=douyin`、`capability=content_detail`、`resource_dependency_mode=required`、`required_capabilities=[account, proxy]`
  - formal spec 必须允许 `resource_dependency_mode=none` 存在，以容纳未来经共享证据验证后的非资源路径；但 `v0.5.0` 不要求双参考适配器当前基线必须提供 `none` 样本声明。
- 契约需求：
  - `adapter_key` 必须是非空字符串，用于把声明绑定到单一 adapter；声明 carrier 不承担 provider、tenant 或 runtime backend 选择语义。
  - `capability` 必须是非空字符串，且当前只允许复用 adapter-facing 共享 capability 词汇 `content_detail`；不得把 `content_detail_by_url`、`verify_fp`、`xsec_token` 或其他平台前置值误写成声明层 capability。
  - `required_capabilities[]` 表达“Core 在进入该 adapter capability 前必须满足的共享受管资源能力集合”，而不是 provider 配置、技术栈选择或 adapter 内部 fallback 提示。
  - `evidence_refs[]` 必须是非空、去重字符串数组；其每个成员都必须引用 `FR-0015` 已批准共享证据，不得引用本 FR 私有 research、临时实现注释、单平台私有实验或未审批的外部材料。
  - `evidence_refs[]` 的用途是证明该声明确实来自共享证据，而不是作为描述性备注；若无法绑定到 `FR-0015` 共享证据，则该声明必须视为 contract violation 并 fail-closed。
  - 本 FR 明确禁止以下字段或同义扩张进入 canonical carrier：
    - `preferred_capabilities`
    - `optional_capabilities`
    - `fallback`
    - `priority`
    - `provider_selection`
    - Playwright / CDP / Chromium / browser provider 一类技术实现字段
  - 本 FR 只冻结声明面，不承诺 provider 选择、能力优先级、部分满足、降级执行或技术实现抽象；这些方向若未来需要引入，必须通过新的 formal spec 明确推进。
- 非功能需求：
  - 声明 contract 必须保持 Core / Adapter / provider 实现无关，只收敛“是否需要共享受管资源”这一层最小语义。
  - 声明 contract 必须能被 reviewer、guardian 与后续实现 Work Item 稳定消费，不允许把共享资源依赖重新退回 runtime 私有常量或 adapter 私有说明。
  - 本 FR 必须服务 `v0.5.0` 的“收敛抽象而不凭空扩张抽象”目标；证据不足时必须保持最小声明模型，而不是提前设计大全 schema。

## 约束

- 阶段约束：
  - 本事项只服务 `v0.5.0` 的适配器资源需求声明，不提前进入 provider selection、复杂能力匹配、策略 DSL 或浏览器资源抽象。
  - 只有当双参考适配器都暴露出同类资源语义时，才允许在 `required_capabilities[]` 中出现对应共享词汇；当前批准词汇仅 `account`、`proxy`。
- 架构约束：
  - `FR-0013` 只定义声明层；资源生命周期 truth 继续由 `FR-0010` 持有，Core 注入 bundle / Adapter 禁止自行来源化资源的执行边界继续由 `FR-0012` 持有。
  - `FR-0013` 只能引用 `FR-0015` 的共享能力词汇与共享证据，不得在 research.md 或实现 PR 中另建第二套共享证据真相。
  - formal spec 与实现 PR 必须分离；本 FR 只冻结 requirement，不混入 runtime / tests 改动。

## GWT 验收场景

### 场景 1

Given `adapter_key=xhs`、`capability=content_detail` 的声明以 `resource_dependency_mode=required` 绑定 `required_capabilities=[account, proxy]`，且 `evidence_refs[]` 全部来自 `FR-0015` 已批准共享证据  
When reviewer 或后续实现 Work Item 消费该声明  
Then 该执行路径必须被视为进入 adapter 前需要同时满足 `account` 与 `proxy` 的共享受管资源依赖

### 场景 2

Given `adapter_key=douyin`、`capability=content_detail` 的声明以 `resource_dependency_mode=required` 绑定 `required_capabilities=[account, proxy]`  
When Core 侧后续实现把声明映射到资源匹配输入  
Then 它只能要求 `account` 与 `proxy` 两个已批准共享能力，而不能自行追加 browser provider、sign service 或其他技术字段

### 场景 3

Given 某条声明把 `resource_dependency_mode` 设为 `none`  
When formal spec 校验其字段形状  
Then `required_capabilities[]` 必须且只能是空数组，而不是 `null`、缺字段或带有任何能力值

### 场景 4

Given 某条声明把 `resource_dependency_mode` 设为 `required`  
When formal spec 校验其字段形状  
Then `required_capabilities[]` 必须为非空、去重数组，且只能出现 `account`、`proxy`

### 场景 5

Given 某条声明包含 `preferred_capabilities`、`optional_capabilities`、`fallback`、`priority`、`provider_selection` 或 Playwright/CDP/Chromium 字段  
When 该声明进入 formal review  
Then 它必须被视为越过 `v0.5.0` 边界的 contract violation，而不是合法扩展

### 场景 6

Given 某条声明的 `evidence_refs[]` 为空、重复、或引用 `FR-0015` 之外的私有材料  
When formal spec 校验其证据绑定  
Then 该声明必须 fail-closed，因为它无法证明自己来自已批准共享证据

## 异常与边界场景

- 异常场景：
  - `resource_dependency_mode=required` 但 `required_capabilities[]` 为空、重复、形状不合法或包含 `account`、`proxy` 之外的值时，必须视为 contract violation。
  - `resource_dependency_mode=none` 但 `required_capabilities[]` 非空时，必须视为 contract violation。
  - `evidence_refs[]` 缺失、为空、重复或无法证明来自 `FR-0015` 共享证据时，必须视为 contract violation。
- 边界场景：
  - 本事项允许声明 carrier 出现 `none`，但不要求当前双参考适配器共享基线必须立即提供 `none` 样本。
  - 本事项只冻结最小声明字段，不定义 target_type、collection_mode、operation 级 carrier；这些执行轴如需出现在实现映射层，必须由后续事项基于本 FR 进行受控消费，而不是反向改写本 FR 的 carrier。
  - 本事项不允许以“便于实现”为理由把平台私有前置参数或技术实现字段直接提升到 `required_capabilities[]`。

## 验收标准

- [ ] formal spec 明确冻结 `AdapterResourceRequirementDeclaration` 作为 canonical declaration carrier
- [ ] formal spec 明确冻结 `adapter_key`、`capability`、`resource_dependency_mode`、`required_capabilities[]`、`evidence_refs[]` 五个固定字段
- [ ] formal spec 明确冻结 `resource_dependency_mode` 只允许 `none` / `required`
- [ ] formal spec 明确冻结 `none => required_capabilities=[]` 与 `required => required_capabilities` 非空、去重且只允许 `account` / `proxy`
- [ ] formal spec 明确要求每条声明都必须绑定 `FR-0015` 已批准共享证据
- [ ] formal spec 明确禁止 `preferred_capabilities`、`optional_capabilities`、`fallback`、`priority`、`provider_selection` 与技术实现字段进入 canonical carrier
- [ ] formal spec 明确写出当前双参考适配器共享声明基线与允许 `none` 的边界

## 依赖与外部前提

- 外部依赖：
  - `FR-0010` 已冻结最小共享资源类型与 lifecycle 主 contract
  - `FR-0012` 已冻结 Core 注入 bundle / Adapter 资源边界
  - `FR-0015` 已批准共享能力词汇 `account`、`proxy` 与可被引用的共享证据
- 上下游影响：
  - 后续 runtime / matcher 实现只能消费本 FR 的最小声明 carrier，不得在实现层反向新增字段
  - 相邻 FR 若要扩张声明词汇、证据真相或 provider 选择语义，必须通过新的 formal spec 推进
