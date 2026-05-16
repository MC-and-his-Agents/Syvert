# CHORE-0448 v1.6 batch / dataset consumers 执行计划

## 关联信息

- item_key：`CHORE-0448-v1-6-batch-dataset-consumers`
- Issue：`#448`
- item_type：`CHORE`
- release：`v1.6.0`
- sprint：`2026-S25`
- Parent Phase：`#444`
- Parent FR：`#445`
- 关联 spec：`docs/specs/FR-0445-batch-dataset-core-contract/spec.md`
- 关联 PR：`#453`
- 状态：`active`

## 目标

- 迁移 TaskRecord、result query、runtime admission 与 compatibility consumers，使 #447 交付的 batch/dataset public carrier 可被公共消费者读取。
- 保持 direct `execute_task(batch_execution)` fail-closed，不重新打开 #447 runtime carrier 或 shared runtime admission 语义。
- 保持 read-side result envelope 不被 batch consumer 重写。

## 范围

- 本次纳入：
  - `syvert/task_record.py` 的 batch TaskRecord request/result projection 校验。
  - `tests/runtime/test_task_record.py` 的 batch TaskRecord 编解码兼容回归。
  - `tests/runtime/test_cli_http_same_path.py` 的 CLI query / HTTP status / HTTP result 读取同一 batch public carrier 回归。
  - `tests/runtime/test_operation_taxonomy_consumers.py` 的 batch target item admission consumer 与 compatibility fail-closed 回归。
  - 本执行计划。
- 本次不纳入：
  - `syvert/batch_dataset.py` runtime carrier 语义改写。
  - `syvert/runtime.py` shared `TaskRequest` / `CoreTaskRequest` admission 扩容。
  - scheduler、write-side admission、provider selector/fallback/marketplace、content library、BI、UI。
  - #449 evidence artifact 与 #450 release closeout。

## 当前停点

- Phase `#444`：open。
- FR `#445`：open，显式绑定 `v1.6.0 / 2026-S25`。
- Work Item `#447`：runtime carrier PR `#452` 已合入 main，merge commit `926a378dbec0c93fe2766eff8f4e3277083797c5`。
- Work Item `#448`：active consumers migration。
- Workspace key：`issue-448-445-v1-6-0-batch-dataset-consumers`
- Branch：`issue-448-445-v1-6-0-batch-dataset-consumers`
- Worktree：`/Users/mc/code/worktrees/syvert/issue-448-445-v1-6-0-batch-dataset-consumers`
- Baseline：`926a378dbec0c93fe2766eff8f4e3277083797c5`
- PR：`#453` / `https://github.com/MC-and-his-Agents/Syvert/pull/453`
- PR metadata follow-up 不刷新 checkpoint head；live review head 以 PR `headRefOid`、GitHub checks、guardian state 与 merge gate 为准。

## 已实现合同

- TaskRecord request snapshot 允许 `batch_execution / operation_batch / batch` 作为 consumer-side record projection，但不加入 runtime `execute_task` admission mapping。
- TaskRecord terminal envelope 支持读取 batch public result carrier，并校验：
  - `batch_id` 与 request snapshot 绑定；
  - `result_status` 与 item outcome aggregation 一致；
  - sink-bound success 必须携带 `dataset_record_ref`；
  - sinkless item 不得伪造 `dataset_record_ref`；
  - `resume_token.next_item_index` 只指向已处理 item 前缀；
  - batch terminal 顶层不得携带 `raw` / `normalized` payload。
- Guardian follow-up：TaskRecord batch projection 重建 canonical `BatchResultEnvelope` 并调用 #447 public carrier validator，避免 failed item 伪造 `dataset_record_ref`、nested `result_envelope` target drift、source/audit/private carrier 泄漏等宽松读取；同时对原始 batch envelope 顶层、`resume_token` 与 `item_outcomes` 执行严格字段集校验，避免 canonical projection 忽略的额外私有字段被原样回读。
- Merge-gate follow-up：TaskRecord 接受 `batch_result_envelope_to_dict` 序列化后的 cursor-sensitive comment batch public carrier；该 public carrier 按 #447 约定不暴露 `request_cursor_context`，consumer 只从公开 comment result 中校验 schema/target/source/continuation 并派生本地验证用 thread ref，再交回 canonical batch validator 校验 aggregation、dataset boundary 与 audit。
- CLI query、HTTP status 与 HTTP result 可读取同一 batch TaskRecord public carrier，且不会暴露 `request_cursor_context`。
- Batch target item consumer 只消费稳定 read-side runtime slices；compatibility consumers 遇到 dataset normalized payload 形状时 fail-closed。

## 已验证项

- Focused TaskRecord/result-query/compat tests：
  - `python3 -m unittest tests.runtime.test_task_record.TaskRecordCodecTests.test_round_trips_batch_execution_record tests.runtime.test_task_record.TaskRecordCodecTests.test_rejects_batch_execution_result_status_drift`
  - 结果：通过，2 tests。
  - `python3 -m unittest tests.runtime.test_cli_http_same_path.CliHttpSamePathTests.test_batch_task_record_query_and_http_result_share_public_carrier`
  - 结果：通过，1 test。
  - `python3 -m unittest tests.runtime.test_operation_taxonomy_consumers.OperationTaxonomyConsumerMigrationTests.test_batch_target_items_consume_stable_read_side_runtime_slices tests.runtime.test_operation_taxonomy_consumers.OperationTaxonomyConsumerMigrationTests.test_batch_target_item_rejects_provider_compatibility_as_operation tests.runtime.test_operation_taxonomy_consumers.OperationTaxonomyConsumerMigrationTests.test_compatibility_consumers_do_not_accept_dataset_normalized_payload`
  - 结果：通过，3 tests。
