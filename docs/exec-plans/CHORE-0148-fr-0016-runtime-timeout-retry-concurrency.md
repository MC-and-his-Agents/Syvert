# CHORE-0148 FR-0016 runtime timeout/retry/concurrency 执行计划

## 关联信息

- item_key：`CHORE-0148-fr-0016-runtime-timeout-retry-concurrency`
- Issue：`#224`
- item_type：`CHORE`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 spec：`docs/specs/FR-0016-minimal-execution-controls/`
- 关联 PR：`#247`
- 状态：`active`

## 目标

- 在 `FR-0016` 已冻结边界内实现 Core-owned 最小执行控制 runtime：attempt 级 timeout、固定 retry predicate、process-local fail-fast concurrency slot。
- 保持 CLI / HTTP / adapter 入口只消费同一 Core path，不在入口层或 adapter 私有层维护第二套控制真相。
- 所有 attempts 共享同一 `task_id` 与同一条 durable `TaskRecord`；attempt/control 事实通过 JSON-safe `runtime_result_refs` 与 `execution_control_events` 投影。

## 范围

- 本次纳入：
  - `syvert/runtime.py` Core attempt orchestration
  - timeout -> `platform/execution_timeout` 与 `details.control_code=execution_timeout`
  - retryable predicate：`execution_timeout` 或 `platform + details.retryable=true`，且 capability 为 `content_detail_by_url`
  - process-local concurrency scopes：`global`、`adapter`、`adapter_capability`
  - pre-accepted concurrency rejection：`invalid_input/concurrency_limit_exceeded` 且不创建 `TaskRecord`
  - post-accepted retry reacquire rejection：保留上一 attempt 终态 error，仅追加 `ExecutionControlEvent`
  - `tests/runtime/test_execution_control.py`
- 本次不纳入：
  - 分布式调度、队列、取消/暂停/恢复、复杂 retry DSL
  - HTTP endpoint shape 变更
  - `FR-0017/#227` observability carrier runtime
  - `FR-0019/#234` operability gate runner

## 当前停点

- 已通过 `python3 scripts/create_worktree.py --issue 224 --class implementation` 创建 worktree：`/Users/mc/code/worktrees/syvert/issue-224-fr-0016`。
- 已确认主干基线为 `65657a49536eb7ad83ea1cf666d0a43f233f67fa`，包含 `#230/#231` 的 HTTP / CLI same-path evidence。
- 已在 Core path 中加入最小 attempt orchestration，保留现有 `TaskRecord` 生命周期：accepted -> running -> 单次 terminal finish。
- 已新增执行控制回归测试，覆盖 timeout、retry、非 retry、adapter-owned `execution_timeout` 不冒充 Core timeout、pre/post accepted concurrency rejection、accepted persistence 与 resource preparation 不计入 `max_in_flight`、slot release underflow fail-closed、hung adapter timeout fail-closed、hung closeout failure 资源 `INVALID` quarantine 与 slot 延迟释放、timeout grace late disposition hint consumption、malformed late hint fail-closed、timeout closeout quarantine、retry control details 回写、`ExecutionAttemptOutcome.control_code` shape、`ended_at` 晚于资源 release 的可复核时间顺序、FR-0016 carrier 字段与三类 scope。

## FR-0016 concurrency 语义决策

- 本事项同时保持两条 `FR-0016` 边界：`max_in_flight` 只表达同 scope 内处于 adapter execution attempt 阶段的数量；首次并发获取失败必须在 durable accepted 前 fail-fast 为 `invalid_input/concurrency_limit_exceeded`，且不创建 `TaskRecord`。
- 为消除 admission 检查与真实 execution slot 获取之间的 TOCTOU，Core 使用不计入 `max_in_flight` 的 per-scope admission guard 串行化首次 attempt admission；该 guard 不是 execution slot，不作为 caller-visible in-flight 事实。
- 首次 execution slot 只在资源准备完成、即将进入 adapter execution 前获取；获取成功后释放 admission guard，并在 attempt closeout 后释放 execution slot。若同 scope 已有真实 execution slot，guard 内 fail-fast 拒绝且不创建 `TaskRecord`。
- retry 不复用上一 attempt 的 slot；只有上一 attempt 已完成资源 closeout 与 slot release 后才重新获取下一轮 slot。若 retry reacquire 被拒绝，只追加 `retry_concurrency_rejected` control event，不改写上一 attempt 的终态分类。
- 本事项不提供队列、调度器或跨进程限流能力；admission guard 仅用于本地同步 Core 的 contract-preserving atomicity。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.6.0` 提供 `timeout_retry_concurrency` 的真实 runtime evidence，使后续 `FR-0019/#234` gate matrix 可以消费可复验结果。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0016` implementation Work Item。
- 阻塞：
  - `#225` parent closeout 依赖本事项实现与 PR 合入。
  - `#234` operability gate matrix 的 `timeout_retry_concurrency` 维度依赖本事项 runtime evidence。

