# CHORE-0447 v1.6 batch / dataset runtime 执行计划

## 关联信息

- item_key：`CHORE-0447-v1-6-batch-dataset-runtime`
- Issue：`#447`
- item_type：`CHORE`
- release：`v1.6.0`
- sprint：`2026-S25`
- Parent Phase：`#444`
- Parent FR：`#445`
- 关联 spec：`docs/specs/FR-0445-batch-dataset-core-contract/spec.md`
- 关联 decision：
- 关联 PR：
- 状态：`active`

## 目标

- 交付 Core batch/dataset runtime carriers、validators、reference dataset sink 与 batch item execution wrapper。
- 复用现有 read-side item result envelope，不重新定义 creator/comment/media/content 私有字段。
- 将 `batch_execution` admitted 为 `FR-0445` 的 stable runtime taxonomy slice。

## 范围

- 本次纳入：
  - `syvert/batch_dataset.py`
  - `syvert/operation_taxonomy.py`
  - `tests/__init__.py`（仅启用根目录默认 unittest discovery 进入治理测试包）
  - `tests/runtime/test_batch_dataset.py`
  - `tests/runtime/test_operation_taxonomy.py`
  - 本执行计划
- 本次不纳入：
  - TaskRecord/result query/compatibility consumer migration（`#448`）
  - sanitized evidence artifact 与 replay matrix（`#449`）
  - release closeout、annotated tag、GitHub Release 或 published truth carrier（`#450`）
  - scheduler、write-side、content library、BI、UI、provider selector/fallback/marketplace
  - raw payload files、source names、本地路径、storage handles、private account/media/creator fields

## 当前停点

- Phase `#444`：open。
- FR `#445`：open，已显式绑定 `v1.6.0 / 2026-S25`。
- Work Item `#446`：completed，spec PR `#451` 已合入。
- Work Item `#447`：active runtime carrier。
- Workspace key：`issue-447-445-v1-6-0-batch-dataset-runtime`
- Branch：`issue-447-445-v1-6-0-batch-dataset-runtime`
- Baseline：`0486d7755b0d3fe6b50a5d513d6aba136ab2ad7a`

## 已实现合同

- `BatchRequest` / `BatchTargetItem` / `BatchResumeToken` / `BatchItemOutcome` / `BatchResultEnvelope` public carriers。
- `DatasetRecord` 与 JSON-safe in-memory `ReferenceDatasetSink`。
- `execute_batch_request` wrapper 逐 item 调用现有 `execute_task` path。
- 支持 `complete`、`partial_success`、`all_failed`、`resumable` batch result status。
- 支持 `succeeded`、`failed`、`duplicate_skipped` item status。
- duplicate `dedup_key` 采用 first-wins，重复 item neutral skip 且不写第二份 dataset record。
- dataset sink write failure 映射为 failed item，保留 read-side success envelope 供审计。
- resume token 只表达 runtime position，不表达 scheduler、priority、workflow、provider fallback 或 marketplace。
- batch 本身不要求真实账号；item operation 需要资源时继续经过 existing resource governance。
- guardian follow-up：resume 会校验 prior outcomes 与 target-set 前缀、dedup state 和 dataset sink readback；绑定 `dataset_sink_ref` 但缺 sink 时 fail-closed；`source_trace` 只允许 sanitized Core 字段；search/list request cursor 当前 fail-closed，避免静默丢弃。
- guardian rerun follow-up：timeout/cancel 类已 dispatch item failure 在存在 suffix 时返回 `resumable`；fresh run 拒绝携带 prior outcomes；batch audit trace 补齐 `started_at`、`item_trace_refs`、sanitized `evidence_refs` 与 stop reason 校验。
- guardian rerun2 follow-up：resume prefix 拒绝未知 outcome status 和非重复 item 的 `duplicate_skipped`；所有 BatchItemOutcome source_trace 先经 sanitized validator；`creator_profile_by_id` request cursor 当前 fail-closed，避免静默丢弃。
- guardian rerun3 follow-up：prior `BatchItemOutcome` 进入 resume 前强制 canonical validation；`DatasetRecord.normalized_payload` 递归拒绝 raw/source/storage/private 字段；sanitized ref validator 拒绝真实 URL、bucket/storage URL 和本地路径。
- guardian rerun4 follow-up：`BatchItemOutcome` canonical validation 强制 status/payload invariant，`succeeded` 必须有 result envelope，`failed` 必须有 error envelope 且不得引用 dataset record，`duplicate_skipped` 不得携带 result/error/dataset record。
- guardian rerun5 follow-up：sanitized ref validator 拒绝所有以 `/` 开头的本地绝对路径，同时保留 `raw://` 等 sanitized alias。
- guardian rerun6 follow-up：`source_trace.provider_path` 专用 validator 同样拒绝以 `/` 开头的本地绝对路径。
- guardian rerun7 follow-up：`source_trace.provider_path` 复用 storage/private token denylist，`normalized_payload` 私有字段检测改为大小写不敏感，同时 public payload 仍允许 sanitized `raw_payload_ref`。
- guardian rerun8 follow-up：`execute_batch_request` 在返回前验证新产生的 `BatchItemOutcome`，将 unsafe adapter failure payload 转换成 sanitized `unsafe_item_outcome` failure，避免直接暴露 unsafe error details。

