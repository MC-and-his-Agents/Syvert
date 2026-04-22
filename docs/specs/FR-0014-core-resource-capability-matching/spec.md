# FR-0014 Core resource capability matching

## 关联信息

- item_key：`FR-0014-core-resource-capability-matching`
- Issue：`#190`
- item_type：`FR`
- release：`v0.5.0`
- sprint：`2026-S18`

## 背景与目标

- 背景：`FR-0010` 与 `FR-0012` 已冻结最小资源生命周期和 Core 注入边界，但 `v0.5.0` 还缺少一层正式的“能力满足性判断” contract。若这层 contract 不先冻结，Core 很容易把 matcher 漂移成 provider selector、资源编排器或技术绑定检查器。
- 目标：为 `v0.5.0` 冻结 Core 资源能力匹配的最小 contract，只判断当前资源能力集合是否满足 `FR-0013` 已声明的全部必需能力；不引入排序、偏好、fallback、provider 选择或技术实现绑定。

## 范围

- 本次纳入：
  - 冻结 canonical matching input `ResourceCapabilityMatcherInput`
  - 冻结 canonical matching output `ResourceCapabilityMatchResult`
  - 冻结“全部满足才算 `matched`”的匹配规则
  - 冻结 matcher 输入违法与资源不足的错误口径边界
- 本次不纳入：
  - provider 选择、调度策略、资源编排 DSL
  - `FR-0010` 的 bundle / lease 生命周期语义
  - `FR-0012` 的 resource bundle 注入边界
  - runtime acquire / release 实现
  - browser / Playwright / CDP / Chromium 技术绑定

## 需求说明

- 功能需求：
  - Core 资源能力匹配的 canonical 输入固定为 `ResourceCapabilityMatcherInput`。
  - `ResourceCapabilityMatcherInput` 至少必须包含：
    - `task_id`
    - `adapter_key`
    - `capability`
    - `requirement_declaration`
    - `available_resource_capabilities`
  - `task_id` 必须是非空字符串；matcher 不得脱离 task-bound 运行时上下文工作。
  - `adapter_key` 与 `capability` 必须与 `requirement_declaration` 中的同名字段一致；若不一致，输入违反 contract。
  - `requirement_declaration` 必须满足 `FR-0013` 已冻结的 `AdapterResourceRequirementDeclaration` contract；matcher 不得接受影子声明 carrier。
  - `available_resource_capabilities` 必须是去重集合；元素只能来自 `FR-0015` 已批准词汇。当前 `v0.5.0` 只允许 `account`、`proxy`。
  - Core 资源能力匹配的 canonical 输出固定为 `ResourceCapabilityMatchResult`。
  - `ResourceCapabilityMatchResult` 至少必须包含：
    - `task_id`
    - `adapter_key`
    - `capability`
    - `match_status`
  - `match_status` 在 `v0.5.0` 只允许两类结论：
    - `matched`
    - `unmatched`
  - 匹配规则固定为“全量满足”：
    - 当 `requirement_declaration.resource_dependency_mode=required` 时，只有在 `available_resource_capabilities` 覆盖全部 `required_capabilities` 时才允许返回 `matched`
    - 只满足其中一部分能力时，必须返回 `unmatched`
    - 不允许 partial match
  - 当 `requirement_declaration.resource_dependency_mode=none` 且 `required_capabilities=[]` 时，matcher 必须返回 `matched`；这是非资源路径的唯一 canonical 处理方式。
  - matcher 只负责判断“能力集合是否满足声明”，不得选择 provider、不得绑定具体资源实例、不得决定 acquire 次序，也不得引入排序、打分、偏好或 fallback。
  - matcher 不得在本 FR 中重新定义 `FR-0010` 的 bundle / lease / slot 语义；“能力满足”与“资源 acquire 成功”不是同一个 contract。
  - matcher 不得在本 FR 中重新定义 `FR-0012` 的注入边界；资源是否由 Core 注入、何时注入，继续由 `FR-0012` 持有。
- 契约需求：
  - 以下情况必须归类为 `runtime_contract`，并固定 `error.code=invalid_resource_requirement`：
    - `requirement_declaration` 形状非法
    - `requirement_declaration` 中出现未被 `FR-0015` 批准的能力标识
    - `task_id`、`adapter_key`、`capability` 与 `requirement_declaration` 上下文不一致
    - `available_resource_capabilities` 形状非法、重复、或出现未批准能力标识
  - 以下情况不得视为 `invalid_resource_requirement`：
    - 声明本身合法，但当前 `available_resource_capabilities` 无法满足全部 `required_capabilities`
  - 对于上述“声明合法但资源能力集合不满足”的情况，matcher 必须返回 `ResourceCapabilityMatchResult(match_status=unmatched)`；若 shared runtime 需要把它外显为失败 envelope，则错误口径必须继续使用 `resource_unavailable`。
  - matcher 结果不得携带 provider id、resource_id、排序分数、优先级或 fallback 候选；这些字段一旦出现，就意味着 matcher scope 漂移。
  - matcher 只消费 `FR-0013` 声明与 `FR-0015` 词汇，不得在匹配阶段自行批准新能力名。
