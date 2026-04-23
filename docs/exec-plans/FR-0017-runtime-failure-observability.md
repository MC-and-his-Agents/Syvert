# FR-0017 执行计划（requirement container）

## 关联信息

- item_key：`FR-0017-runtime-failure-observability`
- Issue：`#220`
- item_type：`FR`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 spec：`docs/specs/FR-0017-runtime-failure-observability/`
- 关联 PR：`待创建`
- 状态：`inactive requirement container`

## 说明

- `FR-0017` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- 当前 formal spec closeout 由 `docs/exec-plans/CHORE-0150-fr-0017-formal-spec-closeout.md` 承担 `#226` 的执行轮次；本 FR 自身不直接成为执行入口。
- `FR-0017` 只冻结运行时失败可观测性的最小 formal contract：失败分类投影、结构化日志、最小执行指标，以及它们与 `task_id`、TaskRecord、failed envelope、resource trace 和 `FR-0016` timeout / retry / concurrency 结果的关联规则。
- `FR-0017` 不重写 `FR-0005` 的错误分类，不重写 `FR-0008` 的 TaskRecord，不重写 `FR-0011` 的 resource tracing truth，也不重写 `FR-0016` 的 runtime control 语义。
- 后续 `#227` 作为 runtime implementation Work Item 消费本 formal spec；`#228` 作为 parent closeout Work Item 收口 GitHub 状态、repo semantic truth、主干与 PR 状态一致性。

## 最近一次 checkpoint 对应的 head SHA

- `待生成`