- Consumer/runtime compatibility suite：
  - `python3 -m unittest tests.runtime.test_task_record tests.runtime.test_cli_http_same_path tests.runtime.test_operation_taxonomy_consumers tests.runtime.test_batch_dataset tests.runtime.test_runtime tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，379 tests。
- Guardian follow-up validation：
  - `python3 -m unittest tests.runtime.test_task_record.TaskRecordCodecTests.test_round_trips_batch_execution_record tests.runtime.test_task_record.TaskRecordCodecTests.test_rejects_failed_batch_item_with_dataset_record_ref tests.runtime.test_task_record.TaskRecordCodecTests.test_rejects_batch_item_result_envelope_target_drift tests.runtime.test_task_record.TaskRecordCodecTests.test_rejects_batch_item_result_envelope_private_source_trace tests.runtime.test_task_record.TaskRecordCodecTests.test_rejects_batch_execution_top_level_raw_payload`
  - 结果：通过，5 tests。
  - `python3 -m unittest tests.runtime.test_cli_http_same_path.CliHttpSamePathTests.test_batch_task_record_query_and_http_result_share_public_carrier`
  - 结果：通过，1 test。
  - `python3 -m unittest tests.runtime.test_task_record tests.runtime.test_cli_http_same_path tests.runtime.test_operation_taxonomy_consumers tests.runtime.test_batch_dataset tests.runtime.test_runtime tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，382 tests。
- Guardian rerun follow-up validation：
  - `python3 -m unittest tests.runtime.test_task_record.TaskRecordCodecTests.test_round_trips_batch_execution_record tests.runtime.test_task_record.TaskRecordCodecTests.test_rejects_batch_execution_top_level_extra_private_field tests.runtime.test_task_record.TaskRecordCodecTests.test_rejects_batch_execution_request_snapshot_unsafe_batch_id tests.runtime.test_task_record.TaskRecordCodecTests.test_rejects_batch_item_extra_private_field tests.runtime.test_task_record.TaskRecordCodecTests.test_rejects_failed_batch_item_with_dataset_record_ref tests.runtime.test_task_record.TaskRecordCodecTests.test_rejects_batch_item_result_envelope_target_drift tests.runtime.test_task_record.TaskRecordCodecTests.test_rejects_batch_item_result_envelope_private_source_trace`
  - 结果：通过，7 tests。
  - `python3 -m unittest tests.runtime.test_cli_http_same_path.CliHttpSamePathTests.test_batch_task_record_query_and_http_result_share_public_carrier`
  - 结果：通过，1 test。
  - `python3 -m unittest tests.runtime.test_task_record tests.runtime.test_cli_http_same_path tests.runtime.test_operation_taxonomy_consumers tests.runtime.test_batch_dataset tests.runtime.test_runtime tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，385 tests。
- Merge-gate follow-up validation：
  - `python3 -m unittest tests.runtime.test_task_record.TaskRecordCodecTests.test_round_trips_serialized_cursor_sensitive_batch_result`
  - 结果：通过，1 test。
  - `python3 -m unittest tests.runtime.test_task_record`
  - 结果：通过，45 tests。
  - `python3 -m unittest tests.runtime.test_task_record tests.runtime.test_cli_http_same_path tests.runtime.test_operation_taxonomy_consumers tests.runtime.test_batch_dataset tests.runtime.test_runtime tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，386 tests。
- Full unittest discovery：
  - `python3 -m unittest discover`
  - 结果：通过，527 tests。
- Guards：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
  - `python3 scripts/docs_guard.py`
  - 结果：通过。
  - `python3 scripts/workflow_guard.py`
  - 结果：通过。
  - `python3 scripts/version_guard.py`
  - 结果：通过。
  - `python3 scripts/governance_gate.py --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
  - `git diff --check`
  - 结果：通过。

## 未决风险

- 当前实现只迁移消费者读取 public batch carrier，不提供新的 batch/dataset CLI/HTTP submit endpoint。
- TaskRecord consumer 复用 canonical batch/dataset carrier validation；cursor-sensitive comment public carrier 的私有 request cursor omission 仅在 consumer 读回中按公开字段受控恢复验证上下文。若发现 read-side carrier 缺陷，仍须单独开修复项。
- #449 仍需补 sanitized evidence 与 replayable proof。
- `python3 .loom/bin/loom_check.py .` 已运行但失败，失败项为 Loom full-runtime/adoption scaffold 缺失（如 `tools/loom_init.py`、`skills/*`、`packages/loom-installer`、adoption docs），不属于 #448 consumer migration 范围；Syvert repo-native guards 与 GitHub checks 已通过。

## 回滚方式

- 使用独立 revert PR 撤销本 Work Item 的 TaskRecord consumer 与测试增量。
- 保留 #445 / #448 truth，由后续 Work Item 重新迁移 consumer。

## 最近一次 checkpoint 对应的 head SHA

- Consumer migration checkpoint：`2df4d3cca1dd8b4e64d01c931750af7342da56e8`
- Strict batch public carrier validation checkpoint：`15140180888cf2820dcb4e5ff8fd6fe5428ec897`
- Cursor-sensitive public carrier compatibility checkpoint：`1e632913489b2aa1eaf00f7bb3f39417341bf24f`
- Live PR head 以 GitHub `headRefOid` 为准；metadata-only checkpoint 只更新本执行计划记录。
