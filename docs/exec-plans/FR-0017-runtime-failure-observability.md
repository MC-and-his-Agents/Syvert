# FR-0017 执行计划（requirement container）

## 关联信息

- item_key：`FR-0017-runtime-failure-observability`
- Issue：`#220`
- item_type：`FR`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 spec：`docs/specs/FR-0017-runtime-failure-observability/`
- 关联 PR：`N/A（requirement container 不直接承载 PR；当前 formal spec 执行 PR 见 #239）`
- 状态：`inactive requirement container`

## 说明

- `FR-0017` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- formal spec closeout 已由 `docs/exec-plans/CHORE-0150-fr-0017-formal-spec-closeout.md` / `#226` / PR `#239` 收口并合入主干。
- runtime implementation 已由 `docs/exec-plans/CHORE-0151-fr-0017-failure-logs-metrics-runtime.md` / `#227` / PR `#249` 收口并合入主干。
- parent closeout 由 `docs/exec-plans/CHORE-0152-fr-0017-parent-closeout.md` / `#228` 承担，只同步 GitHub 状态、主干事实与后续 gate 引用。
- `FR-0017` 只冻结运行时失败可观测性的最小 formal contract：失败分类投影、结构化日志、最小执行指标，以及它们与 `task_id`、TaskRecord、failed envelope、resource trace 和 `FR-0016` 的 `ExecutionAttemptOutcome` / `ExecutionControlEvent` 的关联规则。
- `FR-0017` 不重写 `FR-0005` 的错误分类，不重写 `FR-0008` 的 TaskRecord，不重写 `FR-0011` 的 resource tracing truth，也不重写 `FR-0016` 的 runtime control 语义；本 FR 只收紧正常 `execution_timeout` 的 observability 投影、固定 retryable predicate 的观测边界，以及 `admission_concurrency_rejected` / `retry_concurrency_rejected` 的日志与指标区分。
- `FR-0017` 完成后为 `FR-0019/#234` 提供 `failure_log_metrics` 维度的 formal spec 与 runtime evidence 输入。

## closeout 证据

- formal spec closeout：PR `#239`，merge commit `3bff42393da63da3100a5a99dc0c16f043a6b180`。
- runtime implementation：PR `#249`，merge commit `d0ae78b6c96789f0c16b541bac14694dd1ad9df4`。
- parent closeout：`#228` / `CHORE-0152-fr-0017-parent-closeout` 负责同步 GitHub 状态、主干事实与后续 gate 引用。

## 最近一次 checkpoint 对应的 head SHA

- `7622327c418d78e1e0eb966c4ed51349cbec294b`
