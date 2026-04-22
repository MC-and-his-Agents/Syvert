# FR-0015 Dual-reference resource capability evidence

## 关联信息

- item_key：`FR-0015-dual-reference-resource-capability-evidence`
- Issue：`#191`
- item_type：`FR`
- release：`v0.5.0`
- sprint：`2026-S18`

## 背景与目标

- 背景：`v0.4.0` 已冻结最小资源生命周期、任务级追踪与 Core 注入资源包边界，但 `v0.5.0` 需要开始收敛“资源能力抽象”。若没有正式证据载体，后续 `FR-0013` 的 adapter 资源需求声明与 `FR-0014` 的 Core 资源能力匹配就会退化成会话内判断、单平台经验或具体技术名词驱动的抽象扩张。
- 目标：为 `v0.5.0` 冻结双参考适配器资源能力证据记录 contract，要求每个新增共享资源能力标识都能被小红书 / 抖音的真实运行差异解释，并把这套记录变成 `#192/#193/#197` 的正式输入，而不是一次性人工笔记。

## 范围

- 本次纳入：
  - 冻结 `DualReferenceResourceCapabilityEvidenceRecord` 的最小字段、约束与决策语义
  - 冻结 `shared_status`、`decision` 与 `evidence_refs` 的证据判定边界
  - 冻结 `v0.5.0` 可被 `#192/#193` 消费的有限共享资源能力词汇表
  - 冻结“共性资源语义 / 单平台特例 / 被拒绝抽象候选”的正式研究口径
- 本次不纳入：
  - `FR-0013` 的 adapter 资源需求声明 carrier 设计
  - `FR-0014` 的 Core 资源能力匹配输入输出与执行算法
  - 第三个平台、provider 生态、复杂调度或具体浏览器技术绑定
  - runtime 代码、真实证据落盘实现与 release gate 改造

## 需求说明

- 功能需求：
  - `v0.5.0` 的资源能力证据记录必须统一使用 `DualReferenceResourceCapabilityEvidenceRecord` 作为 canonical carrier；不得再用 issue 评论、会话摘要、临时表格或运行日志片段替代 formal evidence truth。
  - `DualReferenceResourceCapabilityEvidenceRecord` 固定字段必须为：
    - `adapter_key`
    - `capability`
    - `execution_path`
    - `resource_signals`
    - `candidate_abstract_capability`
    - `shared_status`
    - `evidence_refs`
    - `decision`
  - `shared_status` 在 `v0.5.0` 只允许以下值：
    - `shared`
    - `adapter_only`
    - `rejected`
  - `shared_status=shared` 只允许用于“小红书 / 抖音都暴露出同类资源语义，且该语义可以在不绑定具体技术实现的前提下被同一抽象解释”的场景。
  - `shared_status=adapter_only` 只允许用于“某条资源语义仅由单平台暴露，仍应留在 adapter 私有边界，不得提升为 Core 共享能力”的场景。
  - `shared_status=rejected` 只允许用于“候选抽象本身违反阶段边界、绑定具体技术名词、或被双参考适配器证据证明不应进入共享词汇表”的场景。
  - `resource_signals` 必须是非空数组，至少能表达当前 `adapter_key + capability + execution_path` 下观察到的资源语义信号；这些信号用于解释候选抽象为何成立、为何只应留在 adapter 私有边界，或为何应被拒绝。
  - `evidence_refs` 必须是非空、去重数组，且每条记录至少同时指向一个可复验的 reference adapter 运行面证据与一个仓内 formal context 证据；不得只引用口头结论。
  - `decision` 必须显式表达该记录对 `candidate_abstract_capability` 的处置结论；后续 `#192/#193` 只能消费 `decision=approve_shared_capability` 且 `shared_status=shared` 的能力标识。
  - `FR-0015` 在 `v0.5.0` 冻结的有限共享资源能力词汇表固定为：
    - `managed_account`
      - 语义：由 Core 管理、按 `adapter_key` 作用域隔离的账号 / 会话执行材料；共享层只冻结其“受管账号能力”身份，不冻结平台私有 material 字段命名。
    - `managed_proxy`
      - 语义：由 Core 管理的网络出口 / 代理执行材料；共享层只冻结其“受管代理能力”身份，不冻结 provider、协议或实现技术。
  - 除上述两个能力标识外，`v0.5.0` 不得再新增第三个共享资源能力标识；若证据不足，必须继续保持 `v0.4.0` 最小资源模型，而不是提前设计大全抽象。
- 契约需求：
  - `#192` 与 `#193` 只能消费本 FR 已批准的共享资源能力标识，也就是 `managed_account` 与 `managed_proxy`；不得自行在 formal spec、实现 PR 或测试夹具中另建新词汇。
  - `adapter_key` 必须复用既有 reference adapter 标识，当前只允许 `xhs` 与 `douyin`。
  - `capability` 必须复用上游共享请求模型与 `v0.4.0` reference adapter 真实路径中已经冻结的 operation truth；当前 `FR-0015` 的证据基线固定围绕 `content_detail_by_url` 的 hybrid 执行路径，不得改写为具体 adapter-facing capability family 或单平台私有调用名。
  - `execution_path` 必须显式区分证据建立在哪条 reference adapter 真实路径上；`FR-0015` 当前只批准 `hybrid_content_detail_by_url` 作为正式共享证据入口，避免不同运行路径混淆。
  - 共享资源能力词汇表不得直接绑定 `Playwright`、`CDP`、`Chromium`、`sign service`、`verify_fp`、`ms_token`、`webid` 等具体技术或平台私有字段名；这些内容如果只在单平台出现，只能作为 `resource_signals` 或 adapter 私有 material 事实存在。
  - 任一候选抽象若只能由单平台信号解释、或需要穿透 `FR-0012` 已冻结的 adapter 私有 material 才能成立，就必须被记录为 `adapter_only` 或 `rejected`，不得提升为共享能力。
  - `FR-0015` 只冻结证据记录 contract 与批准词汇表，不重新定义 `FR-0010` 的生命周期主 contract、`FR-0011` 的 tracing truth 或 `FR-0012` 的注入边界。
