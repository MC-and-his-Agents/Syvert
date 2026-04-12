# FR-0006 v0.2.0 adapter contract test harness

## 关联信息

- item_key：`FR-0006-adapter-contract-test-harness`
- Issue：`#66`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`

## 背景与目标

- 背景：`v0.1.0` 已证明同一 Core 主路径可以承载两个真实参考适配器，但 `v0.2.0` 需要把“能跑”推进到“可验证”。如果 Core 契约只能通过真实平台验证，就会把登录态、签名、内容波动与平台可用性混进 Core 契约判断，导致 contract 回归不可重复、不可稳定归因。
- 目标：冻结一套 adapter contract test harness 的 formal spec，使 Core 能在不依赖真实平台的前提下验证统一 adapter contract、结果 envelope 语义与关键失败分支，并为后续实现 PR 提供清晰、有限的落地范围。

## 范围

- 本次纳入：
  - adapter contract test harness 的职责边界
  - fake adapter 在契约验证中的语义定位
  - Core 在受控输入下验证统一 adapter contract 的最小验证面
  - 验证工具、harness、fake adapter 三者之间的角色关系
  - harness 可提供的保证级别，以及与真实平台测试、参考适配器回归的边界
- 本次不纳入：
  - `InputTarget`、`CollectionPolicy`、错误模型或 adapter registry 本身的正式语义定义
  - 真实平台测试方案、双参考适配器回归流程或版本 gate 编排
  - fake adapter、验证工具或 harness 的具体代码结构、测试框架选型、CLI 形态
  - 新能力类型、新平台接入或真实平台流量录制机制

## 需求说明

- 功能需求：
  - 必须存在一套受控的 contract harness，使 Core 能在不执行真实平台请求的情况下运行 adapter contract 验证。
  - harness 必须允许把一个或多个 fake adapter 接入到 Core 的标准 adapter 宿主路径，而不是绕过 Core 直接断言内部函数。
  - fake adapter 必须能够声明自身支持的 capability，并以受控方式返回成功态或失败态结果，用于驱动 Core 契约分支验证。
  - 验证工具必须负责组织契约样例、触发 harness 执行并输出可判定的验证结果；它不直接定义 Core 契约语义。
  - harness 与验证工具合起来必须覆盖四类最小结果：通过、合法失败、contract violation、执行前置不满足。
- 契约需求：
  - harness 验证的对象固定为 Core 与 adapter 之间已经批准的统一运行时 contract，而不是某个平台的抓取正确性。
  - `FR-0002` 提供 success / failed envelope 的基础结构；`FR-0005` 提供 `invalid_input`、`unsupported`、`runtime_contract`、`platform` 的错误分类与 capability / registry 语义边界；本 FR 只消费这些上位 contract，不重新定义它们。
  - fake adapter 是契约测试替身，不是参考适配器、也不是平台模拟器；它只表达为验证 contract 所必需的最小行为。
  - fake adapter 必须通过与真实 adapter 同类的注册/发现入口被 Core 调用；允许使用受控测试注册表，但不得要求 Core 为 fake adapter 引入平台特定分支。
  - harness 必须能验证 Core 对 adapter 成功返回的 envelope 约束，包括 `raw payload` 与 `normalized result` 同时存在这一统一 contract 前提。
  - harness 必须能验证 Core 对 adapter 失败返回的统一 envelope 处理语义，但不在本 FR 中重新定义错误分类枚举或错误对象字段。
  - 当 fake adapter 返回缺失必填字段、结构非法，或 adapter 声明与实际行为不一致时，harness 必须能证明该样例不满足已批准 contract；这里的 `contract violation` 是验证工具层的判定标签，不是新的运行时 `error.category`。
  - 对于运行时已经按上位 contract 返回的合法失败 envelope，验证工具必须将其识别为“合法失败样例已按预期发生”，而不是 `contract violation`；例如 capability 不受支持且返回 `unsupported`、输入不合法且返回 `invalid_input`，都属于合法失败。
  - `执行前置不满足` 固定表示验证工具或 harness 在进入 Core 执行前发现样例装配、测试替身注册或测试期输入前提缺失；它不是 Core 运行时结果，也不替代 `invalid_input` / `unsupported` / `runtime_contract` 的上位语义。
  - 验证工具输出至少必须能区分：通过、合法失败、contract violation、执行前置不满足四类结果，并能把失败归因到样例/断言级别。
  - harness 的样例输入必须围绕已批准 capability 的最小公共 contract 组织，不得为方便测试而引入只服务 fake adapter 的生产字段。
  - harness 必须允许后续实现为同一 contract 复用多组 fake adapter 样例，但本 FR 不要求定义录制回放、随机数据生成或跨进程协议。
- 非功能需求：
  - contract 验证必须具备可重复性，不受真实平台内容变化、登录态、签名、网络抖动影响。
  - contract 失败的归因必须清晰，能够区分 Core contract 处理问题与真实平台问题。
  - harness 必须保持实现边界有限，后续实现 PR 只需补齐 fake adapter、验证工具和必要测试宿主，不需要顺带改写真实参考适配器。
  - fake adapter 的存在不得成为 Core 新的生产依赖；其语义仅存在于验证场景。

## 约束

- 阶段约束：
  - 当前事项服务于 `v0.2.0` “把能跑推进到可验证”的阶段目标。
  - 本 FR 只定义 contract harness 基座，不把双参考适配器回归 gate、平台泄漏检查 gate 写成本事项主体语义。
- 架构约束：
  - Core 负责运行时 contract 判定与统一 envelope 处理；fake adapter 只负责按受控样例暴露 contract 输入/输出。
  - 平台 URL 解析、签名、Cookie、真实响应解析、反爬对抗与页面回放都不属于 fake adapter 责任。
  - harness 必须验证“Core 是否正确承载统一 adapter contract”，而不是重新定义 adapter registry、错误模型或 capability 体系。

## GWT 验收场景

### 场景 1

Given Core 注册了一个声明支持既有 capability 的 fake adapter，且该 fake adapter 返回满足已批准 contract 的成功结果  
When 验证工具通过 harness 驱动一次 contract 样例执行  
Then 结果必须被判定为通过，且验证结论能证明 Core 在不访问真实平台时仍正确承载统一 success envelope

### 场景 2

Given fake adapter 返回缺失 `raw` 或 `normalized` 的成功结果，或返回结构非法的结果 envelope  
When harness 执行对应契约样例  
Then 验证结论必须把该结果判定为验证工具层的 `contract violation`，并明确它不是新的运行时错误分类

### 场景 3

Given fake adapter 明确返回受控失败结果，或声明的 capability 与收到的调用不匹配  
When harness 通过 Core 执行该样例  
Then 验证结果必须能观测到统一失败处理路径，并区分“合法失败 envelope”与“contract violation”两类结果

### 场景 4

Given 某个验证样例缺少运行该样例所必需的测试替身注册、样例夹具或 harness 级前置输入  
When 验证工具准备执行该样例  
Then 该样例必须被判定为 `执行前置不满足`，且不得冒充 Core 返回的 `invalid_input`、`unsupported` 或其他运行时失败

## 异常与边界场景

- 异常场景：
  - 若验证样例本身缺少 contract 必需输入，验证工具必须在进入 adapter 执行前给出可归因的前置失败，而不是产出模糊结论。
  - 若 fake adapter 需要依赖真实网络、真实平台 cookie 或外部签名环境，说明该样例已越出本 FR 的 contract harness 边界。
  - 若 Core 只能在绕过标准 adapter 宿主路径时才能通过样例，说明该 harness 不能作为 contract 验证基座。
- 边界场景：
  - harness 只覆盖 Core 与 adapter 共享 contract 的语义正确性，不覆盖真实平台可达性、页面解析正确性或双参考适配器业务回归。
  - fake adapter 可以最小化实现行为，但不得演变为真实平台适配器的第二份影子实现。
  - 本 FR 不要求定义回归 gate 编排、版本放行策略或 CI 拓扑；这些事项由后续回归/门禁工作项处理。
  - 若后续实现发现现有 contract 本身存在缺口，应回到对应 formal spec 审查链路，而不是在 harness 实现中隐式补定义。

## 验收标准

- [ ] adapter contract test harness 的职责、纳入范围与排除范围已冻结
- [ ] fake adapter 的语义定位已明确为 contract test double，而非参考适配器或平台模拟器
- [ ] Core 在不依赖真实平台时可验证的 contract 面已明确，包括通过、合法失败、contract violation、执行前置不满足四类最小结果
- [ ] 验证工具、harness 与 fake adapter 的角色关系已明确，且已区分验证工具分类与运行时错误语义
- [ ] harness 可提供的保证级别已明确，并与真实平台测试、参考适配器回归、版本门禁保持边界分离
- [ ] formal spec 已限制后续实现 PR 的范围，不要求在同一轮引入真实平台回放、回归 gate 或相邻 FR 的语义扩张

## 依赖与外部前提

- 外部依赖：
  - GitHub Issue `#66` 作为当前 FR 真相源入口
  - `FR-0002` 已冻结最小 adapter contract，作为本 FR 的上位 contract 前提
  - `FR-0005` 已冻结标准化错误模型与 adapter registry contract，作为本 FR 的失败 envelope 与 capability 边界前提
  - `vision.md` 与 `docs/roadmap-v0-to-v1.md` 对 `v0.2.0` 的阶段边界保持有效
- 上下游影响：
  - 后续 implementation PR 需要在本 spec 边界内补齐 fake adapter、contract harness 与验证工具
  - 真实平台测试、双参考适配器回归与版本 gate 应消费本 FR 的产出，但不得反向改写本 FR 的主体语义