## 已验证项

- `python3 -m unittest tests.runtime.test_batch_dataset`
  - 结果：通过，35 tests。
- `python3 -m unittest tests.runtime.test_batch_dataset tests.runtime.test_operation_taxonomy tests.runtime.test_operation_taxonomy_consumers tests.runtime.test_task_record`
  - 结果：通过，89 tests。
- `python3 -m unittest discover`
  - 结果：通过，527 tests。
- `python3 -m unittest tests.runtime.test_batch_dataset tests.runtime.test_operation_taxonomy tests.runtime.test_operation_taxonomy_consumers tests.runtime.test_task_record tests.governance.test_open_pr`
  - 结果：通过，171 tests。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/version_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `git diff --check`
  - 结果：通过。
- `python3 /private/tmp/pr_guardian_danger_452_clone.py review 452 --post-review --json-output /private/tmp/syvert-pr-452-guardian.json`
  - 结果：首轮 `REQUEST_CHANGES`，阻断项为 resume state、dataset sink 缺失、source_trace enforcement、search/list cursor 静默丢弃；已在当前 follow-up 修复并补测试。
- `python3 /private/tmp/pr_guardian_danger_452_clone.py review 452 --post-review --json-output /private/tmp/syvert-pr-452-guardian-rerun.json`
  - 结果：第二轮 `REQUEST_CHANGES`，阻断项为 timeout/cancel resumable boundary、fresh run prior outcome contamination、BatchAuditTrace 最小字段与 sanitized refs；已在当前 follow-up 修复并补测试。
- `python3 /private/tmp/pr_guardian_danger_452_clone.py review 452 --post-review --json-output /private/tmp/syvert-pr-452-guardian-rerun2.json`
  - 结果：第三轮 `REQUEST_CHANGES`，阻断项为 resume outcome status、BatchItemOutcome source_trace sanitation、creator profile cursor 静默丢弃；已在当前 follow-up 修复并补测试。
- `python3 /private/tmp/pr_guardian_danger_452_clone.py review 452 --post-review --json-output /private/tmp/syvert-pr-452-guardian-rerun3.json`
  - 结果：第四轮 `REQUEST_CHANGES`，阻断项为 prior outcome unsafe carrier smuggling、normalized_payload 泄漏、raw storage URL refs；已在当前 follow-up 修复并补测试。
- `python3 /private/tmp/pr_guardian_danger_452_clone.py review 452 --post-review --json-output /private/tmp/syvert-pr-452-guardian-rerun4.json`
  - 结果：第五轮 `REQUEST_CHANGES`，阻断项为 failed prior outcomes 缺失 error envelope 或伪造 dataset_record_ref；已在当前 follow-up 修复并补测试。
- `python3 /private/tmp/pr_guardian_danger_452_clone.py review 452 --post-review --json-output /private/tmp/syvert-pr-452-guardian-rerun5.json`
  - 结果：第六轮 `REQUEST_CHANGES`，阻断项为 sanitized ref 仍允许 `/home`、`/etc` 等本地绝对路径；已在当前 follow-up 修复并补测试。
- `python3 /private/tmp/pr_guardian_danger_452_clone.py review 452 --post-review --json-output /private/tmp/syvert-pr-452-guardian-rerun6.json`
  - 结果：第七轮 `REQUEST_CHANGES`，阻断项为 `source_trace.provider_path` 仍允许本地绝对路径；已在当前 follow-up 修复并补测试。
- `python3 /private/tmp/pr_guardian_danger_452_clone.py review 452 --post-review --json-output /private/tmp/syvert-pr-452-guardian-rerun7.json`
  - 结果：第八轮 `REQUEST_CHANGES`，阻断项为 `source_trace.provider_path` 仍允许 storage/private routing aliases，以及 `normalized_payload` 私有字段大小写绕过；已在当前 follow-up 修复并补测试。
- `python3 /private/tmp/pr_guardian_danger_452_clone.py review 452 --post-review --json-output /private/tmp/syvert-pr-452-guardian-rerun8.json`
  - 结果：第九轮 `REQUEST_CHANGES`，阻断项为 failed item error envelope 返回前未做 public-carrier leakage validation；已在当前 follow-up 修复并补测试。

## 待验证项

- PR guardian review rerun
- `python3 scripts/pr_guardian.py merge-if-safe`

## 未决风险

- `#448` 仍需证明 TaskRecord/result query/compatibility consumers 消费 batch/dataset public carriers。
- `#449` 仍需提供 replayable sanitized evidence matrix。
- 若 runtime carrier 暴露 read-side envelope defect，必须新建 remediation Work Item，不能混入本 PR。

## 回滚方式

- 使用独立 revert PR 撤销本 Work Item 的 runtime/test/doc 增量。
- 保留 `#445` formal spec 与 `#447` GitHub truth，由后续 Work Item 重新交付 runtime carrier。

## 最近一次 checkpoint 对应的 head SHA

- Initial branch checkpoint：`0486d7755b0d3fe6b50a5d513d6aba136ab2ad7a`
