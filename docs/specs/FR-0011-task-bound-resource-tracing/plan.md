# FR-0011 实施计划

## 关联信息

- item_key：`FR-0011-task-bound-resource-tracing`
- Issue：`#165`
- item_type：`FR`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 exec-plan：
  - `docs/exec-plans/FR-0011-task-bound-resource-tracing.md`
  - `docs/exec-plans/CHORE-0131-fr-0011-formal-spec-closeout.md`

## 实施目标

- 在进入实现前冻结资源状态跟踪与资源使用日志的最小 contract，使 `v0.4.0` 的资源系统具备 task-bound、可审计、可回放的最小证据面。

## 分阶段拆分

- 阶段 1：`#166` 收口 formal spec，明确 tracing event truth、最小事件类型与审计投影。
- 阶段 2：后续实现 Work Item 基于该 spec 落地 append-only tracing 与最小查询/验证能力。
- 阶段 3：版本 gate 与 reference adapter 回归在不改写 tracing contract 的前提下消费同一审计面。

## 实现约束

- 不允许触碰的边界：
  - 不得重新定义 `FR-0010` 的 acquire/release 主接口、资源状态轴或 bundle 结构
  - 不得在 tracing 层扩张到 UI、报表与跨租户分析系统
  - 不得引入 Adapter 注入 boundary 或资源能力匹配语义
- 与上位文档的一致性约束：
  - 与 `docs/roadmap-v0-to-v1.md` 对 `v0.4.0` 的最小资源系统目标保持一致
  - 与 `FR-0010` 的状态名、资源类型与 lease/bundle carrier 保持一致
  - 与 `AGENTS.md`、`WORKFLOW.md` 对 formal spec 与执行入口的约束保持一致

## 测试与验证策略

- formal spec 阶段：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
- implementation 阶段：
  - tracing 事件序列单测：验证 append-only、重复事件幂等与冲突 fail-closed
  - task-bound usage projection 测试：验证按 `task_id` / `resource_id` / `lease_id` / `bundle_id` 可重建最小时间线
  - 资源生命周期集成测试：验证状态迁移成功时 tracing truth 必然存在
- 手动验证：
  - 逐条核对 `FR-0011` 与 `FR-0010` / `FR-0012` 的交界，确保 tracing 不再长出第二套状态机或注入 contract

## TDD 范围

- 先写测试的模块：
  - `ResourceTraceEvent` 共享 schema 与事件类型
  - append-only 幂等/冲突检测
  - task/resource/lease/bundle 关联视图的最小重建能力
- 暂不纳入 TDD 的模块与理由：
  - 审计 UI、报表与 release/sprint closeout 索引不属于运行时代码

## 并行 / 串行关系

- 可并行项：
  - `#166` 可与 `#164`、`#168` 的 formal spec closeout 并行推进，因为主要写集分离
- 串行依赖项：
  - `FR-0011` 必须消费 `FR-0010` 已冻结的资源类型、状态名与 lease/bundle carrier
  - tracing 的实现 Work Item 必须在 formal spec 通过后再进入 implementation PR
- 阻塞项：
  - 若 task/resource/lease 关联字段与最小时间线未冻结，后续实现与 gate 会各自长出不同审计口径

## 进入实现前条件

- [ ] `FR-0011` formal spec 已通过 spec review
- [ ] `ResourceTraceEvent` 最小字段集合已冻结
- [ ] `acquired / released / invalidated` 事件类型与时间线已冻结
- [ ] task-bound usage log 的最小审计面已冻结

## spec review 结论

- 结论目标：把“资源使用可以按任务追踪”的 GitHub 意图推进到 implementation-ready 的 tracing contract。
- 审查关注：
  - 是否形成单一 append-only tracing truth，而不是事件流和日志各自一套 schema
  - 是否把 task/resource/lease/bundle 关联字段冻结清楚
  - 是否把生命周期主 contract 与 Adapter 注入 boundary 留在相邻 FR
- implementation-ready 判定：formal spec 通过 spec review 且进入实现前条件满足后，后续 tracing 实现 Work Item 才可进入执行回合。
