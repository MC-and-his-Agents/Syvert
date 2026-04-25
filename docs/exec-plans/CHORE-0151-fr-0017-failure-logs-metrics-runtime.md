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
- guardian 初审要求补齐 pre-accepted failure、admission concurrency control ref、retry scheduling、persistence phase 与 resource trace refs 五类 FR-0017 关联 truth；当前修复已落到同一 Core path。

## 下一步动作

- 推送 guardian review-sync 修复提交。
- 重跑 CI、guardian、merge gate。
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
- `python3 -m unittest tests.runtime.test_task_record_store tests.runtime.test_runtime tests.runtime.test_http_api tests.runtime.test_cli_http_same_path tests.runtime.test_execution_control tests.runtime.test_runtime_observability`
  - 初始结果：通过，`Ran 161 tests`，`OK`。
  - guardian review-sync 后结果：通过，`Ran 164 tests`，`OK`。
  - guardian 第二轮 review-sync 后结果：通过，`Ran 165 tests`，`OK`。
- `python3 -m unittest discover -s tests`
  - 结果：通过，`Ran 376 tests`，`OK`。
- `python3 scripts/governance_gate.py --mode local --base-ref origin/main`
  - 结果：通过。

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
- 本次追加 checkpoint 元数据属于 `metadata-only review sync`，不推进新的 runtime / formal spec 语义。
