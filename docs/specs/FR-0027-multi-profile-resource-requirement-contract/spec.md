# FR-0027 Multi-profile resource requirement contract

## 关联信息

- item_key：`FR-0027-multi-profile-resource-requirement-contract`
- Issue：`#294`
- item_type：`FR`
- release：`v0.8.0`
- sprint：`2026-S21`

## 背景与目标

- 背景：`FR-0013`、`FR-0014`、`FR-0015` 在 `v0.5.0` 冻结了单条 `resource_dependency_mode + required_capabilities[]` 声明、全量满足 matcher 与共享能力词汇证据基线。这套 contract 适合最小双参考切片，但已经无法表达“同一 adapter capability 存在多个都合法的资源依赖 profile”这一 `v0.8.0` 现实。
- 目标：为 `v0.8.0` 冻结多 profile 资源依赖声明、matcher `one-of` 满足性判断与 profile 级 evidence 消费边界，使同一 capability 可以声明多个合法 profile，同时保持 fail-closed，不引入排序、自动 fallback、provider 选择或新共享能力词汇。

## 范围

- 本次纳入：
  - 冻结 canonical declaration carrier `AdapterResourceRequirementDeclarationV2`
  - 冻结 canonical profile carrier `AdapterResourceRequirementProfile`
  - 冻结 matcher `one-of matched` 语义与 `invalid_resource_requirement` / `resource_unavailable` 边界
  - 冻结 profile 级 evidence 消费边界，要求 shared profile 只能来自 `FR-0015` 已批准证据
  - 冻结 `v0.8.0` 当前允许的 profile 组合空间只来自 `none`、`account`、`proxy` 三类最小共享能力语义
- 本次不纳入：
  - provider capability offer / compatibility decision
  - profile 优先级、排序、自动 fallback、打分或 provider selector
  - `FR-0010` 资源生命周期与 `FR-0012` Core 注入 bundle 主 contract
  - 新共享能力词汇
  - 第三方 adapter onboarding 细节、SDK 表面与实现代码

## 需求说明

