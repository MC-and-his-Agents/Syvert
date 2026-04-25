# CHORE-0151 FR-0017 failure/log/metrics runtime 执行计划

## 关联信息

- item_key：`CHORE-0151-fr-0017-failure-logs-metrics-runtime`
- Issue：`#227`
- item_type：`CHORE`
- release：`v0.6.0`
- sprint：`2026-S19`
- 父 FR：`#220`
- 关联 spec：`docs/specs/FR-0017-runtime-failure-observability/`
- 状态：`active`

## 目标

- 在 `FR-0017` 边界内实现最小 runtime observability carrier：`RuntimeFailureSignal`、`RuntimeStructuredLogEvent`、`RuntimeExecutionMetricSample`。
- 失败分类从 shared failed envelope 投影，不新增第二套错误 taxonomy，不改写 success `raw` / `normalized` payload。
- 将 carrier 落到同一 Core path 与 durable `TaskRecord` truth，供 CLI / HTTP / review / gate 后续消费。

## 范围

- 本次纳入：
  - `syvert/runtime.py`
  - `syvert/task_record.py`
  - `tests/runtime/test_runtime_observability.py`
  - `docs/exec-plans/CHORE-0151-fr-0017-failure-logs-metrics-runtime.md`
- 本次不纳入：
  - 外部日志后端、metrics backend、dashboard、OpenTelemetry / Prometheus 集成
  - adapter 私有平台 taxonomy
  - success envelope contract 改写
  - `FR-0019/#234` gate matrix

## 当前停点

- 已通过 `python3 scripts/create_worktree.py --issue 227 --class implementation` 创建 worktree：`/Users/mc/code/worktrees/syvert/issue-227-fr-0017`。
- 当前主干基线为 `3c57ec6ce6437b0e810645b104fd85d6bf1235ba`，已包含 `FR-0016` closeout。
- 已在 runtime helper 层为 failed envelope 投影最小 failure signal、structured log event 与 metric sample。
- 已扩展 `TaskRecord` JSON-safe durable fields：`runtime_failure_signals`、`runtime_structured_log_events`、`runtime_execution_metric_samples`。
- guardian 多轮审查要求补齐 pre-accepted failure、admission concurrency control ref、retry scheduling、persistence phase、resource trace refs、success envelope 边界与 observability write failure 保留语义；当前修复已落到同一 Core path。
- 已按本地 reviewer 复核补齐 `ExecutionAttemptOutcome.terminal_envelope` 与 FR-0017 carrier 去重边界、`observability_write_failed` metric allowlist 边界，以及 execution-control runtime_contract 的真实 phase 投影。
- 已按 guardian 第五轮审查补齐 success/lifecycle structured logs 与 minimal metrics、post-accepted failed signal 的 durable `task_record_ref` 重投影、retry-then-success 中间失败 signal 顶层持久化，以及 observability 同 ID identical replay / conflict fail-closed 约束。
- 已按 guardian 第六轮审查补齐 repeated identical retry failure 的 per-attempt signal identity，以及 failed terminal path 的 attempt lifecycle log/metric 保留。
- 已按 guardian 第七轮审查收敛 FR-0017 注入边界、`envelope_ref` occurrence identity，以及 durable observability carrier 枚举校验。
- 已按 guardian 第八轮审查补齐 record lifecycle fail-closed 分支的 FR-0017 carrier，并收紧 failed log / metric 必填引用和错误元数据校验。
- 已按 guardian 第九轮审查收窄 `retry_scheduled.runtime_result_refs` 至直接前因，并修正 terminal observability reconciliation 的 append-only superset 约束。

## 下一步动作

- 推送第九轮 guardian review-sync 修复提交。
- 等待 CI 重新全绿后重跑 guardian 与 merge gate。
- 合入后同步 `#227` issue / Project 状态，并进入 `#228` parent closeout。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.6.0` 提供 `failure_log_metrics` 维度 runtime evidence，使后续 `FR-0019/#234` gate matrix 可以消费可复验 observability carrier。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0017` implementation Work Item。
- 阻塞：
  - `#228` parent closeout 依赖本事项实现与 PR 合入。
  - `#234` operability gate matrix 的 `failure_log_metrics` 维度依赖本事项 runtime evidence。

## 已验证项

- `python3 -m py_compile syvert/runtime.py syvert/task_record.py tests/runtime/test_runtime_observability.py`
  - 结果：通过。
