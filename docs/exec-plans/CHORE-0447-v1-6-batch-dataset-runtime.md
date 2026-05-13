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
  - `scripts/common.py`（仅修复 issue-scoped worktree repo locator，确保默认 discovery / PR scripts 不漂移到其他 repo）
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
- issue-scoped worktree 名称（如 `syvert-447-runtime`）解析为 canonical Syvert repo，避免本地验证和 PR scripts 读取其他 repo 语义。

## 已验证项

- `python3 -m unittest tests.runtime.test_batch_dataset`
  - 结果：通过。
- `python3 -m unittest tests.runtime.test_batch_dataset tests.runtime.test_operation_taxonomy tests.runtime.test_operation_taxonomy_consumers tests.runtime.test_task_record`
  - 结果：通过。
- `python3 -m unittest discover`
  - 结果：通过，527 tests。
- `python3 -m unittest tests.runtime.test_batch_dataset tests.runtime.test_operation_taxonomy tests.runtime.test_operation_taxonomy_consumers tests.runtime.test_task_record tests.governance.test_open_pr`
  - 结果：通过，165 tests。
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

## 待验证项

- PR guardian review
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
