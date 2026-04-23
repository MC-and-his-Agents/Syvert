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
  - 为 `#230` HTTP endpoint implementation、`#231` CLI/API same-path regression evidence、`#232` parent closeout 提供 implementation-ready requirement 输入

## 分阶段拆分

- 阶段 1：对齐 `FR-0008`、`FR-0009` 与 `v0.6.0` 路线图边界，确认 HTTP service surface 只能暴露既有闭环，不得旁路 Core。
- 阶段 2：冻结 `submit`、`status`、`result` 的职责、成功/失败 contract、GWT、数据模型与风险，形成完整 formal spec 套件。
- 阶段 3：`spec review` 通过后进入 `#230`，实现最小 HTTP endpoint surface 并接入同一条 Core / `TaskRecord` durable path。
- 阶段 4：`#230` 完成后进入 `#231`，补齐 CLI/API same-path regression evidence，证明两个入口共享 durable truth、状态查询与结果回读语义。
- 阶段 5：`#231` 证据齐备后进入 `#232`，收口 FR-0018 的 parent closeout、GitHub 状态、PR 关联与 release/sprint 真相。

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
  - 必须明确 API transport 只做 ingress/egress，不新增 adapter 直连、影子状态或影子 envelope

## 测试与验证策略

- 单元测试：
  - 本 formal spec 回合不新增单元测试；实现阶段由 `#230` 补齐 endpoint / transport 映射测试
- 集成/契约测试：
  - 本 formal spec 回合通过 spec suite、contracts/README 与 data-model 冻结 API contract；`#231` 负责补齐 CLI/API same-path regression evidence
- 手动验证：
  - 核对 `submit/status/result` 是否全部建立在 `FR-0008` / `FR-0009` 已批准 contract 之上
  - 核对 spec 中已显式排除认证、多租户、RBAC、分布式队列、复杂查询 DSL、完整控制台

## TDD 范围

- 先写测试的模块：
  - 无；本轮只交付 formal spec 套件
- 暂不纳入 TDD 的模块与理由：
  - HTTP routing、serialization、CLI/API regression harness 均属于后续实现 Work Item，不属于本次 formal spec closeout 范围

## 并行 / 串行关系

- 可并行项：
  - `spec.md`、`data-model.md`、`contracts/README.md`、`risks.md` 可围绕同一 contract 并行补齐
  - requirement container 与 active closeout exec-plan 可在 formal spec 定稿后同步更新
- 串行依赖项：
  - 必须先冻结 API 与 Core same-path 边界，再进入 `#230` 的 endpoint implementation
  - 必须先完成 `#230`，再进入 `#231` 做 CLI/API same-path regression evidence
  - 必须在 `#231` 证据完成后，才能由 `#232` 做 parent closeout
- 阻塞项：
  - 若 `submit/status/result` 仍无法与 `FR-0008` / `FR-0009` 的 shared truth 明确对齐，后续实现将被迫在 transport 层重新做 requirement 决策

## 进入实现前条件

- [ ] `spec review` 已通过
- [ ] 关键风险已记录并有缓解策略
- [ ] `FR-0008` / `FR-0009` 边界已被明确引用，后续实现不需要再自行发明 API 私有 truth