- `python3 -m unittest tests.runtime.test_runtime_observability -v`
  - 初始结果：通过，`Ran 5 tests`，`OK`。
  - guardian review-sync 后结果：通过，`Ran 8 tests`，`OK`。
  - guardian 第二轮 review-sync 后结果：通过，`Ran 9 tests`，`OK`。
  - guardian 第三轮 review-sync 后结果：通过，`Ran 11 tests`，`OK`。
  - guardian 第四轮 review-sync 后结果：通过，`Ran 11 tests`，`OK`。
  - 本地 reviewer 复核修复后结果：通过，`Ran 13 tests`，`OK`。
- guardian 第五轮 review-sync 后结果：通过，`Ran 13 tests`，`OK`。
  - guardian 第六轮 review-sync 后结果：通过，`Ran 14 tests`，`OK`。
  - guardian 第七轮 review-sync 后结果：通过，`Ran 15 tests`，`OK`。
- `python3 -m unittest tests.runtime.test_task_record_store tests.runtime.test_runtime tests.runtime.test_http_api tests.runtime.test_cli_http_same_path tests.runtime.test_execution_control tests.runtime.test_runtime_observability`
  - 初始结果：通过，`Ran 161 tests`，`OK`。
  - guardian review-sync 后结果：通过，`Ran 164 tests`，`OK`。
  - guardian 第二轮 review-sync 后结果：通过，`Ran 165 tests`，`OK`。
  - guardian 第三轮 review-sync 后结果：通过，`Ran 167 tests`，`OK`。
  - guardian 第四轮 review-sync 后结果：通过，`Ran 167 tests`，`OK`。
  - 本地 reviewer 复核修复后结果：通过，`Ran 169 tests`，`OK`。
- `python3 -m unittest tests.runtime.test_task_record_store tests.runtime.test_runtime tests.runtime.test_http_api tests.runtime.test_cli_http_same_path tests.runtime.test_execution_control tests.runtime.test_runtime_observability tests.runtime.test_task_record`
  - guardian 第五轮 review-sync 后结果：通过，`Ran 190 tests`，`OK`。
  - guardian 第六轮 review-sync 后结果：通过，`Ran 191 tests`，`OK`。
  - guardian 第七轮 review-sync 后结果：通过，`Ran 193 tests`，`OK`。
  - guardian 第八轮 review-sync 后结果：通过，`Ran 195 tests`，`OK`。
  - guardian 第九轮 review-sync 后结果：通过，`Ran 196 tests`，`OK`。
- `python3 -m unittest discover -s tests`
  - 结果：通过，`Ran 376 tests`，`OK`。
  - guardian 第四轮 review-sync 后结果：通过，`Ran 376 tests`，`OK`。
  - 本地 reviewer 复核修复后结果：通过，`Ran 376 tests`，`OK`。
  - guardian 第五轮 review-sync 后结果：通过，`Ran 376 tests`，`OK`。
  - guardian 第六轮 review-sync 后结果：通过，`Ran 376 tests`，`OK`。
  - guardian 第七轮 review-sync 后结果：通过，`Ran 376 tests`，`OK`。
  - guardian 第八轮 review-sync 后结果：通过，`Ran 376 tests`，`OK`。
  - guardian 第九轮 review-sync 后结果：通过，`Ran 376 tests`，`OK`。
- `python3 scripts/governance_gate.py --mode local --base-ref origin/main`
  - 结果：通过。
  - guardian 第四轮 review-sync 后结果：通过。
  - 本地 reviewer 复核修复后结果：通过。
  - guardian 第五轮 review-sync 后结果：通过。
  - guardian 第六轮 review-sync 后结果：通过。
  - guardian 第七轮 review-sync 后结果：通过。
  - guardian 第八轮 review-sync 后结果：通过。
  - guardian 第九轮 review-sync 后结果：通过。
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - guardian 第四轮 review-sync 后结果：通过。
  - 本地 reviewer 复核修复后结果：通过。
  - guardian 第五轮 review-sync 后结果：通过。
  - guardian 第六轮 review-sync 后结果：通过。
  - guardian 第七轮 review-sync 后结果：通过。
  - guardian 第八轮 review-sync 后结果：通过。
  - guardian 第九轮 review-sync 后结果：通过。

## guardian review-sync

- PR `#249` 初次 guardian 结论：`REQUEST_CHANGES`。
- 已处理阻断项：
  - pre-accepted failure 统一投影 `task_record_ref=none` 与 `stage=pre_admission`。
  - admission concurrency rejection 的 `ExecutionControlEvent` 同步进入 `runtime_result_refs`。
  - retry predicate 命中且预算允许时生成 `retry_scheduled` structured log 与 `retry_scheduled_total` metric，不新增 FR-0016 control event。
  - persistence / completion 写入失败投影 `failure_phase=persistence`。
  - 已 acquire 资源后的 failed envelope 注入 FR-0011 `resource_trace_refs`，并同步到 failure signal / structured log。