- 非功能需求：
  - 匹配 contract 必须 fail-closed；任何无法证明声明合法或输入一致的情况，都不得宽松返回 `matched`。
  - 匹配结果必须保持确定性；相同输入不得依赖随机排序、外部 provider 状态或技术实现细节得出不同结论。
  - `FR-0014` 只冻结“能力匹配前置判断”，不提前承诺多 provider 策略、资源编排或技术桥接。

## 约束

- 阶段约束：
  - 本事项只服务 `v0.5.0` 的 formal spec closeout，不混入 runtime、测试代码、release / sprint 索引或根级治理修正。
  - 本事项必须消费 `FR-0015` 已批准词汇与 `FR-0013` 已冻结声明形状，不得反向改写它们。
- 架构约束：
  - Core 继续拥有资源能力匹配语义；matcher 不得把判断责任下放回 adapter。
  - formal spec 与实现 PR 必须分离；`#193` 只冻结 input / output / fail-closed 规则，不实现 runtime matcher。
  - 本 FR 不得重开 `FR-0010` 的 bundle / lease / slot 命名，也不得重开 `FR-0012` 的注入边界。

## GWT 验收场景

### 场景 1

Given `requirement_declaration=required + [account, proxy]` 且 `available_resource_capabilities=[account, proxy]`  
When Core 执行资源能力匹配  
Then matcher 必须返回 `ResourceCapabilityMatchResult(match_status=matched)`

### 场景 2

Given `requirement_declaration=required + [account, proxy]` 但 `available_resource_capabilities=[account]`  
When Core 执行资源能力匹配  
Then matcher 必须返回 `unmatched`，而不是 partial match 或自动 fallback

### 场景 3

Given `requirement_declaration.resource_dependency_mode=none` 且 `required_capabilities=[]`  
When Core 执行资源能力匹配  
Then matcher 必须返回 `matched`，且不得强行要求额外资源能力

### 场景 4

Given `requirement_declaration` 中包含未被 `FR-0015` 批准的能力标识，或 matcher 输入中的 `adapter_key / capability` 与声明不一致  
When Core 执行资源能力匹配  
Then matcher 必须按 `runtime_contract + invalid_resource_requirement` fail-closed，而不是返回 `unmatched`

### 场景 5

Given matcher 输入合法，但当前资源能力集合没有覆盖全部 `required_capabilities`  
When shared runtime 把 matcher 结论映射到外部失败 envelope  
Then 失败口径必须继续使用 `resource_unavailable`，而不是把合法声明误报成 `invalid_resource_requirement`

## 异常与边界场景

- 异常场景：
  - 若 `available_resource_capabilities` 含有重复项、未知能力或影子能力名，matcher 输入不满足 contract。
  - 若 `requirement_declaration` 缺字段、包含禁止字段，或与 `task_id / adapter_key / capability` 上下文对不上，matcher 必须直接失败。
  - 若 matcher 尝试返回 provider 候选、排序分数或 partial match 结果，则视为 scope 漂移与 contract violation。
- 边界场景：
  - `FR-0014` 只判断能力集合满足性，不保证具体资源实例一定可成功 acquire；实例级冲突仍由 `FR-0010` 生命周期路径处理。
  - `FR-0014` 不扩展为 scheduler、provider selector 或资源编排 DSL。
  - `FR-0014` 不以 Playwright、CDP、Chromium、浏览器 profile 或代理 provider 类型作为匹配输入字段。

## 验收标准

- [ ] formal spec 明确冻结 `ResourceCapabilityMatcherInput` 与 `ResourceCapabilityMatchResult`
- [ ] formal spec 明确冻结 `matched / unmatched` 两类结论与“全量满足”规则
- [ ] formal spec 明确冻结 `invalid_resource_requirement` 与 `resource_unavailable` 的口径边界
- [ ] formal spec 明确禁止排序、打分、偏好、fallback、provider 选择与技术绑定字段
- [ ] formal spec 明确禁止 matcher 反向改写 `FR-0010` / `FR-0012` 已冻结 contract

## 依赖与外部前提

- 外部依赖：
  - `#188` 已把 `v0.5.0` 定义为资源需求声明、能力匹配与双参考证据收口阶段
  - `#190` 作为本 FR 的 canonical requirement 容器已建立，并绑定 `#193`
  - `FR-0013` 已定义 `AdapterResourceRequirementDeclaration` 的 canonical 声明形状
  - `FR-0015` 已冻结 `account`、`proxy` 作为当前唯一批准的共享资源能力词汇
  - `FR-0010` 与 `FR-0012` 已分别冻结资源生命周期与注入边界，是本 FR 的相邻上游约束
- 上下游影响：
  - runtime matcher 实现 Work Item 必须直接消费本 FR 冻结的输入 / 输出 / 错误边界
  - `FR-0013` 与 `FR-0015` 不得被 runtime matcher 实现反向改写
