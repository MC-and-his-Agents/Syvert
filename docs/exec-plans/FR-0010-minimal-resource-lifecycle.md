# FR-0010 执行计划（requirement container）

## 关联信息

- item_key：`FR-0010-minimal-resource-lifecycle`
- Issue：`#163`
- item_type：`FR`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 spec：`docs/specs/FR-0010-minimal-resource-lifecycle/`
- 关联 PR：`#170`
- 状态：`inactive requirement container`

## 说明

- `FR-0010` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- 当前 formal spec closeout 由 `docs/exec-plans/CHORE-0130-fr-0010-formal-spec-closeout.md` 记录 `#164` 的执行轮次，当前受审 PR 为 `#170`。
- `FR-0010` 冻结资源生命周期主 contract：资源类型、bundle/lease carrier、状态迁移、`acquire / release` 语义，以及 host-side durable snapshot / bootstrap / revision / 默认本地入口 traceability。
- task-bound tracing / audit contract 留给 `FR-0011`，Adapter 注入边界留给 `FR-0012`；相邻事项不得反向改写本 FR 的主 contract。
- 后续实现 Work Item 必须消费本 formal spec，而不是在实现 PR 中重开状态名、slot 命名或 lease 语义。
- 当前分支已形成最新 formal spec 语义 checkpoint `c6b76888bda690a5d3a781723af647174a77659a`；`#177` 继续补齐 store/bootstrap traceability 后，requirement baseline 需要同步覆盖 snapshot / bootstrap / revision / 默认本地入口语义，避免 formal suite 内部漂移。

## 最近一次 checkpoint 对应的 head SHA

- `c6b76888bda690a5d3a781723af647174a77659a`