## 已验证项

- `python3 -m py_compile syvert/runtime.py tests/runtime/test_execution_control.py`
  - 结果：通过。
- `python3 -m unittest tests.runtime.test_execution_control -v`
  - 结果：通过，`Ran 16 tests`，`OK`。
- `python3 -m unittest tests.runtime.test_execution_control tests.runtime.test_cli_http_same_path -q`
  - 结果：通过，`Ran 28 tests`，`OK`。
- `python3 -m unittest tests.runtime.test_runtime tests.runtime.test_http_api tests.runtime.test_cli_http_same_path tests.runtime.test_task_record_store tests.runtime.test_version_gate tests.runtime.test_execution_control`
  - 结果：通过，`Ran 255 tests`，`OK`。
- `python3 -m unittest discover -s tests`
  - 结果：通过，`Ran 376 tests`，`OK`。
- `python3 scripts/governance_gate.py --mode local --base-ref origin/main`
  - 结果：通过。
- 子 agent review
  - 结果：首轮指出 timeout closeout 早于 late result quarantine、runtime refs carrier 字段不足两项阻断；已修复为 timeout closeout 有界确认、hung adapter fail-closed、slot release 后生成 attempt `ended_at`，并补齐 `ExecutionAttemptOutcome` 字段与 `ExecutionControlEvent` refs。
