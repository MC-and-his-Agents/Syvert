# FR-0018 实施计划

## 关联信息

- item_key：`FR-0018-http-task-api-same-core-path`
- Issue：`#221`
- item_type：`FR`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 exec-plan：`docs/exec-plans/CHORE-0153-fr-0018-formal-spec-closeout.md`

## 实施目标

- 本次实施要交付的能力：
  - 冻结 HTTP `submit`、`status`、`result` 的最小 formal contract
  - 冻结 HTTP ingress 如何投影到既有共享请求 / `TaskRecord` / result truth，而不新建 shadow path
  - 对齐 `FR-0016` / `FR-0017` 已冻结的执行控制、瞬态失败、closeout/control-state failure 与 `runtime_result_refs` 语义
  - 明确 `ExecutionControlPolicy` 在 HTTP 的可见性、默认值、错误边界与 idempotency safety gate 承接方式
  - 为 `#230` HTTP endpoint implementation、`#231` CLI/API same-path regression evidence、`#232` parent closeout 提供 implementation-ready requirement 输入

## 分阶段拆分

- 阶段 1：对齐 `FR-0008`、`FR-0009` 与 `v0.6.0` 路线图边界，确认 HTTP service surface 只能暴露既有闭环，不得旁路 Core。
- 阶段 2：把 `FR-0016` 的共享执行控制语义映射到 HTTP：冻结 `ExecutionControlPolicy` 可见性、共享默认值、retryable predicate、`execution_timeout` 投影，以及 closeout/control-state failure 边界。
- 阶段 3：把 `FR-0017` 的共享观测语义映射到 HTTP：冻结结构化控制结果、`ExecutionControlEvent` 与 `runtime_result_refs` 不得被 transport 裁剪的约束。
- 阶段 4：冻结 `submit`、`status`、`result` 的职责、成功/失败 contract、GWT、数据模型与风险，形成完整 formal spec 套件。
- 阶段 5：`spec review` 通过后进入 `#230`，实现最小 HTTP endpoint surface 并接入同一条 Core / `TaskRecord` durable path。
- 阶段 6：`#230` 完成后进入 `#231`，补齐 CLI/API same-path regression evidence，证明两个入口共享 durable truth、控制结果分类、状态查询与结果回读语义。
- 阶段 7：`#231` 证据齐备后进入 `#232`，收口 FR-0018 的 parent closeout、GitHub 状态、PR 关联、依赖 FR 与 release/sprint 真相。

## 实现约束

- 不允许触碰的边界：
  - `syvert/**`
  - `tests/**`
  - `scripts/**`
  - `docs/releases/**`
  - `docs/sprints/**`
  - 相邻 FR 正文与非 FR-0018 exec-plan
- 与上位文档的一致性约束：
  - 必须满足 `docs/roadmap-v0-to-v1.md` 对 `v0.6.0` “先闭环再暴露服务面”的约束
  - 必须继续复用 `FR-0008` 的 durable `TaskRecord` truth 与 `FR-0009` 的 same-path 查询边界
  - 必须继续复用 `FR-0016` 的共享执行控制与错误分类真相，尤其是 retryable predicate、`execution_timeout` 与 closeout/control-state failure 边界
  - 必须继续复用 `FR-0017` 的结构化控制结果、指标与 `runtime_result_refs` truth
  - 必须明确 API transport 只做 ingress/egress，不新增 adapter 直连、影子状态、影子 envelope、影子控制事件或 transport 私有重试策略
  - 当前 public capability 只能是 `content_detail_by_url`

## 测试与验证策略

- 单元测试：
  - 本 formal spec 回合不新增单元测试；实现阶段由 `#230` 补齐 endpoint / transport 映射测试，并覆盖 `ExecutionControlPolicy` pass-through 与错误边界
- 集成/契约测试：
  - 本 formal spec 回合通过 spec suite、contracts/README 与 data-model 冻结 API contract
  - `#231` 负责补齐 CLI/API same-path regression evidence，特别验证 pre-accepted concurrency rejection、`execution_timeout`、closeout/control-state failure、post-accepted reacquire rejection 与 `runtime_result_refs` 可见性
- 手动验证：
  - 核对 `submit/status/result` 是否全部建立在 `FR-0008` / `FR-0009` / `FR-0016` / `FR-0017` 已批准 contract 之上
  - 核对 HTTP 文档未把整个 `platform` category 扩张为 retryable，也未吞掉 `error.details.control_code` / `error.details.retryable` / `runtime_result_refs`
  - 核对 spec 中已显式排除认证、多租户、RBAC、分布式队列、复杂查询 DSL、完整控制台与 transport 私有控制 DSL

## TDD 范围

- 先写测试的模块：
  - 无；本轮只交付 formal spec 套件
- 暂不纳入 TDD 的模块与理由：
  - HTTP routing、serialization、CLI/API regression harness、结构化观测落盘均属于后续实现 Work Item，不属于本次 formal spec closeout 范围

## 并行 / 串行关系

- 可并行项：
  - `spec.md`、`data-model.md`、`contracts/README.md`、`risks.md` 可围绕同一 contract 并行补齐
  - requirement container 与 active closeout exec-plan 可在 formal spec 定稿后同步更新
- 串行依赖项：
  - 必须先冻结 API 与 Core same-path 边界，再进入 `#230` 的 endpoint implementation
  - 必须先冻结 `FR-0016` / `FR-0017` 对 HTTP 的承接边界，再进入任何 transport mapping 实现
  - 必须先完成 `#230`，再进入 `#231` 做 CLI/API same-path regression evidence
  - 必须在 `#231` 证据完成后，才能由 `#232` 做 parent closeout
- 阻塞项：
  - 若 `submit/status/result` 仍无法与 `FR-0008` / `FR-0009` 的 shared truth、`FR-0016` 的控制语义、`FR-0017` 的观测 truth 明确对齐，后续实现将被迫在 transport 层重新做 requirement 决策

## 进入实现前条件

- [ ] `spec review` 已通过
- [ ] 关键风险已记录并有缓解策略
- [ ] `FR-0008` / `FR-0009` / `FR-0016` / `FR-0017` 边界已被明确引用，后续实现不需要再自行发明 API 私有 truth
- [ ] `ExecutionControlPolicy` 的 HTTP 可见性、共享默认值、错误边界与 idempotency safety gate 已冻结
- [ ] `execution_timeout`、closeout/control-state failure、pre-accepted concurrency rejection、post-accepted reacquire rejection 与 `runtime_result_refs` 语义已冻结

## Closeout 语义

- formal spec closeout：本回合只负责把 HTTP service surface 与共享控制/观测边界冻结为 requirement truth，不宣布 runtime 实现已完成。
- implementation closeout：`#230` 必须证明 HTTP endpoint 复用同一 Core path，且没有吞掉共享错误、控制事件或 `runtime_result_refs`。
- evidence closeout：`#231` 必须提供 CLI/API same-path regression evidence，覆盖成功、非终态、pre-accepted failure、控制面 timeout、closeout/control-state failure 与 post-accepted reacquire rejection。
- parent closeout：`#232` 必须在上述 requirement / implementation / evidence truth 全部收口后，统一 GitHub 状态、PR、review、release/sprint 与依赖 FR 真相。
