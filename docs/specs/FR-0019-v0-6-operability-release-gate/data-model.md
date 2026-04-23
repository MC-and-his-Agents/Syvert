# FR-0019 v0.6 operability release gate 数据模型

## 实体清单

- 实体：`OperabilityGateResult`
- 用途：表达一次 `v0.6.0` operability release gate 的总体结论、矩阵覆盖、证据引用与 fail-closed 判定。

- 实体：`OperabilityMatrixCase`
- 用途：表达一个必选或扩展 gate case 的验证对象、入口组合、前置条件、预期结果、实际证据与 gate 影响。

- 实体：`SamePathProof`
- 用途：表达 CLI 与 HTTP API 在等价请求或等价失败条件下是否回指同一 Core / task-record / store / envelope 语义。

- 实体：`OperabilityEvidenceRef`
- 用途：表达可复验的本地证据引用，例如测试 case id、结构化 gate output、日志片段索引或 metrics 聚合输出。

## 关键字段

- `OperabilityGateResult.release`
  - 约束：固定为 `v0.6.0`；缺失或不匹配时 gate fail。
- `OperabilityGateResult.fr_item_key`
  - 约束：固定为 `FR-0019-v0-6-operability-release-gate`。
- `OperabilityGateResult.gate_id`
  - 约束：稳定字符串，用于区分一次 gate 执行或一个 gate 定义版本。
- `OperabilityGateResult.baseline_gate_ref`
  - 约束：必须引用 `FR-0007` 基础 gate 的可信结论；缺失时 verdict 必须为 `fail`。
- `OperabilityGateResult.matrix_version`
  - 约束：稳定字符串；用于说明当前 case 集合版本。
- `OperabilityGateResult.cases`
  - 约束：非空数组，必须覆盖四类必选维度：`timeout_retry_concurrency`、`failure_log_metrics`、`http_submit_status_result`、`cli_api_same_path`。
- `OperabilityGateResult.summary`
  - 约束：至少包含 pass / fail case 数、失败 case id 列表与失败维度。
- `OperabilityGateResult.evidence_refs`
  - 约束：非空、去重、稳定，且可从仓内命令输出或 CI artifact 复验。
- `OperabilityGateResult.verdict`
  - 约束：只允许 `pass` 或 `fail`；任何未知、缺失或部分通过状态都必须映射为 `fail`。
- `OperabilityGateResult.normative_dependencies`
  - 约束：必须包含 `FR-0007`、`FR-0016`、`FR-0017`、`FR-0018`；缺失任一依赖时 verdict 必须为 `fail`。
- `OperabilityGateResult.policy_snapshot`
  - 约束：必须固定包含：
    - `timeout_ms=30000`
    - `retry.max_attempts=1`
    - `retry.backoff_ms=0`
    - `concurrency.scope=global`
    - `concurrency.max_in_flight=1`
    - `concurrency.on_limit=reject`
  - 任一字段缺失或值漂移都必须使 gate fail。

- `OperabilityMatrixCase.case_id`
  - 约束：稳定、唯一、可在 gate result 与测试输出中交叉引用。
- `OperabilityMatrixCase.dimension`
  - 约束：只允许 `timeout_retry_concurrency`、`failure_log_metrics`、`http_submit_status_result`、`cli_api_same_path`，后续扩展必须不削弱四类必选维度。
- `OperabilityMatrixCase.entrypoints`
  - 约束：声明涉及 `core`、`cli`、`http` 中的一个或多个入口。
- `OperabilityMatrixCase.preconditions`
  - 约束：列出请求、store、错误分类、并发条件或 baseline gate 前提。
- `OperabilityMatrixCase.expected_result`
  - 约束：必须可判定，且说明成功 / 失败 envelope、状态迁移、日志或 metrics 的预期。
  - 子字段：
    - `expected_result.fields`：数组，每项都包含 `path`、`operator`、`value`，用于字段级断言。
    - `expected_result.side_effects`：数组，显式断言 `TaskRecord` / `ExecutionControlEvent` / metrics / logs 的副作用。
    - `expected_result.forbidden_mutations`：数组，显式断言禁止改写的字段（例如上一 attempt 的终态 code/category）。
  - case 只写抽象同义词（例如“应一致”“应可重试”）而无字段路径和值时必须 fail。
- `OperabilityMatrixCase.actual_result_ref`
  - 约束：必须引用可复验证据；缺失时 case fail。
- `OperabilityMatrixCase.gate_impact`
  - 约束：必选 case 失败必须使 overall verdict fail。
