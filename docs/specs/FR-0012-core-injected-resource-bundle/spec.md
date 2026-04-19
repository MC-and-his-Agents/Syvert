# FR-0012 Core-injected resource bundle and Adapter boundary

## 关联信息

- item_key：`FR-0012-core-injected-resource-bundle`
- Issue：`#167`
- item_type：`FR`
- release：`v0.4.0`
- sprint：`2026-S17`

## 背景与目标

- 背景：`v0.4.0` 的资源系统不仅要定义资源生命周期，还要把“资源由谁准备、谁注入、谁负责释放/失效”冻结成清晰边界。若 Adapter 仍能自行读取本地会话、拉取代理或另找账号，Core 就无法成为运行时语义的拥有者。
- 目标：为 `v0.4.0` 冻结 Core 向 Adapter 执行注入资源包的 formal contract，明确 Adapter 禁止自行来源化执行资源的边界，以及 Adapter 如何在不改写资源生命周期主 contract 的前提下消费注入 bundle。

## 范围

- 本次纳入：
  - 冻结 Adapter 执行时接收 `ResourceBundle` 的最小注入 carrier
  - 冻结“Core 先 acquire，再调用 Adapter；Core 最终 release/invalidates”的执行边界
  - 冻结 Adapter 可以消费哪些注入字段、可以反馈哪些资源处置提示
  - 冻结“Adapter 不自行来源化执行资源”的禁止性约束
- 本次不纳入：
  - 资源生命周期主接口、状态机与使用日志 schema
  - 资源能力匹配、需求声明与调度策略
  - 浏览器 provider、外部代理 provider 或完整资源调度器实现
  - 参考 Adapter 的具体改造代码

## 需求说明

- 功能需求：
  - 当某条执行路径被判定需要受管资源时，Core 必须先完成 `FR-0010` 所定义的 `acquire`，得到合法 `ResourceBundle` 后，才能调用 Adapter。
  - Adapter 执行边界中的 `resource_bundle` 必须复用 `FR-0010` 已冻结的 canonical carrier：至少包含 `bundle_id`、`lease_id`、`task_id`、`adapter_key`、`capability`、`requested_slots` 与已填充的 slot 资源实体。`FR-0012` 不得重新定义第二套 bundle 顶层字段。
  - Adapter 允许在单次执行内消费 `resource_bundle` 中各 slot 的 `material`，并把它们转译为平台私有的 header、cookie、session、client 或网络配置；这些派生物属于 Adapter 内部临时执行材料，不得回写为新的共享资源 truth。
  - 若当前执行路径被声明为资源依赖路径，而 Core 无法提供合法完整的 `resource_bundle`，Core 必须在调用 Adapter 之前 fail-closed；Adapter 不得以“缺 bundle 时自行补资源”的方式继续执行。
  - 若当前执行路径不依赖受管资源，Core 可以显式注入空 bundle / `null` bundle，但这一事实必须由 Core 决定，而不是由 Adapter 在运行时自行判定后绕过。
  - Adapter 在执行过程中只允许向 Core 返回“资源处置提示”，例如当前 bundle 应按 `AVAILABLE` 或 `INVALID` 收口；真正的 `release` / 状态推进仍只能由 Core 执行。
  - 资源处置提示若存在，最小 payload 必须包含：
    - `lease_id`
    - `target_status_after_release`
    - `reason`
  - `target_status_after_release` 在 `v0.4.0` 只允许 `AVAILABLE` 或 `INVALID`，并且必须复用 `FR-0010` 已冻结的 release 语义。
- 契约需求：
  - Adapter 明确被禁止的行为包括：
    - 自行从本地文件、环境变量、数据库、远程 provider 或其他隐式来源选择账号/代理作为执行资源
    - 在注入 bundle 之外再额外拉取第二套代理、账号或会话资源作为主执行材料
    - 直接改写共享资源状态、lease 或 tracing truth
  - Adapter 明确被允许的行为包括：
    - 消费 Core 已注入的 `resource_bundle`
    - 基于 bundle `material` 派生单次执行内的平台私有运行对象
    - 把资源处置建议反馈给 Core，由 Core 决定最终 release/invalidates
  - Core 必须把“资源是否已满足”作为 Adapter 调用前的 host-side 前置条件，而不是把它下放给 Adapter 在平台路径里临时补救。
  - 一旦 `resource_bundle` 的形状、`lease_id`、slot 填充情况与当前 task 不一致，Core 必须在调用 Adapter 前按 `runtime_contract` fail-closed。
  - “Adapter 不自行来源化执行资源”是最小架构边界，而不是 best-effort 建议；若实现违反该边界，应被视为 contract violation / platform leakage。
