# FR-0019 contracts

## Contract surfaces

- `OperabilityGateResult`：`v0.6.0` operability release gate 的总体结果载体。
- `OperabilityMatrixCase`：单个回归矩阵 case 的稳定描述与执行结论。
- `SamePathProof`：CLI 与 HTTP API 对同一共享执行语义的同路径证明。
- HTTP `submit/status/result`：HTTP 入口能力语义，必须映射到 Core / task-record / store / shared envelope。
- CLI `run/query` same-path：CLI 入口能力语义，必须与 HTTP API 共享同一任务 truth。

## Required gate dimensions

- `timeout_retry_concurrency`
- `failure_log_metrics`
- `http_submit_status_result`
- `cli_api_same_path`

## Baseline dependency

`FR-0019` 不替代 `FR-0007`。任何 `OperabilityGateResult` 都必须包含可信 `baseline_gate_ref`，证明 `FR-0007` 版本级基础 gate 已被消费。缺失该引用时，`FR-0019` gate 只能输出 `fail`。

## Normative dependencies

- `FR-0016`：
  - policy 默认值必须固定为 `timeout_ms=30000`、`retry.max_attempts=1`、`retry.backoff_ms=0`、`concurrency.scope=global`、`concurrency.max_in_flight=1`、`concurrency.on_limit=reject`。
  - retryable predicate 只允许：
    - `execution_timeout`
    - `error.category=platform && error.details.retryable=true` 的 transient failure（且需通过 idempotency safety gate）
  - `execution_timeout` 必须投影为 `error.category=platform`，并带 `error.details.control_code=execution_timeout`。
  - pre-accepted concurrency rejection 必须投影 `error.category=invalid_input` 且无 `TaskRecord`。
  - post-accepted retry reacquire rejection 只允许追加 `ExecutionControlEvent.details`，不得改写上一已完成 attempt 的终态 `error.code` / `error.category`。
  - 当前批准 capability 仅 `content_detail_by_url`。
- `FR-0017`：
  - failure、结构化日志、结构化 metrics、evidence refs 必须共用同一结构化 contract。
- `FR-0018`：
  - HTTP 与 CLI 必须通过同一 Core path，复用同一 `TaskRecord` 与 shared envelope 语义。

## HTTP semantic contract

- `submit`：接收请求并进入共享 admission、共享请求投影、Core 执行与 durable 建档路径。
- `status`：读取共享 `TaskRecord` 状态，不维护 HTTP 私有状态缓存作为真相源。
- `result`：读取共享终态 envelope，不拼装 HTTP 私有结果 schema 或读取第二套结果文件。

本 FR 不固定具体 URL path、HTTP method、端口、框架、鉴权方案或部署形态。

## CLI / API same-path contract

- 等价 CLI 与 HTTP 请求必须回映到同一共享请求语义。
- 成功进入 durable 生命周期后，CLI 与 HTTP 必须读取同一类 `TaskRecord` truth。
- 成功态必须共享 success envelope 语义。
- 失败态必须共享 failed envelope 与错误分类语义。
- CLI 与 HTTP 可以有展示差异，但不得改变 task state、result envelope、error category 或 durable truth。

## Evidence contract

- evidence ref 必须稳定、去重、可本地复验。
- evidence ref 可以指向本地测试输出、CI artifact、结构化 gate result、日志索引或 metrics 聚合输出。
- 只存在于外部 SaaS dashboard、口头描述、一次性截图或生产系统中的材料不得作为唯一 gate evidence。

## Metrics snapshot contract

- `OperabilityGateResult.metrics_snapshot` 必须固定包含：
  - `submit_total`
  - `success_total`
  - `failure_total`
  - `timeout_total`
  - `retry_attempt_total`
  - `concurrency_case_total`
  - `concurrency_case_failure_total`
  - `same_path_case_total`
  - `same_path_case_failure_total`
- 任一字段缺失、不可机判或无法追溯到当前 gate revision 时，overall gate verdict 必须为 `fail`

## Matrix case contract（字段级）

每个 `OperabilityMatrixCase.expected_result` 必须使用字段级断言，不允许抽象同义词：

- 必填结构：
  - `fields[]`：`path` + `operator` + `value`
  - `side_effects[]`
  - `forbidden_mutations[]`
- `fields[]` 至少包含一个精确值断言（例如 `error.category=platform`），只写“一致”“可重试”“同路径”视为无效 case。

### Mandatory cases

以下表格是 `data-model.md` 中 canonical mandatory matrix 的人类可读投影；`case_id` 集合、mandatory membership 与字段断言不得与 `data-model.md` 漂移。

#### `timeout_retry_concurrency`

