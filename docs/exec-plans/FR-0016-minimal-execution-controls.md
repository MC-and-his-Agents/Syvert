# FR-0016 执行计划（requirement container）

## 关联信息

- item_key：`FR-0016-minimal-execution-controls`
- Issue：`#219`
- item_type：`FR`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 spec：`docs/specs/FR-0016-minimal-execution-controls/`
- 关联 PR：`#237`
- 状态：`inactive requirement container`

## 说明

- `FR-0016` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- 当前 formal spec closeout 由 `docs/exec-plans/CHORE-0147-fr-0016-formal-spec-closeout.md` 承担；formal spec 收口、review-sync 与 PR 元数据必须统一回写到该 Work Item，而不是在 requirement container 中混入执行态细节。
- `FR-0016` 冻结 Core 最小执行控制 contract：`ExecutionControlPolicy`、attempt timeout、基础 retry 与 fail-fast concurrency gate。
- `FR-0016` 不实现 runtime，不定义 HTTP API，不建立 observability 平台，不重写 `FR-0005` 错误分类闭集，不扩张 `FR-0013` 到 `FR-0015` 的资源能力与 provider 边界。
- 后续 `#224` implementation Work Item 必须直接消费本 formal spec；若需要队列、优先级、公平性、取消、恢复、复杂 backoff 或分布式 slot，必须通过新的 formal spec 推进。

## 最近一次 checkpoint 对应的 head SHA

- `ad14f84f8e2c6b7a3df8b266fbd204859a5b2257`
