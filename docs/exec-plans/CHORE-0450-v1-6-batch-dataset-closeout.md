# CHORE-0450 v1.6 batch / dataset closeout

## 关联信息

- item_key：`CHORE-0450-v1-6-batch-dataset-closeout`
- Issue：`#450`
- item_type：`CHORE`
- release：`v1.6.0`
- sprint：`2026-S25`
- Parent Phase：`#444`
- Parent FR：`#445`
- 关联 spec：`docs/specs/FR-0445-batch-dataset-core-contract/`
- 关联 artifact：`docs/exec-plans/artifacts/CHORE-0450-v1-6-batch-dataset-closeout-evidence.md`
- 关联 PR：pending
- 状态：`active`

## 目标

- Work Item：`#450`
- Parent FR：`#445`
- Scope：消费 `#446/#447/#448/#449` 的 merged truth、验证结果与 sanitized evidence，完成 `#445` closeout、Phase `#444` closeout 判断、`v1.6.0` 发布锚点（tag + GitHub Release）与 release/sprint 索引回写。
- Out of scope：新增 runtime 行为、consumer 迁移、evidence fixture、scheduler、UI、BI、写侧流程、provider selector/fallback/marketplace 或真实 provider 数据。

## 改动记录

- 基于 `origin/main@357024e4389bb2f75b578f202c09bdb20222280e` 更新 `v1.6.0` release index、`2026-S25` sprint index 和 `#450` closeout evidence。
- 统一记录 `#446-#449` 的 PR、merge commit、Work Item 状态与 validation inputs。
- 明确 release decision：`v1.6.0` 发布目标为 evidence PR `#454` 的 merge commit `357024e4389bb2f75b578f202c09bdb20222280e`，closeout PR 只回写 reconciliation truth，不改变 release target。
- 在发布完成后回写 annotated tag object、tag target、GitHub Release URL、published timestamp。

## 验证记录

- `git rev-parse v1.6.0^{tag}`
- `git rev-parse v1.6.0^{}`
- `gh release view v1.6.0 --json tagName,url,publishedAt,targetCommitish,isDraft,isPrerelease`
- 结果：tag object、tag target、GitHub Release URL、published timestamp 与 `#454` release target 对齐。
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/version_guard.py --mode ci`
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
- `python3 scripts/spec_guard.py --mode ci --all`
- 结果：通过。
- `python3 -m unittest tests.runtime.test_batch_dataset_evidence tests.runtime.test_batch_dataset tests.runtime.test_task_record tests.runtime.test_cli_http_same_path tests.runtime.test_operation_taxonomy_consumers`
- 结果：通过，180 tests。
- `python3 -m unittest discover`
- 结果：通过，527 tests。
- `git diff --check`
- 结果：通过。
- Closeout 文档泄漏扫描
- 结果：仅命中禁止/不需要的 sanitized boundary 描述，未发现真实账号、原始 payload、provider source name、本地路径、storage handle 或私有 account/media/creator 值。

## Release decision

- Decision：publish `v1.6.0` as the Batch / Dataset Core Contract release slice for `#445`.
- Release target：`357024e4389bb2f75b578f202c09bdb20222280e` (`#454` evidence merge commit on `main`).
- Rationale：`#446/#447/#448/#449` are merged, sanitized evidence is repo-backed, and no remaining release gate requires real provider data, credentials, scheduler behavior, write-side behavior, UI, BI, or private provider fields.
- Closeout PR：records repository truth and GitHub reconciliation only; it is not the release target.

## 未决风险

- `#450` PR 必须通过 checks、guardian 与 merge gate 后，`#444/#445/#450` 才可关闭。
- 本 release 只证明 sanitized fake/reference Batch / Dataset Core Contract，不证明真实 provider production 行为。
- Scheduler、write-side、provider selector/fallback/marketplace、UI、BI 和上层 content library 仍是后续独立范围。

## 回滚方式

- closeout truth 错误：使用独立 docs PR 与 GitHub issue/release metadata 修正，不回滚 `#446-#449` 已合入实现。
- tag / GitHub Release metadata 错误：按 version-management 规则修正 GitHub Release notes；不得重写已发布 tag，除非独立批准。
- 若发布后复现 runtime/contract drift：创建独立 remediation/revert Work Item，按回滚门槛处理，不在 closeout PR 混入代码修复。

## 最近一次 checkpoint 对应的 head SHA

- Release target checkpoint：`357024e4389bb2f75b578f202c09bdb20222280e`