| case_id | 必须断言字段和值 |
| --- | --- |
| `trc-timeout-platform-control-code` | `policy.timeout_ms=30000`; `policy.retry.max_attempts=1`; `policy.retry.backoff_ms=0`; `error.category=platform`; `error.details.control_code=execution_timeout` |
| `trc-retryable-platform-retry-once` | `error.category=platform`; `error.details.retryable=true`; `policy.retry.max_attempts=1`; `idempotency_safety_gate=pass`; retry attempt 只允许增加一次 |
| `trc-non-retryable-fail-closed` | `retry.predicate.match=none`; `policy.retry.max_attempts=1`; 不生成新的 retry attempt |
| `trc-retry-budget-exhausted` | `policy.retry.max_attempts=1`; `retry.attempts=1`; `retry.exhausted=true`; 不生成第二次 retry attempt |
| `trc-pre-accept-concurrency-reject` | `request_ref != ""`; `stage=pre_admission`; `result.status=failed`; `policy.concurrency.scope=global`; `policy.concurrency.max_in_flight=1`; `policy.concurrency.on_limit=reject`; `error.category=invalid_input`; `metrics.concurrency_case_total>=1`; `TaskRecord` 不存在 |
| `trc-concurrent-status-shared-truth` | `status.read_a.task_id == status.read_b.task_id`; `status.read_a.status == status.read_b.status`; `case.verdict=pass`; `metrics.concurrency_case_total>=1`; 不创建额外 `TaskRecord`；不出现状态回退 |
| `trc-concurrent-result-shared-truth` | `result.read_a.task_id == result.read_b.task_id`; `result.read_a.envelope_ref == result.read_b.envelope_ref`; `case.verdict=pass`; `metrics.concurrency_case_total>=1`; 不创建影子结果；终态不被重复改写 |
| `trc-post-accept-reacquire-reject` | `policy.retry.max_attempts=1`; `policy.concurrency.scope=global`; `policy.concurrency.on_limit=reject`; `metrics.concurrency_case_total>=1`; `ExecutionControlEvent.details.reacquire_rejected=true`; `forbidden_mutations` 包含“上一 attempt 终态 \`error.code\`/\`error.category\` 不变” |

#### `failure_log_metrics`

| case_id | 必须断言字段和值 |
| --- | --- |
| `flm-success-observable` | `result.status=succeeded`; `metrics.success_total>=1`; 结构化日志包含 `task_id/entrypoint/stage/result.status` |
| `flm-business-failure-observable` | `error.category in {invalid_input, unsupported, platform}`; `metrics.failure_total>=1`; 结构化日志包含 `task_id/entrypoint/stage/error.category` |
| `flm-contract-failure-fail-closed` | `error.category=runtime_contract`; `gate.verdict=fail`; 不输出 success envelope |
| `flm-timeout-observable` | `error.category=platform`; `error.details.control_code=execution_timeout`; `metrics.timeout_total>=1` |
| `flm-retry-exhausted-observable` | `policy.retry.max_attempts=1`; `retry.exhausted=true`; `metrics.retry_attempt_total>=1` |
| `flm-store-unavailable-fail-closed` | `error.code=task_record_unavailable`; `error.category=runtime_contract`; `gate.verdict=fail` |
| `flm-http-invalid-input-observable` | `request_ref != ""`; `entrypoint=http`; `stage=pre_admission`; `result.status=failed`; `error.category=invalid_input`; `metrics.failure_total>=1`; 不创建 `TaskRecord` |
| `flm-cli-invalid-input-observable` | `request_ref != ""`; `entrypoint=cli`; `stage=pre_admission`; `result.status=failed`; `error.category=invalid_input`; `metrics.failure_total>=1`; 不创建 `TaskRecord` |
| `flm-same-path-violation-observable` | `same_path.verdict=fail`; `metrics.same_path_case_failure_total>=1`; overall gate verdict=fail |

#### `http_submit_status_result`

| case_id | 必须断言字段和值 |
| --- | --- |
| `http-submit-status-result-shared-truth` | `submit.request.capability=content_detail_by_url`; `metrics.submit_total>=1`; `status.task_id == result.task_id`; `status.task_record_ref == result.task_record_ref`; `result.envelope_ref != ""`; 只存在一条共享 `TaskRecord`；`result` 读取同一 shared envelope |

#### `cli_api_same_path`

| case_id | 必须断言字段和值 |
| --- | --- |
| `same-path-success-shared-truth` | `cli.task_record_ref == http.task_record_ref`; `cli.envelope_ref == http.envelope_ref`; `same_path.verdict=pass`; `metrics.same_path_case_total>=1`; 同一状态迁移 |
| `same-path-pre-admission-invalid-input` | `cli.request_ref != ""`; `http.request_ref != ""`; `cli.stage == http.stage == pre_admission`; `cli.result.status == http.result.status == failed`; `cli.error.category == http.error.category == invalid_input`; `cli.error.code == http.error.code`; `same_path.verdict=pass`; `metrics.same_path_case_total>=1`; 两侧都不创建 `TaskRecord` |
| `same-path-durable-record-unavailable` | `cli.error.code == http.error.code == task_record_unavailable`; `cli.error.category == http.error.category == runtime_contract`; `same_path.verdict=pass`; `metrics.same_path_case_total>=1`; 两侧都 fail-closed |
| `same-path-terminal-result-read` | `cli.result.task_id == http.result.task_id`; `cli.result.envelope_ref == http.result.envelope_ref`; `same_path.verdict=pass`; `metrics.same_path_case_total>=1`; 共享同一组 `runtime_result_refs` |
