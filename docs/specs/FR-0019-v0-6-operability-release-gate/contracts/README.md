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

## Matrix case contract（字段级）

每个 `OperabilityMatrixCase.expected_result` 必须使用字段级断言，不允许抽象同义词：

- 必填结构：
  - `fields[]`：`path` + `operator` + `value`
  - `side_effects[]`
  - `forbidden_mutations[]`
- `fields[]` 至少包含一个精确值断言（例如 `error.category=platform`），只写“一致”“可重试”“同路径”视为无效 case。

### Mandatory cases

| case_id | 必须断言字段和值 |
| --- | --- |
| `trc-timeout-platform-control-code` | `policy.timeout_ms=30000`; `policy.retry.max_attempts=1`; `policy.retry.backoff_ms=0`; `error.category=platform`; `error.details.control_code=execution_timeout` |
| `trc-pre-accept-concurrency-reject` | `policy.concurrency.scope=global`; `policy.concurrency.max_in_flight=1`; `policy.concurrency.on_limit=reject`; `error.category=invalid_input`; `TaskRecord` 不存在 |
| `trc-post-accept-reacquire-reject` | `ExecutionControlEvent.details.reacquire_rejected=true`; `forbidden_mutations` 包含“上一 attempt 终态 `error.code`/`error.category` 不变” |
| `flm-retryable-predicate-idempotency-gate` | `retry.predicate.match` 只允许 `execution_timeout` 或 `platform_retryable`; `idempotency_safety_gate=pass`；日志字段含 `task_id/entrypoint/stage/error.category`；指标含 retry attempt 计数 |
| `http-submit-status-result-shared-truth` | `submit.request.capability=content_detail_by_url`; `status.task_id == result.task_id`; 同一 `TaskRecord` |
| `same-path-cli-http-success-and-failure` | 成功态：`cli.envelope.schema == http.envelope.schema`；失败态：`cli.error.category == http.error.category`；同一 `TaskRecord.task_id` |
