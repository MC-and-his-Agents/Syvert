# FR-0008 执行计划（requirement container）

## 关联信息

- item_key：`FR-0008-task-record-persistence`
- Issue：`#127`
- item_type：`FR`
- release：`v0.3.0`
- sprint：`2026-S16`
- 关联 spec：`docs/specs/FR-0008-task-record-persistence/`
- 状态：`inactive requirement container`

## 说明

- `FR-0008` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- `FR-0008` formal spec 已由 PR `#145` 合入主干；对应 `docs/exec-plans/CHORE-0122-fr-0008-formal-spec-closeout.md` 保留 formal spec 收口轮次的原始执行记录。
- `FR-0008` 的任务状态/结果/日志共享模型已由 PR `#147` 完成并关闭 `#138`；对应 `docs/exec-plans/CHORE-0123-fr-0008-task-record-model.md` 保留该实现轮次的原始执行记录。
- `FR-0008` 的本地持久化与共享序列化管线已由 PR `#148` 完成并关闭 `#139`；对应 `docs/exec-plans/CHORE-0124-fr-0008-local-persistence-and-serialization.md` 保留该实现轮次的原始执行记录。
- 上述子事项 exec-plan 中残留的 active / current 表述仅绑定各自已结束的历史执行轮次，不构成当前 `FR-0008` 的 active 入口，也不重新打开这些 Work Item。
- `FR-0008` 的父事项 closeout 由 `docs/exec-plans/CHORE-0125-fr-0008-parent-closeout.md` 记录 `#140` 执行回合，并负责把 `#127` 的关闭语义、release / sprint 索引和 GitHub 真相收口到同一条证据链。

## 最近一次 checkpoint 对应的 head SHA

- `b6ebf00dce8cb0182b81b077fb1255270f1ee803`