- 功能需求：
  - `AdapterResourceRequirementDeclarationV2` 必须是 `v0.8.0` 及之后 multi-profile requirement 的唯一 canonical declaration carrier；实现不得并行维护第二套影子声明模型。
  - `AdapterResourceRequirementDeclarationV2` 至少必须固定以下字段：
    - `adapter_key`
    - `capability`
    - `resource_requirement_profiles`
  - `adapter_key` 必须是非空字符串，并且当前 declaration 上每一个 profile 引用到的 `ApprovedSharedResourceRequirementProfileEvidenceEntry` 都必须显式批准该 `adapter_key`；未被批准的 adapter 不得借用已批准 tuple 进入 shared contract。
  - `resource_requirement_profiles` 必须是非空数组；数组中的每一项都必须满足 `AdapterResourceRequirementProfile` contract。
  - `AdapterResourceRequirementProfile` 至少必须固定以下字段：
    - `profile_key`
    - `resource_dependency_mode`
    - `required_capabilities`
    - `evidence_refs`
  - 为了让 declaration / matcher / adapter migration 在 `#300` 合入后拥有可直接消费的批准证明，`FR-0027` 同时冻结一个最小 evidence consumer contract：`ApprovedSharedResourceRequirementProfileEvidenceEntry`。
  - `ApprovedSharedResourceRequirementProfileEvidenceEntry` 至少必须固定以下字段：
    - `profile_ref`
    - `capability`
    - `resource_dependency_mode`
    - `required_capabilities`
    - `reference_adapters`
    - `shared_status`
    - `decision`
    - `evidence_refs`
  - `ApprovedSharedResourceRequirementProfileEvidenceEntry` 的字段语义固定为：
    - `profile_ref`：非空、稳定字符串；在当前 approved shared profile carrier 中必须唯一，是 declaration `evidence_refs` 允许引用的 canonical target
    - `capability`：当前只允许 `content_detail`
    - `resource_dependency_mode` / `required_capabilities`：与 declaration profile 的 canonical tuple 完全对齐；比较前必须先做同一套 canonicalization
    - `reference_adapters`：当前必须且只能覆盖 `xhs` 与 `douyin`
    - `shared_status`：沿用 `FR-0015` 已冻结词汇；当前 shared declaration 只接受 `shared`
    - `decision`：沿用 `FR-0015` 的批准词汇，不在 `FR-0027` 另起新枚举；当前 shared declaration 只接受 `approve_for_v0_5_0`
    - `evidence_refs`：非空、去重字符串数组；用于回指 `FR-0015` research / artifact 中更细粒度的双参考证据
  - `#300` 的职责不是替 `FR-0027` 发明新的批准证明 shape，而是把 `FR-0015` 更新到至少能产出上述 `ApprovedSharedResourceRequirementProfileEvidenceEntry`，并补齐 shared / adapter-local / rejected profile truth。
  - `profile_key` 必须是声明内唯一的非空字符串，用于稳定标识一个合法 profile；它只承担声明内追溯与 evidence 对齐职责，不承载优先级或执行顺序语义。
  - `resource_dependency_mode` 在 `v0.8.0` 只允许 `none` 或 `required`。
  - 当 `resource_dependency_mode=none` 时，`required_capabilities` 必须且只能为空数组。
  - 当 `resource_dependency_mode=required` 时，`required_capabilities` 必须是非空、去重数组，元素只能来自 `FR-0015` 已批准共享能力词汇。`v0.8.0` 当前只允许 `account`、`proxy`。
  - profile tuple 的 canonical identity 固定为 `resource_dependency_mode + normalized_required_capabilities`。其中 `normalized_required_capabilities` 指去重后按 `FR-0015` 已批准共享能力词汇顺序规范化的数组；当前顺序固定为 `account`、`proxy`。
  - declaration profile 上的 `evidence_refs` 必须是非空、去重字符串数组；每个引用都必须精确且唯一地命中一个 `ApprovedSharedResourceRequirementProfileEvidenceEntry.profile_ref`，并且该 entry 的 `capability`、`resource_dependency_mode`、`required_capabilities` 必须与 declaration 的 `capability` 和当前 profile tuple 完全一致，同时其 `reference_adapters` 必须覆盖 declaration 的 `adapter_key`；不得引用 adapter 私有注释、运行期临时日志或未批准材料。
  - 同一条 declaration 中允许存在多个合法 profile；这些 profile 表达“任一满足即可执行”的共享 contract，而不是“按顺序尝试”的 fallback 列表。
  - `v0.8.0` 当前允许出现在 shared declaration 空间中的 profile 只允许由以下最小共享能力语义组合构成：
    - `none`
    - `required + [account]`
    - `required + [proxy]`
    - `required + [account, proxy]`
  - 上述组合空间不等于自动批准；只有存在与之完全对齐的 `ApprovedSharedResourceRequirementProfileEvidenceEntry` 时，该 profile 才允许进入 canonical declaration。
  - 同一 declaration 内不得出现语义重复的 profile。若两个 profile 在 canonical tuple 维度上等价，则必须视为重复声明并 fail-closed。
  - matcher 的 canonical 输入必须消费 `AdapterResourceRequirementDeclarationV2`，并以 `available_resource_capabilities` 判断是否满足任一合法 profile。
  - matcher 的 canonical 输出仍只允许：
    - `matched`
    - `unmatched`
  - matcher 规则固定为 `one-of`：
    - 只要存在任一合法 profile 被当前 `available_resource_capabilities` 满足，就必须返回 `matched`
    - 若 declaration 合法，但没有任何 profile 被满足，则必须返回 `unmatched`
    - 不允许 partial match、分数比较、优先级排序、自动 fallback 或“先宽后严”的执行策略
  - 当某个合法 profile 的 `resource_dependency_mode=none` 且 `required_capabilities=[]` 时，该 profile 必须被视为已满足。
