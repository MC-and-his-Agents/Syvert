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
