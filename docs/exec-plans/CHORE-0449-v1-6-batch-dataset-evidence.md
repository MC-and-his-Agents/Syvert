# CHORE-0449 v1.6 batch / dataset evidence 执行计划

## 关联信息

- item_key：`CHORE-0449-v1-6-batch-dataset-evidence`
- Issue：`#449`
- item_type：`CHORE`
- release：`v1.6.0`
- sprint：`2026-S25`
- Parent Phase：`#444`
- Parent FR：`#445`
- 关联 spec：`docs/specs/FR-0445-batch-dataset-core-contract/spec.md`
- 关联 artifact：`docs/exec-plans/artifacts/CHORE-0449-v1-6-batch-dataset-evidence.md`
- 关联 PR：
- 状态：`active`

## 目标

- 交付 `FR-0445` 的 sanitized fake/reference evidence 与 replay matrix。
- 覆盖 partial success / partial failure、all failed、resume、timeout resumable、duplicate target、dataset replay、resource boundary 与 public carrier leakage prevention。
- 只使用 sanitized fake/reference carriers；不引入真实账号、原始 payload 文件、私有 provider 数据、source names、本地路径、storage handles、私有 media/account/creator 字段、scheduler、UI、BI 或写侧流程。

## 范围

- 本次纳入：
  - `docs/exec-plans/artifacts/CHORE-0449-v1-6-batch-dataset-evidence.md` 的 embedded JSON evidence snapshot。
  - `tests/runtime/test_batch_dataset_evidence.py` 的 replay / sanitizer / leakage prevention 测试。
  - 本执行计划。
- 本次不纳入：
  - `syvert/batch_dataset.py` runtime carrier 语义改写。
  - TaskRecord/result query/compatibility consumer migration。
  - release closeout、annotated tag、GitHub Release 或 published truth carrier。
  - scheduler、write-side、content library、BI、UI、provider selector/fallback/marketplace。
  - raw payload files、真实账号凭据、provider source names、本地路径、storage handles、私有 media/account/creator values。

## 当前停点

- Phase `#444`：open。
- FR `#445`：open，显式绑定 `v1.6.0 / 2026-S25`。
- Work Item `#446`：spec PR `#451` 已合入。
- Work Item `#447`：runtime carrier PR `#452` 已合入，merge commit `926a378dbec0c93fe2766eff8f4e3277083797c5`。
- Work Item `#448`：consumer PR `#453` 已合入，merge commit `23cbce712138e5edaba8e199cba419ff31dd0956`。
- Work Item `#449`：active evidence。
- Workspace key：`issue-449-445-v1-6-0-batch-dataset-evidence`
- Branch：`issue-449-445-v1-6-0-batch-dataset-evidence`
- Worktree：formal issue-scoped worktree for `#449`
- Baseline：`23cbce712138e5edaba8e199cba419ff31dd0956`

## 已实现证据

- 新增 replayable evidence artifact，嵌入由测试重建的 structured JSON snapshot。
- replay matrix 使用 `execute_batch_request`、`ReferenceDatasetSink` 与 sanitized fake/reference adapter。
- 覆盖场景：
  - `partial_success_failure`：一个成功 item 与一个 `permission_denied` failed item；只写成功 dataset record。
  - `all_failed`：所有 item failed；不写 dataset records。
  - `resume`：中断只返回已处理前缀，恢复后返回完整 canonical outcomes，并复用 dedup/write state。
  - `timeout_resumable`：已 dispatch timeout item 作为 failed outcome，suffix 由 resume token 继续。
  - `duplicate_target`：相同 `dedup_key` first-wins，duplicate item 为 `duplicate_skipped`，不重复写 record。
  - `dataset_replay`：`read_by_dataset`、`read_by_batch` 与 `audit_replay` 返回 JSON-safe public record/replay summary。
  - `resource_boundary`：batch admission 不要求真实账号；item path 继续通过 existing resource governance fail-closed。
  - `public_carrier_leakage_prevention`：dataset/result/resume public carrier 对 raw inline、path/ref、storage、private entity field、routing marker 等泄漏 fail-closed。
- Snapshot sanitization 记录：
  - no raw payload files / embedded raw payload。
  - no source names / local paths / storage handles。
  - no private account/media/creator fields。
  - no provider selector / marketplace semantics。
  - no real account credentials required。

## 已验证项

- Initial focused evidence replay:
  - `python3 -m unittest tests.runtime.test_batch_dataset_evidence.BatchDatasetEvidenceTests.test_evidence_snapshot_covers_fr_0445_matrix tests.runtime.test_batch_dataset_evidence.BatchDatasetEvidenceTests.test_evidence_snapshot_has_no_private_or_raw_fragments tests.runtime.test_batch_dataset_evidence.BatchDatasetEvidenceTests.test_public_carrier_leakage_matrix_fails_closed`
  - 结果：通过，3 tests。
- Evidence artifact replay:
  - `python3 -m unittest tests.runtime.test_batch_dataset_evidence`
  - 结果：通过，4 tests。
- Evidence / replay / consumer matrix:
  - `python3 -m unittest tests.runtime.test_batch_dataset_evidence tests.runtime.test_batch_dataset tests.runtime.test_task_record tests.runtime.test_cli_http_same_path tests.runtime.test_operation_taxonomy_consumers`
  - 结果：通过，180 tests。
- Full unittest discovery:
  - `python3 -m unittest discover`
  - 结果：通过，527 tests。
- Guards:
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

## 未决风险

- 当前 evidence 只证明 repo-backed sanitized fake/reference matrix；不证明真实 provider 行为。
- `#450` 仍需消费本 evidence、完成 release/sprint/FR/Phase truth reconciliation 和 explicit `v1.6.0` release decision。

## 回滚方式

- 使用独立 revert PR 撤销本 Work Item 的 evidence artifact、replay tests 与执行计划增量。
- 保留 #445 / #447 / #448 truth，由后续 Work Item 重新补证据。

## 最近一次 checkpoint 对应的 head SHA

- Evidence replay checkpoint：pending local commit。
