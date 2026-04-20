# FR-0010 实施计划

## 关联信息

- item_key：`FR-0010-minimal-resource-lifecycle`
- Issue：`#163`
- item_type：`FR`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 exec-plan：
  - `docs/exec-plans/FR-0010-minimal-resource-lifecycle.md`
  - `docs/exec-plans/CHORE-0130-fr-0010-formal-spec-closeout.md`
  - `docs/exec-plans/CHORE-0134-fr-0010-store-bootstrap-formal-contract-traceability.md`

## 实施目标

- 在进入实现前冻结最小资源生命周期主 contract，使后续资源模型、追踪日志与 Adapter 注入都围绕同一套 `resource -> bundle -> lease -> state transition` truth 推进。

## 分阶段拆分

- 阶段 1：`#164` 收口 formal spec，明确资源类型、bundle/lease carrier、状态机与 `acquire/release` 主 contract。
- 阶段 2：后续实现 Work Item 基于该 formal spec 落地 Core 侧资源模型与获取/释放路径。
- 阶段 2.1：实现 Work Item 需要同时消费 formal spec 中的 `ResourceLifecycleSnapshot` / `seed_resources(records)` traceability，把本地默认 store 与 bootstrap 入口约束在同一套 lifecycle contract 下。
- 阶段 3：相邻 FR 在不改写 lifecycle 主 contract 的前提下，分别补齐 task-bound tracing 与 Adapter 注入边界。

## 实现约束

- 不允许触碰的边界：
  - 不得提前定义浏览器资源、能力匹配、复杂调度与恢复循环
  - 不得在本事项中加入 `FR-0011` 的审计日志 schema
  - 不得在本事项中加入 `FR-0012` 的 Adapter 注入执行约束
- 与上位文档的一致性约束：
  - 与 `docs/roadmap-v0-to-v1.md` 对 `v0.4.0` 的最小资源系统目标保持一致
  - 与 `AGENTS.md`、`WORKFLOW.md` 对“Core 负责运行时语义、formal spec 绑定 FR、Work Item 是执行入口”的规则保持一致
  - 与 `FR-0004` 已冻结的 `adapter_key` / `capability` 输入语义保持一致
  - 与 `FR-0002` / `FR-0005` 已冻结的 shared envelope 与失败分类边界保持一致
  - 若实现提供默认本地 store 与内部 bootstrap surface，则 `ResourceLifecycleSnapshot`、`revision`、`seed_resources(records)` 与默认 store 路径入口都必须直接复用 formal spec 词汇，不得在实现侧另发明影子 schema

## 测试与验证策略

- formal spec 阶段：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
- implementation 阶段：
  - 资源状态迁移单测：验证 `AVAILABLE / IN_USE / INVALID` 允许迁移与非法迁移 fail-closed
  - 资源 bundle/lease 集成测试：验证整包 acquire/release 语义与重复 release 幂等
  - bootstrap / snapshot 测试：验证 `seed_resources(records)` 的 same-value replay/no-op、同批重复 `resource_id` 直接拒绝、被 active lease 解释的 `IN_USE` same-value replay 允许、无 lease 可解释的 `IN_USE` seed 输入前置拒绝，以及既有 truth 冲突 fail-closed
  - durable write 测试：验证 snapshot `revision` compare-and-swap 的 stale-write 拒绝，以及空 store 回落到 canonical 空 snapshot
  - 默认本地入口测试：验证 `SYVERT_RESOURCE_LIFECYCLE_STORE_FILE` 覆盖优先级与未提供时回落 `~/.syvert/resource-lifecycle.json`
  - 端到端回归：验证 Core 不会在部分 slot 缺失时错误注入部分 bundle
- 手动验证：
  - 逐条核对 `FR-0010` 与 `FR-0011 / FR-0012` 的边界，确保没有重复冻结同一 contract
  - 明确记录 durable snapshot / store-path traceability 的迁移结论：本次 formal follow-up 不涉及 schema 升级、路径迁移或数据回填

## TDD 范围

- 先写测试的模块：
  - 资源状态机与非法迁移约束
  - `ResourceBundle` / `ResourceLease` 共享 carrier
  - `acquire` 整包成功/失败与 `release` 幂等行为
- 暂不纳入 TDD 的模块与理由：
  - release/sprint/GitHub closeout 索引属于流程与治理工件，不是运行时代码

## 并行 / 串行关系

- 可并行项：
  - `#164` 可与 `#166`、`#168` 的 formal spec closeout 并行推进，因为主要写集分离
- 串行依赖项：
  - `FR-0010` formal spec 必须先冻结，后续资源实现 Work Item 才能进入 implementation PR
  - `FR-0011` 与 `FR-0012` 的实现侧不得反向改写本 FR 的生命周期主 contract
- 阻塞项：
  - 若资源类型、bundle/lease carrier 或状态迁移在 formal spec 中未冻结清楚，后续实现一定会重新替 requirement 做决策

## 进入实现前条件

- [x] `spec review` 已通过
- [x] `account` / `proxy` / `ResourceBundle` / `ResourceLease` 最小 carrier 已冻结
- [x] `acquire` / `release` 输入输出与失败语义已冻结
- [x] `AVAILABLE / IN_USE / INVALID` 状态迁移边界已冻结
- [x] `ResourceLifecycleSnapshot`、`seed_resources(records)` 与 `revision` compare-and-swap 语义已补齐到 formal suite
- [x] 默认本地入口的 store-path traceability 已补齐，且没有把当前 JSON/file backend 升格为唯一长期后端

## spec review 结论

- 当前结论：通过（含 `#177` traceability follow-up）
- 未决问题与风险：
  - 当前 formal spec 已把资源类型、bundle/lease carrier、状态迁移、`acquire / release` 输入输出、host-side durable snapshot truth、bootstrap replay/no-op/conflict、bootstrap 不得引入无 lease 可解释的 `IN_USE` 资源，以及默认本地入口 traceability 收口到 implementation-ready；残余风险主要在后续实现是否忠实消费该 contract，而不是当前规约仍存在 requirement 缺口
  - `resource_unavailable` 的 host-side / `runtime_contract` 边界、重复 `release` 的 canonical idempotent no-op，以及 snapshot `revision` compare-and-swap 的并发行为，仍需在后续实现 Work Item 中补齐 contract tests 与回归验证，避免运行时漂移成 `unsupported` / `platform` 或影子 store 语义
- 进入实现前条件：已满足；guardian / PR checks 属于独立 merge gate，由当前 Work Item exec-plan 跟踪，不混写进 formal spec review 结论。
- 结论目标：把 `v0.4.0` 的“最小资源生命周期”从 GitHub 意图推进到 implementation-ready 的主 contract。
- 审查关注：
  - 是否把资源类型、bundle/lease carrier 与状态机讲清楚
  - 是否明确定义整包 acquire、冲突 release 与 fail-closed 行为
  - 是否把 snapshot / bootstrap / revision / 默认本地入口 traceability 收进同一套 canonical contract
  - 是否把 tracing / Adapter 注入边界留在相邻 FR，而不是在生命周期主 contract 中混写
- implementation-ready 判定：当前 formal spec 已通过 spec review 且进入实现前条件满足，后续实现 Work Item 可在独立 implementation PR 中消费本 requirement baseline。