- PR guardian
  - 结果：首轮 `REQUEST_CHANGES`，指出 hung adapter timeout path 可能无界阻塞，以及 `ExecutionAttemptOutcome.ended_at` 早于 slot release。
  - 处理：timeout closeout 改为 bounded quarantine；若 adapter thread 未在 grace 窗口内完成，返回 `runtime_contract/execution_control_state_invalid` 并释放 slot；正常 timeout 完成 closeout 后仍返回 `platform/execution_timeout`；`ExecutionAttemptOutcome.ended_at` 改为在资源 closeout 与 slot release 后生成，并使用 microseconds 精度提供可复核排序。
  - 结果：二轮 `REQUEST_CHANGES`，指出首次 concurrency slot 持有范围覆盖 admission / TaskRecord / resource preparation，以及 retry exhausted / retry concurrency rejected 未同步写入 failed envelope `error.details`。
  - 处理：admission 改为只做可用性 fail-fast 检查、不持有 slot；attempt slot 只在 resource preparation 后、adapter execution / timeout closeout 窗口内持有；retry exhausted 与 retry concurrency rejected 同步写入 `error.details.execution_control_event` 与 task-level 控制字段。
  - 子 agent 复查指出 slot acquire 后移后，resource preparation 后 acquire 失败会泄漏 managed resources，且首次 attempt race 不应投影为 pre-accepted `admission_concurrency_rejected`。
  - 处理：post-resource-prep acquire 失败先 settle managed resource bundle；首次 attempt slot race 投影为 `runtime_contract/execution_control_state_invalid`，不生成 admission event；retry attempt slot rejection 继续生成 `retry_concurrency_rejected` 并保留上一 attempt 终态 error。
  - 结果：三轮 `REQUEST_CHANGES`，指出 hung timeout closeout failure 仍将资源释放为 `AVAILABLE`，且 adapter thread still alive 时过早释放 concurrency slot。
  - 处理：`thread.is_alive()` closeout-failed 路径将 managed resources 置为 `INVALID` quarantine；concurrency slot 移交后台 watcher，等待 adapter thread 实际退出后释放；返回前同 scope admission 继续被拒绝。
  - 子 agent 复查指出 slot 延迟释放后，若仍生成 `ExecutionAttemptOutcome.ended_at`，会重新违反 `ended_at` 晚于 slot release 的时序契约。
  - 处理：hung closeout-unproven 路径不生成 `ExecutionAttemptOutcome` / `runtime_result_refs`，只返回 fail-closed envelope；避免在 slot 仍由 watcher 持有时声明 attempt 已结束。
  - 结果：四轮 `REQUEST_CHANGES`，指出首次普通并发竞争仍可能 accepted 后投影为 `runtime_contract`，以及 timeout grace 内 late result / error 的 resource disposition hint 未被消费。
  - 处理：新增 admission reservation 计数，普通并发竞争在 accepted 前 fail-fast，且不计入 adapter in-flight；真正 in-flight slot 仍只覆盖 adapter execution / timeout closeout。timeout grace 内若 late result/error 已到达，消费其 `resource_disposition_hint` 后再形成 timeout envelope。
  - 结果：五轮 `REQUEST_CHANGES`，指出 adapter 自报 `execution_timeout` 会被误判为 Core timeout retry，且非 timeout `ExecutionAttemptOutcome.control_code` 被写为空字符串。
  - 处理：Core timeout retry 改为依赖 runtime 内部 `core_timeout_outcome` 布尔，不再只看 adapter 可伪造的 error code/details；`ExecutionAttemptOutcome.control_code` 仅在真实 Core timeout outcome 上输出，其他 attempt 省略该字段。
  - 结果：六轮 `REQUEST_CHANGES`，指出 admission reservation 扩大了并发 gating 窗口，以及 timeout grace 内 malformed late hint 被误分类为 caller `invalid_input`。
  - 处理：撤销 admission reservation，precheck 仅观察真实 adapter in-flight slot；resource preparation 期间同 scope availability 保持 true。malformed late hint 在 accepted timeout closeout 中改为 `runtime_contract/execution_control_state_invalid`，并将资源 `INVALID` quarantine。
  - 结果：七轮 `REQUEST_CHANGES`，要求首次 admission 并发判定与实际 slot 保留收敛为同一原子步骤，并要求 slot release underflow fail-closed。
  - 阶段性处理：首次 execution slot 在 accepted 前原子获取，失败返回 pre-accepted `concurrency_limit_exceeded` 且不创建 `TaskRecord`；retry 仍在前一 attempt 完成后重新获取 slot。`release_execution_concurrency_slot` 对未知/0 计数返回 `runtime_contract/execution_control_state_invalid` shared failed envelope，不向调用方冒出裸异常。
  - 子 agent 复查指出 formal spec 明确 `max_in_flight` 只表达 adapter execution attempt 阶段，accepted / persistence / resource preparation 不应计入 in-flight。
  - 处理：将 admission 原子化改为不计入 `max_in_flight` 的 per-scope guard；真实 execution slot 延后到 resource preparation 完成、进入 adapter execution 前获取。新增窗口回归测试证明 accepted persistence 与 resource preparation 期间 `in_flight` 仍为 0，第二个同 scope 请求等待 guard，直到第一个进入 adapter execution 后才 pre-accepted fail-fast 且不创建 `TaskRecord`。

## 未决风险

- timeout 使用 daemon thread 执行 adapter attempt；正常 timeout outcome 形成前会在有界窗口内等待 closeout quarantine，若无法证明完成则 fail-closed 为 `runtime_contract/execution_control_state_invalid`。当前满足本地单进程 runtime 与测试复验，不承诺生产级抢占或跨进程取消。
- process-local concurrency slot 不提供分布式一致性；这符合 `FR-0016` v0.6.0 边界。
- `runtime_result_refs` 目前只在失败、多 attempt 或 control event 场景写入，避免单 attempt success 改变既有 CLI/HTTP same-path record equality。

## 回滚方式

- 使用独立 revert PR 撤销 `syvert/runtime.py`、`tests/runtime/test_execution_control.py` 与本 exec-plan 的增量。
- 不回滚 `FR-0016` formal spec，不修改 `FR-0017` / `FR-0019` 下游边界。

## 最近一次 checkpoint 对应的 head SHA

- `65657a49536eb7ad83ea1cf666d0a43f233f67fa` 为开始实现时的主干基线。
- `44ecd3a9b2f61838d59ad5ae6dcc89bcaa307182` 为首轮 PR head；后续 guardian blocker 修复提交 SHA 以 PR head 为准。