- 非功能需求：
  - 证据记录必须可追溯、可复验、可被后续 formal spec / code review / release closeout 直接消费，而不是依赖 reviewer 脑补。
  - 该 contract 必须保持平台无关与技术无关；共享词汇表表达的是资源语义，不是实现技术栈。
  - `FR-0015` 只冻结有限词汇表，不承诺 provider 选择、优先级、浏览器 runtime 管理或复杂网络编排。

## 约束

- 阶段约束：
  - 本事项只服务 `v0.5.0` 的资源能力抽象收敛，不提前引入第三个平台验证或复杂 provider 生态。
  - 本事项只批准被双参考适配器共同解释的最小共享能力，不把单平台压力直接抬升成 Core 抽象。
- 架构约束：
  - Core 仍负责共享资源运行时语义；Adapter 仍负责平台私有 material 与单平台执行细节。
  - formal spec 与实现 PR 必须分离；`#194` 只冻结 evidence contract，不混入 runtime / tests 改动。
  - `#192/#193` 必须把本 FR 作为上游 requirement truth，而不是在各自 formal spec 中重新发明能力标识或证据 carrier。

## GWT 验收场景

### 场景 1

Given 小红书与抖音在 `content_detail_by_url` 的 hybrid 执行路径上都要求 Core 注入 adapter-scoped account material 与 proxy material  
When `FR-0015` 记录双参考适配器资源能力证据  
Then 证据记录必须允许把 `managed_account` 与 `managed_proxy` 标记为 `shared`，并把它们冻结为 `v0.5.0` 唯一批准的共享能力标识

### 场景 2

Given 小红书存在签名服务入口、抖音存在 `verify_fp / ms_token / webid` 等单平台执行细节  
When `FR-0015` 对这些信号形成证据记录  
Then 它们只能被记录为 `adapter_only` 或 `rejected`，而不能被提升为新的共享资源能力标识

### 场景 3

Given 某个候选抽象直接绑定 `Playwright`、`CDP`、`Chromium` 或其他具体技术名词  
When `FR-0015` 审查该候选抽象  
Then 该记录必须落为 `shared_status=rejected`，且 `decision` 不能把它批准为共享能力

### 场景 4

Given `#192` 或 `#193` 需要引用 `v0.5.0` 的共享资源能力标识  
When 它们消费 `FR-0015` 的 formal spec  
Then 它们只能引用 `managed_account` 与 `managed_proxy`，不得自行新增未批准标识

### 场景 5

Given 一条证据记录缺少 `resource_signals`、`evidence_refs` 或 `decision`  
When 该记录进入 formal review 或后续实现消费链路  
Then 它不得被视为合法的资源能力证据 truth

## 异常与边界场景

- 异常场景：
  - 若 `shared_status` 不在 `shared / adapter_only / rejected` 内，该记录必须被视为 contract violation。
  - 若 `shared_status=shared`，但 `candidate_abstract_capability` 不在 `managed_account / managed_proxy` 之内，该记录必须被拒绝。
  - 若 `evidence_refs` 只引用单平台证据、一次性会话结论或不可复验材料，该记录不得作为共享能力批准依据。
- 边界场景：
  - `resource_signals` 可以记录平台私有字段与运行特征，但共享词汇表只冻结“抽象能力身份”，不冻结 adapter 私有 material 形状。
  - `adapter_only` 与 `rejected` 记录同样属于正式证据 truth；它们的作用是阻止错误抽象进入共享层，而不是被静默忽略。
  - 本事项只冻结 `content_detail_by_url` hybrid 路径上的证据基线；若未来要扩张到新 capability 或新 execution path，必须通过新的 formal spec 明确批准。

## 验收标准

- [ ] formal spec 明确冻结 `DualReferenceResourceCapabilityEvidenceRecord` 的最小字段集合与字段语义
- [ ] formal spec 明确冻结 `shared_status` 只允许 `shared / adapter_only / rejected`
- [ ] formal spec 明确冻结 `v0.5.0` 的有限共享资源能力词汇表，仅允许 `managed_account` 与 `managed_proxy`
- [ ] formal spec 明确写清 `#192/#193` 只能消费本 FR 已批准的共享能力标识
- [ ] formal spec 明确写清共性资源语义、单平台特例与被拒绝抽象候选的研究边界
- [ ] formal spec 明确禁止把具体技术名词或单平台私有信号提升为共享资源能力抽象

## 依赖与外部前提

- 外部依赖：
  - `#188` 已把 `v0.5.0` 定义为“在真实参考适配器压力下收敛资源能力抽象”的阶段
  - `#189` 与 `#190` 分别承接 adapter 资源需求声明与 Core 资源能力匹配，但都必须等待本 FR 先冻结共享词汇表与证据规则
  - `FR-0004` 已冻结 `adapter_key / capability` 的共享输入语义
  - `FR-0010`、`FR-0011`、`FR-0012` 已冻结 lifecycle / tracing / injected bundle 的上游边界，是本 FR 的直接前提
- 上下游影响：
  - `#192` / `FR-0013` 后续只能围绕 `managed_account / managed_proxy` 声明资源需求
  - `#193` / `FR-0014` 后续只能围绕 `managed_account / managed_proxy` 进行能力匹配，不得自行扩张词汇表
  - `#197` 必须按本 FR 的 record contract 落真实证据，而不是建立第二套 evidence schema
