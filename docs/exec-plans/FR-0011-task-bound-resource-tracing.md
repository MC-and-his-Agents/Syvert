# FR-0011 执行计划（requirement container）

## 关联信息

- item_key：`FR-0011-task-bound-resource-tracing`
- Issue：`#165`
- item_type：`FR`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 spec：`docs/specs/FR-0011-task-bound-resource-tracing/`
- 关联 PR：`#169`
- 状态：`inactive requirement container`

## 说明

- `FR-0011` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- 当前 formal spec closeout 由 `docs/exec-plans/CHORE-0131-fr-0011-formal-spec-closeout.md` 记录 `#166` 的执行轮次，当前受审 PR 为 `#169`。
- `FR-0011` 只冻结 task-bound tracing / usage log truth、事件类型与最小审计面，不重新定义资源生命周期主 contract。
- `FR-0011` 必须复用 `FR-0010` 已冻结的资源类型、状态名、bundle/lease carrier 与 fail-closed 边界。
- 后续实现 Work Item 必须消费本 formal spec，而不是在 tracing 实现中另建新的事件词汇或影子日志 schema。
- 当前分支已形成最新 formal spec 语义 checkpoint `8241217d65fe9dda57a783b55cbdec5d040f14de`，其后若仅追加 exec-plan / PR metadata，只作为 review-sync follow-up，不改写 requirement 语义。

## 最近一次 checkpoint 对应的 head SHA

- `8241217d65fe9dda57a783b55cbdec5d040f14de`
