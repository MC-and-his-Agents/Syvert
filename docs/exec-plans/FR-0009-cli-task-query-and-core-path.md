# FR-0009 执行计划（requirement container）

## 关联信息

- item_key：`FR-0009-cli-task-query-and-core-path`
- Issue：`#128`
- item_type：`FR`
- release：`v0.3.0`
- sprint：`2026-S16`
- 关联 spec：`docs/specs/FR-0009-cli-task-query-and-core-path/`
- 状态：`inactive requirement container`

## 说明

- `FR-0009` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- `FR-0009` formal spec 已由 PR `#154` 合入主干；对应 `docs/exec-plans/CHORE-0126-fr-0009-formal-spec-closeout.md` 保留 formal spec 收口轮次的原始执行记录。
- `FR-0009` 的 CLI query public surface 已由 PR `#156` 完成并关闭 `#142`；对应 `docs/exec-plans/CHORE-0127-fr-0009-cli-task-query.md` 保留该实现轮次的原始执行记录。
- `FR-0009` 的 same-path 判别式证据已由 PR `#157` 完成并关闭 `#143`；对应 `docs/exec-plans/CHORE-0128-fr-0009-cli-core-path-persistence-closeout.md` 保留该实现轮次的原始执行记录。
- 上述子事项 exec-plan 中残留的 active / current 表述仅绑定各自已结束的历史执行轮次，不构成当前 `FR-0009` 的 active 入口，也不重新打开这些 Work Item。
- `FR-0009` 的父事项 closeout 由 `docs/exec-plans/CHORE-0129-fr-0009-parent-closeout.md` 记录 `#144` 执行回合，并负责把 `#128` 的关闭语义、release / sprint 索引和 GitHub 真相收口到同一条证据链。
- `FR-0009` 只消费 `FR-0008` 已冻结的 durable `TaskRecord` contract，不新增影子 schema、影子结果文件或 query 私有持久化 truth。

## 最近一次 checkpoint 对应的 head SHA

- 父事项 closeout 基线：`2f4aea6322d93feefa66b63227a3c9ff5299b44c`
- 说明：该基线已经包含 `#141/#142/#143` 合入主干后的 requirement 真相；后续由 `#144` 的 exec-plan 记录 parent closeout、release / sprint 索引与 GitHub 关闭语义收口事实。