- PR `#249` 第二次 guardian 结论：`REQUEST_CHANGES`。
- 已处理阻断项：
  - failed envelope 再投影时只保留 `retry_scheduled` lifecycle carrier，并重建唯一一组 failure signal/log/metric，避免同一失败出现重复且不一致的 observability truth。
  - retry 成功路径只保留既有 `runtime_result_refs` 执行控制证据，不把 `runtime_failure_signal`、`runtime_structured_log_events` 或 `runtime_execution_metric_samples` 写入 success envelope。
- PR `#249` 第三次 guardian 结论：`REQUEST_CHANGES`。
- 已处理阻断项：
  - `failure_phase` 改为按明确 stage / event / error code 投影，避免用宽泛 error category 伪造阶段。
  - failed observability 默认 `task_record_ref=none`；进入 accepted/running/attempt 后由 runtime/finalize 明确补 `task_record:{task_id}`。
  - failed terminal persistence / completion observability 写入失败时保留原业务 failed envelope，并追加 `observability_write_failed` structured log / metric。
  - retry-then-success 的 `retry_scheduled` log/metric 只持久化到 `TaskRecord` 顶层 carrier，success result envelope 不新增 FR-0017 字段。
- PR `#249` 第四次 guardian 结论：`REQUEST_CHANGES`，本地结果已写入 guardian cache，但 GitHub comment 因 GraphQL 配额耗尽未完成发布。
- 已处理阻断项：
  - retry-then-success 的内部 `_runtime_structured_log_events` / `_runtime_execution_metric_samples` 仅作为 `TaskRecord` 顶层持久化输入，`execute_task` / `execute_task_with_record` 公共 success envelope 返回前剥离私有字段。
  - failure observability 重建时保留 `retry_scheduled` 与 `observability_write_failed` lifecycle carrier，避免 completion-time observability write failure 被后续投影覆盖。
  - admission guard release failure 按 durable accepted 边界设置 `task_record_ref`：accepted 前为 `none`，accepted 后为 `task_record:{task_id}`。
- PR `#249` 第四轮后本地 reviewer 复核发现 3 个潜在阻断点。
- 已处理复核项：
  - `ExecutionAttemptOutcome.terminal_envelope` 剥离 `runtime_failure_signal`、`runtime_structured_log_events`、`runtime_execution_metric_samples` 与内部私有 observability 字段，避免 attempt 快照和 canonical failed envelope 出现重复不一致 carrier。
  - `observability_write_failed` 仅作为 `RuntimeStructuredLogEvent` 暴露，不再生成未被 FR-0017 metric allowlist 批准的 `observability_write_failed_total`；该日志回指原业务 `RuntimeFailureSignal.signal_id` 并保留 resource trace refs。
  - 默认 execution-control policy 物化失败投影为 `failure_phase=pre_execution`；guarded admission 后 slot 消失投影为 `failure_phase=concurrency_rejected`，不再兜底成 `adapter_execution`。
- PR `#249` 第五次 guardian 结论：`REQUEST_CHANGES`。
- 已处理阻断项：
  - `TaskRecord` 顶层持久化 `task_accepted`、`task_running`、`attempt_started`、`attempt_finished`、`task_succeeded` lifecycle structured logs，以及 `task_started_total`、`attempt_started_total`、`task_succeeded_total`、`execution_duration_ms` minimal metrics；success envelope 仍不新增 FR-0017 公共字段。
  - `finalize_task_execution_result` 在 post-accepted failed envelope 补入 durable `task_record_ref` 后重投影 failure signal/log/metric，避免 `error.details.task_record_ref` 与 `RuntimeFailureSignal.task_record_ref` 漂移。
  - retry-then-success 会把中间失败的 `RuntimeFailureSignal` 持久化到 `TaskRecord.runtime_failure_signals` 顶层，使 `retry_scheduled.failure_signal_id` 有可追溯目标，同时不污染 success result envelope。
  - `TaskRecord` 校验同一 `signal_id` / `event_id` / `metric_id` 的 identical replay；store reconciliation 只允许 terminal incoming observability 作为无冲突 superset 合入，冲突性同 ID payload fail-closed。
- PR `#249` 第六次 guardian 结论：`REQUEST_CHANGES`。
- 已处理阻断项：
  - `RuntimeFailureSignal.signal_id`、`task_failed` log id 与 failed metric id 纳入 `attempt_index`，同一 task 中重复相同 retryable failure 会保留不同 occurrence 的 signal，不触发同 ID 不同 payload 冲突。
  - failed path 的 `with_failure_observability` 保留已有 `attempt_started` / `attempt_finished` structured logs 与 `attempt_started_total` / `execution_duration_ms` metrics，确保失败终态 durable carrier 不丢 attempt lifecycle evidence。