- 非功能需求：
  - 注入 contract 必须保持实现无关，不绑定某个具体浏览器框架、代理库或认证 SDK。
  - 本 FR 只冻结最小注入边界，不提前规定 Adapter 如何声明资源需求或如何做复杂能力匹配。
  - 该边界必须足以支撑后续 reference adapter 改造与平台泄漏检查，而不要求 `v0.4.0` 同时交付完整 provider 生态。

## 约束

- 阶段约束：
  - 本事项只服务 `v0.4.0` 的“Core 注入资源包、Adapter 不自行来源化资源”目标，不提前进入 `v0.5.0` 的资源需求声明与能力匹配。
  - 本事项不重写 `FR-0010` 的 bundle/lease/status 主 contract，也不重写 `FR-0011` 的 tracing schema。
- 架构约束：
  - Core 负责运行时资源语义与最终状态收口；Adapter 负责平台语义与对注入 bundle 的执行内消费。
  - formal spec 与实现 PR 必须分离；`#168` 只冻结边界 contract，不混入 reference adapter 改造代码。
  - 注入 boundary 必须与平台泄漏检查目标一致：Core 主执行路径不得退化为“Adapter 各自带私有资源来源器”。

## GWT 验收场景

### 场景 1

Given 某个 task 需要 `account` 与 `proxy` 两个受管资源，且 Core 已成功 acquire 到合法 `ResourceBundle`  
When Core 调用 Adapter  
Then Adapter 必须接收到同一 `lease_id`、`bundle_id`、`task_id` 绑定的注入 bundle，而不是自行再拉取第二套账号或代理

### 场景 2

Given 某个 task 被声明为资源依赖路径，但 Core 无法提供完整合法的 `ResourceBundle`  
When Core 准备调用 Adapter  
Then Core 必须在进入 Adapter 前 fail-closed，而不能把“缺资源时自行补齐”的责任下放给 Adapter

### 场景 3

Given Adapter 基于注入的账号 material 构造出平台私有 session，并基于注入的 proxy material 构造出网络配置  
When Adapter 完成一次执行  
Then 这些派生对象只能被视为单次执行内的临时材料，而不能成为新的共享资源 truth

### 场景 4

Given Adapter 在执行过程中判断当前 bundle 不可继续复用  
When Adapter 把 `lease_id`、`target_status_after_release=INVALID` 与 `reason` 返回给 Core  
Then 最终的 release 与状态推进仍必须由 Core 执行，而不是由 Adapter 直接改写共享资源状态

### 场景 5

Given Adapter 尝试从本地 session 文件、环境变量或远程 provider 读取未注入的账号/代理作为主执行资源  
When 该行为进入执行路径  
Then 它必须被视为违反“Adapter 不自行来源化执行资源”的 contract，而不是合法 fallback

## 异常与边界场景

- 异常场景：
  - 若 `resource_bundle.lease_id` 与当前 task 不匹配，Core 必须在调用 Adapter 前拒绝执行。
  - 若 Adapter 收到的 bundle slot 与 `requested_slots` 不一致，Core 必须把它视为 host-side contract 破损，而不是要求 Adapter 自行修复。
  - 若 Adapter 直接释放、失效或改写共享资源状态，则违反 Core 拥有生命周期语义的架构边界。
- 边界场景：
  - 本事项允许 Adapter 把注入资源转换为平台私有运行对象，但这些对象只在单次执行边界内有效。
  - 本事项允许 Core 明确注入空 bundle / `null` bundle 给“不依赖受管资源”的执行路径；是否依赖由 Core 决定，而不是 Adapter 自行猜测。
  - 本事项不定义资源需求 DSL、优先级、provider 选择或浏览器桥接实现。

## 验收标准

- [ ] formal spec 明确冻结 Core 在 Adapter 调用前注入 `ResourceBundle` 的最小 contract
- [ ] formal spec 明确冻结 Adapter 可消费、可反馈与不可越权的边界
- [ ] formal spec 明确禁止 Adapter 自行来源化执行资源
- [ ] formal spec 明确要求资源缺失或 bundle 失配时由 Core 在调用前 fail-closed
- [ ] formal spec 明确要求最终 release / invalidate 仍由 Core 执行

## 依赖与外部前提

- 外部依赖：
  - `#162` 已把“Core 注入资源包、Adapter 不自行来源化资源”设为 `v0.4.0` 阶段目标
  - `#167` 作为本 FR 的 canonical requirement 容器已建立，并绑定 `#168`
  - `FR-0010` 已冻结 `ResourceBundle` / `ResourceLease` 主 carrier，是本 FR 的直接上游前提
- 上下游影响：
  - reference adapter 改造必须围绕本 FR 冻结的注入 boundary 推进
  - 平台泄漏检查与运行时回归必须以本 FR 的禁止性约束为审查依据
