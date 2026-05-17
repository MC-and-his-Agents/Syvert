# FR-0457 Scheduled Execution Core Contract

## 关联信息

- item_key：`FR-0457-scheduled-execution-core-contract`
- Issue：`#457`
- item_type：`FR`
- release：`unbound`
- sprint：`unbound`
- Parent Phase：`#456`
- Roadmap anchor：`#383` remains deferred/not planned and is not an execution entry

## 目标

定义 Scheduled Execution 的 Core contract admission 边界，使延迟执行与周期触发能够复用现有 Core 主路径，而不是引入独立调度产品或 runtime implementation。

## GWT 验收场景

### 延迟执行复用 Core 主路径

Given 一个 schedule record 包含触发时间、目标 task request 与执行策略
When 该触发到期并被 Core claim
Then Core 必须通过现有 task admission / TaskRecord / resource trace 路径执行目标请求
And schedule layer 不得定义平台私有字段或业务 workflow DSL

### 周期触发生成可审计 occurrence

Given 一个周期 schedule record
When 下一次 occurrence 到期
Then Core 必须记录 occurrence identity、claim state 与执行结果关联
And 结果必须回写到 TaskRecord / dataset / resource trace 的既有 truth carrier

### batch target 复用 v1.6.0 batch contract

Given schedule target 是 batch request
When occurrence 被执行
Then batch item outcome、partial failure、resume token 与 dataset sink 必须复用 `FR-0445` contract
And schedule layer 不得重新定义 item result envelope

## 异常与边界场景

### 错过触发

Given scheduler 停止期间错过一个或多个 occurrence
When scheduler 恢复
Then missed run policy 必须明确选择 skip、coalesce 或 catch-up
And policy 不得隐式扩大成上层业务策略

### 重复 claiming

Given 两个 worker 同时发现同一 due occurrence
When 它们尝试 claim
Then 只有一个 claim 可以成功
And 失败方必须得到稳定、可审计的 duplicate-claim 结果

### retry exhausted 与 unknown outcome

Given occurrence 执行失败、重试耗尽或执行结果未知
When Core 记录最终状态
Then TaskRecord 与 scheduler observation 必须能区分 retry exhausted、unknown outcome 与 manual recovery required

## 验收标准

- Formal spec 后续实现前必须定义 scheduled task admission、durable schedule record、trigger occurrence、claim lease、missed run policy 与 scheduler observation 的最小 public vocabulary。
- CLI / API / scheduler 入口必须证明使用同一 Core task path。
- Scheduled Execution 不得引入 UI、BI、上层调度产品、scheduler service、write-side operation、provider selector/fallback/marketplace。
- `#383` 保持 deferred/not planned，不作为 completed truth 或 execution entry。
