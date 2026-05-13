# FR-0445 数据模型

## BatchRequest

- 用途：表达一个 Core batch execution request。
- 最小字段：`batch_id`、`target_set`、`resume_token`（可选）、`dataset_sink_ref`（可选）、`audit_context`。
- 约束：`target_set` 必须是非空 `BatchTargetItem` 数组；`resume_token` 必须绑定同一 `batch_id` 与 target set hash；`dataset_sink_ref` 是 opaque sink alias，不得包含 storage handle、本地路径、bucket URL 或产品数据库 schema。

## BatchTargetItem

- 用途：表达 batch 内单个可执行 read-side item。
- 最小字段：`item_id`、`operation`、`target_type`、`target_ref`、`dedup_key`、`request_cursor`（可选）。
- 约束：`operation` 只能是已稳定 read-side operation；`request_cursor` 只能承载该 operation 已定义的 public cursor/policy carrier；`dedup_key` 必须是稳定 public key。

## BatchItemOutcome

- 用途：表达 batch 内每个 item 的结果。
- 最小字段：`item_id`、`operation`、`target_ref`、`outcome_status`、`result_envelope`（可选）、`error_envelope`（可选）、`dataset_record_ref`（可选）、`audit`。
- 约束：`outcome_status` 至少支持 `succeeded`、`failed`、`duplicate_skipped`；`duplicate_skipped` 不得携带 success result envelope，不得写 dataset record；batch result 聚合时将其视为 neutral terminal outcome，不单独制造 `partial_success`。

## BatchResultEnvelope

- 用途：表达整个 batch 的 terminal result。
- 最小字段：`batch_id`、`operation`、`result_status`、`item_outcomes`、`resume_token`（可选）、`dataset_sink_ref`（可选）、`audit_trace`。
- 约束：`operation` 固定为 `batch_execution`；`result_status` 至少支持 `complete`、`partial_success`、`all_failed`、`resumable`。

## BatchResumeToken

- 用途：表达可恢复的 runtime position。
- 最小字段：`resume_token`、`batch_id`、`target_set_hash`、`next_item_index`、`issued_at`。
- 约束：只恢复 runtime position；不得表达 scheduler trigger、business priority、workflow branch、provider fallback、selector 或 marketplace。

## BatchAuditTrace

- 用途：表达 batch-level 与 item-level audit carrier。
- 最小字段：`batch_id`、`started_at`、`finished_at`（可选）、`item_trace_refs`、`evidence_refs`。
- 约束：`evidence_refs` 必须是 sanitized alias；不得记录 raw payload inline、source names、本地路径、storage handles、private account/media/creator fields。

## DatasetRecord

- 用途：表达 batch/dataset sink 中的最小沉淀记录。
- 最小字段：`dataset_record_id`、`dataset_id`、`source_operation`、`target_ref`、`raw_payload_ref`、`normalized_payload`、`evidence_ref`、`dedup_key`、`batch_id`、`batch_item_id`、`recorded_at`。
- 约束：`normalized_payload` 必须是 JSON-safe public payload；`raw_payload_ref` 只能是 reference 或 null，不得内联 raw payload；`dedup_key` first-wins。

## DatasetSink

- 用途：表达最小 sink contract。
- 最小能力：`write(record)`、`read_by_dataset(dataset_id)`、`read_by_batch(batch_id)`、`audit_replay(dataset_id)`。
- readback 语义：`read_by_dataset(dataset_id)` 返回该 dataset 的 JSON-safe records；`read_by_batch(batch_id)` 返回该 batch 写入的 JSON-safe records；两者都不得返回 storage handle、本地路径、source name 或 raw payload inline。
- 约束：首版 reference sink 可为 in-memory / JSON-safe carrier；不得绑定产品数据库 schema、storage handle、content library lifecycle 或 BI model。