- 契约需求：
  - 以下情况必须归类为 `runtime_contract`，并固定 `error.code=invalid_resource_requirement`：
    - declaration 缺少固定字段，或 `resource_requirement_profiles` 为空
    - profile 缺少固定字段、`profile_key` 重复，或 `resource_dependency_mode` 取值非法
    - `required_capabilities` 形状非法、重复、为空但 mode=`required`，或出现未被 `FR-0015` 批准的能力标识
    - `evidence_refs` 为空、重复，或无法解析到 `ApprovedSharedResourceRequirementProfileEvidenceEntry.profile_ref`
    - 任一 `evidence_ref` 命中多个 approval proof，或 approval proof 的 `profile_ref` 在 carrier 中不唯一
    - declaration 中包含无法与 `ApprovedSharedResourceRequirementProfileEvidenceEntry` 在 `capability + resource_dependency_mode + required_capabilities` 上完全对齐的 profile
    - declaration 的 `adapter_key` 不在任一被引用 `ApprovedSharedResourceRequirementProfileEvidenceEntry.reference_adapters` 中
    - matcher 输入的 `adapter_key` / `capability` 与 declaration 上下文不一致
    - `available_resource_capabilities` 形状非法、存在重复项，或出现未被 `FR-0015` 批准的能力标识
  - 以下情况不得视为 `invalid_resource_requirement`：
    - declaration 合法，但当前 `available_resource_capabilities` 没有满足任何合法 profile
  - 对于上述“声明合法但无命中 profile”的情况，matcher 必须返回 `unmatched`；若 shared runtime 把它外显为失败 envelope，错误口径必须继续使用 `resource_unavailable`。
  - declaration、profile 与 matcher surface 都不得引入以下字段或同义扩张：
    - `priority`
    - `fallback`
    - `preferred_profiles`
    - `optional_capabilities`
    - `provider_selection`
    - `provider_offer`
    - 任何 Playwright / CDP / Chromium / browser profile / network tier 一类技术字段
  - `FR-0027` 只冻结 shared contract，不允许把 `adapter_only` 宽松路径直接塞进 canonical declaration。`adapter_only / rejected` profile 的完整判定真相继续由 `FR-0015` evidence follow-up 持有，但 shared declaration 能否落地，只以这里冻结的 approved shared profile entry contract 为准。
  - `FR-0027` 是 `v0.8.0` multi-profile requirement 的 governing artifact。`FR-0013` / `FR-0014` / `FR-0015` 继续保留 `v0.5.0` 单声明历史语义；自 `v0.8.0` 起，multi-profile declaration / matcher / proof binding 只以 `FR-0027` 为准。
- 非功能需求：
  - contract 必须 fail-closed；任何无法证明 profile 合法、证据有效或输入一致的情况，都不得宽松返回 `matched`。
  - contract 必须保持 Core / Adapter / Provider 实现无关，只回答“哪些 shared profile 合法、当前能力集合是否命中其中之一”。
  - formal spec 必须让 reviewer、guardian 与后续 `#300/#301/#302` 能直接消费，而不依赖会话上下文补足隐藏前提。
  - formal suite 中 `spec.md`、`data-model.md` 与 `contracts/README.md` 对 matcher 输入违法时的结论必须一致：凡是 proof 不可解析、不唯一、不对齐或不覆盖 declaration adapter 的情况，一律归类为 `runtime_contract + invalid_resource_requirement`。

## 约束

- 阶段约束：
  - 本事项只服务 `v0.8.0` 的多 profile requirement contract，不提前进入 provider compatibility、开放接入 SDK 稳定化或真实外部 provider 验证样本。
  - 本事项不新增共享能力词汇；当前 profile 只能重组 `account`、`proxy` 与 `none`。
- 架构约束：
  - `FR-0010` 继续持有资源生命周期 truth；`FR-0012` 继续持有 Core 注入边界；`FR-0027` 不得重开这两个相邻 contract。
  - profile 级 `shared / adapter_only / rejected` 判定必须回指 `FR-0015` evidence，而不是在 matcher 或 adapter 私有代码中另建真相源。
  - formal spec 与实现 PR 必须分离；`#299` 只冻结 requirement truth，不混入 runtime、adapter 或 evidence artifact 实现。

## GWT 验收场景

### 场景 1

Given `adapter_key=xhs`、`capability=content_detail` 的 declaration 合法包含两个 profile：`required + [account, proxy]` 与 `required + [account]`，且两者都绑定到与其 tuple 完全对齐、并覆盖 `xhs` 的 `ApprovedSharedResourceRequirementProfileEvidenceEntry`  
When matcher 接收到 `available_resource_capabilities=[account]`  
Then matcher 必须返回 `matched`，因为当前能力集合命中了其中一个合法 profile

### 场景 1A

Given `adapter_key=external_adapter` 的 declaration 复用了一个只对 `xhs`、`douyin` 批准的 `ApprovedSharedResourceRequirementProfileEvidenceEntry`  
When formal review 或 runtime validator 校验该 declaration  
Then 它必须按 `invalid_resource_requirement` fail-closed，因为 declaration adapter 不在该 approval proof 的 `reference_adapters` 内

### 场景 2

Given 同一条 declaration 合法包含 `required + [account, proxy]` 与 `required + [account]`  
When matcher 接收到 `available_resource_capabilities=[proxy]`  
Then matcher 必须返回 `unmatched`，因为没有任何合法 profile 被完整满足