- `OperabilityMatrixCase.capability`
  - 约束：当前只允许 `content_detail_by_url`；出现其他 capability 时 case 必须 fail。

- `SamePathProof.cli_entrypoint`
  - 约束：指向 CLI `run` 或 `query` 语义，不固定具体命令实现。
- `SamePathProof.http_entrypoint`
  - 约束：指向 HTTP `submit`、`status` 或 `result` 语义，不固定具体 URL path。
- `SamePathProof.shared_request_ref`
  - 约束：必须能回映到共享请求模型或等价失败条件。
- `SamePathProof.task_record_ref`
  - 约束：成功进入 durable 生命周期后必须回指同一类 `TaskRecord` truth。
- `SamePathProof.envelope_ref`
  - 约束：必须回指 shared success / failed envelope；不得是入口私有 schema。
- `SamePathProof.verdict`
  - 约束：只允许 `pass` 或 `fail`。

## 最小必选矩阵（字段级期望）

| case_id | dimension | capability | 前置条件摘要 | expected_result.fields（必须命中） | expected_result.side_effects（必须命中） |
| --- | --- | --- | --- | --- | --- |
| `trc-timeout-platform-control-code` | `timeout_retry_concurrency` | `content_detail_by_url` | 任务被控制面超时终止 | `error.category=platform`; `error.details.control_code=execution_timeout`; `policy.timeout_ms=30000`; `policy.retry.max_attempts=1`; `policy.retry.backoff_ms=0` | 写入 `ExecutionControlEvent.details.control_code=execution_timeout`; `TaskRecord.status=failed` |
| `trc-pre-accept-concurrency-reject` | `timeout_retry_concurrency` | `content_detail_by_url` | 进入 admission 前命中全局并发上限 | `error.category=invalid_input`; `policy.concurrency.scope=global`; `policy.concurrency.max_in_flight=1`; `policy.concurrency.on_limit=reject` | `TaskRecord` 未创建 |
| `trc-post-accept-reacquire-reject` | `timeout_retry_concurrency` | `content_detail_by_url` | 首次 attempt 完成后，retry reacquire 被拒绝 | `policy.retry.max_attempts=1`; `policy.concurrency.scope=global`; `policy.concurrency.on_limit=reject` | 新增 `ExecutionControlEvent.details.reacquire_rejected=true`；保留上一 attempt 的终态 `error.code` / `error.category` |
| `flm-retryable-predicate-idempotency-gate` | `failure_log_metrics` | `content_detail_by_url` | 同时覆盖 `execution_timeout` 与 `error.category=platform + details.retryable=true` | `retry.predicate.match in {execution_timeout, platform_retryable}`; `idempotency_safety_gate=pass` | `metrics.retry_attempt_total>=1`; 结构化日志包含 `task_id`、`entrypoint`、`stage`、`error.category` |
| `flm-non-retryable-fail-closed` | `failure_log_metrics` | `content_detail_by_url` | 非 retryable failure | `idempotency_safety_gate` 未放行；`retry.attempts=0` 或不递增 | `metrics.failure_total>=1`; 不生成新的 retry attempt 事件 |
| `http-submit-status-result-shared-truth` | `http_submit_status_result` | `content_detail_by_url` | HTTP submit 后查询 status/result | `submit.request.capability=content_detail_by_url`; `status.task_id == result.task_id` | 只存在一条共享 `TaskRecord`；读取同一 shared envelope |
| `same-path-cli-http-success-and-failure` | `cli_api_same_path` | `content_detail_by_url` | CLI run/query 与 HTTP submit/status/result 等价请求 | `cli.envelope.schema == http.envelope.schema`; `cli.error.category == http.error.category`（失败态） | CLI 与 HTTP 都回指同一 `TaskRecord.task_id` 与同一状态迁移 |

## 生命周期

- 创建：
  - 后续 `#234` 在执行 gate matrix 时创建 `OperabilityMatrixCase` 结果与 `OperabilityGateResult` 聚合。
  - 每个 case 在执行前必须有稳定 `case_id`、`dimension`、前置条件与预期结果。
- 更新：
  - case 执行后只能补充实际证据、结论与失败原因，不得事后改写 case 预期来适配结果。
  - overall verdict 由 case verdict、baseline gate ref 与 evidence refs 计算得出，不得人工覆盖为通过。
- 失效/归档：
  - 若矩阵版本、release、case 集合或 baseline gate 发生变化，旧 gate result 只能作为历史证据，不得继续作为当前 `v0.6.0` 通过结论。
  - 缺失证据、证据不可复验或与当前 revision 不匹配的 gate result 必须失效并 fail-closed。