- PR `#249` 第七次 guardian 结论：`REQUEST_CHANGES`。
- 已处理阻断项：
  - `failure_envelope(...)` 重新收敛为纯 shared failed envelope helper，不再无条件注入 FR-0017 carrier；runtime 主路径通过 `pre_accepted_failure_envelope`、`with_runtime_observability` 与 `finalize_task_execution_result` 显式投影 observability。
  - `RuntimeFailureSignal.envelope_ref` 增加 attempt occurrence 维度，与 repeated identical failures 的 per-attempt `signal_id` 对齐。
  - `TaskRecord` durable observability carrier 校验固定枚举与语义：`failure_phase`、`event_type`、`level`、`metric_name`、metric unit/value、上下文绑定和失败日志 signal 引用。
- PR `#249` 第八次 guardian 结论：`REQUEST_CHANGES`。
- 已处理阻断项：
  - record lifecycle fail-closed 分支统一注入 FR-0017 runtime observability：`create_task_record` 前失败走 pre-accepted carrier；`start_task_record` / running persistence 后失败走 durable `TaskRecord` completion finalize；success envelope 收口为 JSON-safe terminal record 失败时，转为 `runtime_contract/envelope_not_json_serializable` 并绑定 durable `task_record_ref`。
  - `TaskRecord` durable validation 明确拒绝 failed structured log 缺失或悬空 `failure_signal_id`，覆盖 `admission_concurrency_rejected`、`retry_concurrency_rejected`、`task_failed`、`timeout_triggered`、`retry_scheduled`、`observability_write_failed`。
  - `TaskRecord` durable validation 明确拒绝 failed metrics 缺失 `error_category/error_code/failure_phase`，覆盖 `task_failed_total`、`timeout_total`、`admission_concurrency_rejected_total`、`retry_concurrency_rejected_total`。
- PR `#249` 第九次 guardian 结论：`REQUEST_CHANGES`；GitHub review comment 因 GraphQL quota exhausted 未发布，本地 JSON evidence 为 `/tmp/syvert-guardian-249-7339885.json`。
- 已处理阻断项：
  - `retry_scheduled` structured log 的 `runtime_result_refs` 从累计 execution history 收窄为触发本次 retry 的直接 `ExecutionAttemptOutcome`，避免第二次及后续 retry 混入更早 attempt / control refs。
  - `LocalTaskRecordStore` terminal reconciliation 在同 ID 无冲突之外，进一步要求 incoming terminal observability 是 candidate durable observability 的 superset；较小子集不再能覆盖既有 lifecycle / metric truth。

## 未决风险

- 当前 metrics / logs 是 JSON-safe local carrier，不是持久化指标后端。
- 当前 structured log event 使用最小事件集合；更完整的 duration metrics 或 observability-write failure 注入测试可在后续 gate / closeout 中扩展。
- `TaskRecord` 新字段保持 additive；旧记录缺字段时按空数组解析。

## 回滚方式

- 使用独立 revert PR 撤销 `syvert/runtime.py`、`syvert/task_record.py`、`tests/runtime/test_runtime_observability.py` 与本 exec-plan 的增量。
- 不回滚 `FR-0017` formal spec，不修改 `FR-0016` / `FR-0018` / `FR-0019` 边界。

## 最近一次 checkpoint 对应的 head SHA

- `3c57ec6ce6437b0e810645b104fd85d6bf1235ba` 为开始实现时的主干基线。
- guardian review-sync 可恢复 checkpoint：`9a1239e70f1ff76580ee3a0775815d9a7cdf5ffd`。
- guardian 第二轮 review-sync 可恢复 checkpoint：`3b2883728374972d02637d1e0e61a63306bbd549`。
- guardian 第三轮 review-sync 可恢复 checkpoint：`288c26667e98a74e38feea26a777885fb093f98c`。
- guardian 第四轮 review-sync 可恢复 checkpoint：`9ba4cf56f7837d24307227ec1db12101cba6fe66`。
- guardian 第七轮 review-sync 可恢复 checkpoint：`8eb978c55a91143cb0c9fb975fe93bd8528b55c7`。
- guardian 第八轮 review-sync 可恢复 checkpoint：`7339885287f2bb55b858fba96e5ad61302c04842`。
- guardian 第九轮 review-sync 待提交；本轮不推进 formal spec 语义。