### 场景 3

Given 某条 declaration 合法包含 `none` profile 与 `required + [account, proxy]` profile  
When matcher 接收到空的 `available_resource_capabilities`  
Then matcher 必须返回 `matched`，因为 `none` profile 已满足，且这不代表存在优先级或 fallback 语义

### 场景 4

Given 某条 declaration 中出现两个仅 `profile_key` 不同、但 `resource_dependency_mode` 与 `required_capabilities` 等价的 profile  
When 该 declaration 进入 formal review 或 runtime validation  
Then 它必须按 `invalid_resource_requirement` fail-closed，因为同义 profile 重复会破坏 canonical contract

### 场景 5

Given 某条 declaration 中存在 `required + [account]` profile，但该 profile 的 `evidence_refs` 无法回指与 declaration `capability` 和该 profile tuple 完全对齐的 `ApprovedSharedResourceRequirementProfileEvidenceEntry`  
When matcher 或 validator 消费该 declaration  
Then 该 declaration 必须按 `invalid_resource_requirement` fail-closed，而不是把未经 evidence 批准的 profile 视为合法候选

### 场景 6

Given declaration 合法，但当前 `available_resource_capabilities` 既不满足 `required + [account]`，也不满足 `required + [account, proxy]`  
When shared runtime 将 matcher 结论映射到外部失败 envelope  
Then 失败口径必须继续使用 `resource_unavailable`，而不是把合法 declaration 误报成 `invalid_resource_requirement`

## 异常与边界场景

- 异常场景：
  - `resource_requirement_profiles` 为空，或 profile 缺少 `profile_key`、`resource_dependency_mode`、`required_capabilities`、`evidence_refs` 之一时，必须视为 contract violation。
  - `resource_dependency_mode=none` 但 `required_capabilities` 非空，或 `resource_dependency_mode=required` 但 `required_capabilities` 为空时，必须视为 contract violation。
  - declaration / profile / matcher 任何一层出现新能力词汇、优先级字段、fallback 字段或技术实现字段时，必须视为越过 `v0.8.0` 边界。
- 边界场景：
  - `FR-0027` 允许同一 capability 存在多个 shared profile，但不承诺这些 profile 之间存在稳定优先级，也不承诺 runtime 会自动挑选“最好”的资源组合。
  - `FR-0027` 允许 `none` profile 与资源依赖 profile 并存，但这只表示多条都合法，不表示运行时可以先尝试无资源路径、失败后再自动回退到有资源路径。
  - `FR-0027` 不把 `adapter_only` profile 升格为 shared contract；任何只在单平台成立的宽松路径都必须留在 `FR-0015` 的 `adapter_only / rejected` evidence 语义中。

## 验收标准

- [ ] formal spec 明确冻结 `AdapterResourceRequirementDeclarationV2` 与 `AdapterResourceRequirementProfile`
- [ ] formal spec 明确冻结 `ApprovedSharedResourceRequirementProfileEvidenceEntry` 这一 profile approval proof contract
- [ ] formal spec 明确冻结 `resource_requirement_profiles` 非空、多 profile、去重与 evidence 绑定规则
- [ ] formal spec 明确冻结 matcher `one-of matched` / `unmatched` 语义
- [ ] formal spec 明确冻结 `invalid_resource_requirement` 与 `resource_unavailable` 的口径边界
- [ ] formal spec 明确禁止优先级、排序、自动 fallback、provider 选择与技术字段
- [ ] formal spec 明确声明 `FR-0027` 对 `v0.8.0` multi-profile contract 的 version boundary，以及 `FR-0013` / `FR-0014` / `FR-0015` 的历史定位

## 依赖与外部前提

- 外部依赖：
  - `FR-0010` 已冻结最小资源生命周期
  - `FR-0012` 已冻结 Core 注入 bundle 与 Adapter 资源边界
  - `FR-0013` / `FR-0014` / `FR-0015` 已提供 `v0.5.0` 单声明基线，作为本事项的历史输入
  - `#291` 已把 `v0.8.0` 的开放接入边界、Adapter / Provider 兼容性判断方向与非目标写入 planning / decision truth
- 上下游影响：
  - `#300` 必须基于本 FR 的 profile contract 刷新 `FR-0015` evidence truth
  - `#301` 必须基于本 FR 的 `one-of` 语义更新 matcher / runtime implementation
  - `#302` 必须基于本 FR 的 declaration carrier 迁移 reference adapter baseline
