# FR-0018 执行计划（requirement container）

## 关联信息

- item_key：`FR-0018-http-task-api-same-core-path`
- Issue：`#221`
- item_type：`FR`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 spec：`docs/specs/FR-0018-http-task-api-same-core-path/`
- 关联 PR：`待创建`
- 状态：`inactive requirement container`

## 说明

- `FR-0018` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- 当前 formal spec closeout 由 `docs/exec-plans/CHORE-0153-fr-0018-formal-spec-closeout.md` 承担 `#229` 的执行轮次；formal spec 收口、review-sync 与后续 PR 元数据必须统一回写到该 Work Item，而不是在 requirement container 中混入执行态细节。
- `FR-0018` 只冻结最小 HTTP task API service surface：`submit`、`status`、`result`，以及它与 CLI / Core / `TaskRecord` same-core-path 的共享 contract。
- `FR-0018` 必须继续消费 `FR-0008` 的 durable `TaskRecord` truth 与 `FR-0009` 的 same-path 查询语义；HTTP service 不能反向改写这些既有 formal contract。
- `FR-0018` 不纳入认证、多租户、RBAC、分布式队列、复杂查询 DSL、完整控制台或 adapter 直连旁路；若后续需要扩张这些能力，必须进入新的 formal spec。
- `#230` 只负责落地 HTTP endpoint implementation；`#231` 只负责 CLI/API same-path regression evidence；`#232` 只负责 FR parent closeout。上述后续 Work Item 都只能消费本 requirement container 已冻结的边界，不得自行扩张 requirement。
- 当前执行回合的 formal spec 语义基线绑定到 `c8672004d316d21923a15721da46acadaa06e38a`；其后若只追加 PR / checks / review-sync metadata，不改写本 requirement container 的共享语义。

## 最近一次 checkpoint 对应的 head SHA

- `c8672004d316d21923a15721da46acadaa06e38a`
- review-sync 说明：后续若只回写当前受审 PR、门禁或审查元数据，只作为 metadata-only follow-up，不伪装成新的 requirement 语义 checkpoint。
