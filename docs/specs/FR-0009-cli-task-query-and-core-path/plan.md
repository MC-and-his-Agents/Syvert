# FR-0009 实施计划

## 关联信息

- item_key：`FR-0009-cli-task-query-and-core-path`
- Issue：`#128`
- item_type：`FR`
- release：`v0.3.0`
- sprint：`2026-S16`
- 关联 exec-plan：`docs/exec-plans/CHORE-0126-fr-0009-formal-spec-closeout.md`

## 实施目标

- 为 `v0.3.0` 冻结 CLI `run/query` public surface、legacy 执行入口兼容边界与 query 最小错误 contract，使 `FR-0009` 从 GitHub 意图进入可实现的 formal contract 状态。
- 明确 `#142` 与 `#143` 的实现分工：前者负责 CLI query surface，后者负责同路径闭环与端到端证据。
- 为 `#144` 的 parent closeout 提供统一的 requirement container、release/sprint 索引与 GitHub 收口输入。

## 分阶段拆分

- 阶段 1：`#141` 冻结 formal spec，明确 `run/query` public surface、query 成功/失败 contract 与 same-path 边界。
- 阶段 2：`#142` 在不扩张 requirement 的前提下，实现顶层子命令解析与 CLI query surface，同时保留 legacy 平铺执行入口兼容。
- 阶段 3：`#143` 补齐 `run/legacy-run -> durable record -> query` 的端到端验证，证明 query 只消费共享 durable truth。
- 阶段 4：`#144` 统一收口 requirement container、release/sprint 索引、exec-plan 与 GitHub issue 真相。

## 实现约束

- 不允许触碰的边界：
  - `#141` formal spec PR 只允许修改 `docs/specs/FR-0009-cli-task-query-and-core-path/`、`docs/exec-plans/FR-0009-cli-task-query-and-core-path.md`、当前事项 exec-plan 与最小 release/sprint 索引
  - `#142` 不得重新定义 `TaskRecord` schema，也不得扩张成列表查询或摘要视图
  - `#143` 不得新增 query 私有 payload，只负责证明 same-path 与 fail-closed 行为
  - `#144` 不得引入新 runtime 或新的 formal spec 语义
- 与上位文档的一致性约束：
  - 与 `docs/roadmap-v0-to-v1.md` 的 `v0.3.0` 目标保持一致
  - 与 `FR-0008` 的 `TaskRecord` / store contract 保持一致，不重写 durable truth
  - 与 `AGENTS.md`、`WORKFLOW.md` 对“formal spec 绑定 FR、Work Item 为唯一执行入口、formal spec 与实现分离”的契约保持一致

## 测试与验证策略

- formal spec 阶段：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
  - `python3 scripts/governance_gate.py --mode ci --base-sha <merge-base> --head-sha <head>`
- implementation 阶段：
  - `python3 -m unittest tests.runtime.test_cli`
  - `python3 -m unittest tests.runtime.test_task_record`
  - `python3 -m unittest tests.runtime.test_task_record_store`
  - 受 CLI 入口影响的 adapter CLI 回归测试
- 手动验证：
  - 验证 `query --task-id <id>` 返回完整共享 `TaskRecord`
  - 验证 legacy 平铺执行入口与 `run` 子命令都沿共享 durable path 工作
  - 验证 invalid marker、损坏记录与 store 不可用都 fail-closed 为 `task_record_unavailable`

## TDD 范围

- 先写测试的模块：
  - CLI `query` 成功/失败 surface
  - legacy 平铺入口与 `run` 子命令的兼容回归
  - same-path 回读与 fail-closed 查询回归
- 暂不纳入 TDD 的模块与理由：
  - release/sprint/GitHub closeout 工件不属于运行时代码，使用 docs / workflow 门禁与手工核对收口

## 并行 / 串行关系

- 可并行项：
  - 无；`#141 -> #142 -> #143 -> #144` 必须按 Work Item 串行收口，不在 formal spec 阶段提前展开 `#144` 文档骨架
- 串行依赖项：
  - 必须先完成 `#141` formal spec 冻结，`#142/#143` 才能进入实现 PR
  - `#142` 先冻结 CLI public surface，`#143` 再补 same-path 端到端证据
  - `#144` 必须等待 `#141/#142/#143` 完成并合入主干

## 进入实现前条件

- [ ] `FR-0009` formal spec 已通过 spec review
- [ ] `run/query` public surface 与 legacy 兼容边界已冻结
- [ ] query 最小错误 contract 已冻结
- [ ] same-path / no-shadow-schema 边界已冻结

## spec review 结论

- 结论目标：把 `FR-0009` 从“CLI 应可查询任务状态与结果”的 GitHub 意图推进到可直接指导实现的 formal contract。
- 审查关注：query 是否只消费共享 durable truth；legacy 平铺执行入口是否保持兼容；错误 contract 是否足够明确，不把 requirement 决策留给 `#142`。
- implementation-ready 判定：当前 PR 通过 spec review 并满足进入实现前条件后，`#142/#143` 才可以进入独立实现回合。
