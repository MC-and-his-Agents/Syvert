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
- `FR-0018` 还必须直接消费 `FR-0016` 的最小执行控制语义：`ExecutionControlPolicy` 作为 caller-visible canonical carrier 的默认值、字段可见性与错误边界必须保持一致；HTTP transport 不得在 Core 外单独物化 timeout / retry / concurrency 私有默认值，也不得把 caller-supplied policy 非法形状宽松修补成可执行请求。
- `FR-0018` 对 retry 的 requirement 必须与 `FR-0016` 一致：retryable predicate 只允许“closeout 已完成的 `execution_timeout`”或“`error.category=platform` 且 `error.details.retryable=true`”两类 outcome，且两类 outcome 都必须通过 Core idempotency safety gate；HTTP `submit` 不得把整个 `platform` category、`invalid_input`、`unsupported` 或一般 `runtime_contract` 失败扩张成 transport 私有 retry 语义。
- `FR-0018` 对 timeout / concurrency 的 requirement 必须与 `FR-0016` 一致：正常 `execution_timeout` 必须继续投影为 `platform`，并通过 `error.details.control_code=execution_timeout` 暴露控制面来源；只有 timeout closeout、slot accounting 或其他 control-state failure 才能进入 `runtime_contract`。pre-accepted concurrency rejection 继续返回 `invalid_input` failed envelope 且不创建 `TaskRecord`；post-accepted retry slot reacquire rejection 只能通过 `ExecutionControlEvent` / failed envelope details 收口，不得改写上一已完成 attempt 的终态 `error.code` / `error.category`。
- `FR-0018` 还必须消费 `FR-0017` 的失败可观测性 contract：HTTP `submit/status/result` 暴露的失败、状态与结果语义不得吞掉结构化日志、最小执行指标、`runtime_result_refs`、`task_record_ref` 或与 shared failed envelope 对应的观测真相；若 transport 无法证明这些 shared signal 已与同一 `task_id` 对齐，则必须 fail-closed，而不是返回 transport 私有摘要。
- `FR-0018` 不纳入认证、多租户、RBAC、分布式队列、复杂查询 DSL、完整控制台或 adapter 直连旁路；若后续需要扩张这些能力，必须进入新的 formal spec。
- `#230` 只负责落地 HTTP endpoint implementation；`#231` 只负责 CLI/API same-path regression evidence；`#232` 只负责 FR parent closeout。上述后续 Work Item 都只能消费本 requirement container 已冻结的边界，不得自行扩张 requirement。
- 当前执行回合的 formal spec 语义基线绑定到 `49b1e4a3fa1dc61b8ffb866c50293bd8843d2fb4`；其后若只追加 PR / checks / review-sync metadata，不改写本 requirement container 的共享语义。

## 依赖关系

- 上游 formal spec 依赖：`FR-0005` 错误分类闭集、`FR-0008` durable `TaskRecord`、`FR-0009` same-path query、`FR-0016` execution control、`FR-0017` runtime failure observability。
- `FR-0018` 对上游依赖的消费边界固定为“HTTP transport 只做 ingress/egress 投影，不拥有独立执行真相”；任何 `submit/status/result` 返回都必须能回映到同一条 Core path、同一条 `TaskRecord`、同一份 failed/success envelope，以及同一组 control/observability 引用。
- 下游收口依赖：`#230` 必须证明 HTTP endpoint 只调用 Core path；`#231` 必须证明 HTTP 与 CLI 对 `TaskRecord`、failed envelope、`runtime_result_refs` 与 control/observability truth 的观察一致；`#232` 只负责收口 GitHub 状态、PR、review 与主干真相，不得重新决定 `FR-0016` / `FR-0017` 已冻结的上游语义。

## 最近一次 checkpoint 对应的 head SHA

- `49b1e4a3fa1dc61b8ffb866c50293bd8843d2fb4`
- review-sync 说明：后续若只回写当前受审 PR、门禁或审查元数据，只作为 metadata-only follow-up，不伪装成新的 requirement 语义 checkpoint。
