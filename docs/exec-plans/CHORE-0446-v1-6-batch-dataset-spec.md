# CHORE-0446 v1.6 batch / dataset spec 执行计划

## 关联信息

- item_key：`CHORE-0446-v1-6-batch-dataset-spec`
- Issue：`#446`
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

- 完成 `#445` 的 Batch 0 与 Batch 1。
- 交付 sanitized fixture/error/evidence inventory、formal spec suite、`v1.6.0` release planning index 与 `2026-S25` sprint update。
- 不交付 runtime carrier、consumer migration、evidence implementation、release closeout、tag、GitHub Release 或 raw payload files。

## 范围

- 本次纳入：
  - `docs/exec-plans/artifacts/CHORE-0446-v1-6-batch-dataset-fixture-inventory.md`
  - `docs/exec-plans/CHORE-0446-v1-6-batch-dataset-spec.md`
  - `docs/specs/FR-0445-batch-dataset-core-contract/`
  - `docs/releases/v1.6.0.md`
  - `docs/sprints/2026-S25.md`
- 本次不纳入：
  - `syvert/**` runtime implementation
  - `tests/**` implementation or fixture payloads
  - `#447/#448/#449/#450` execution
  - release closeout, annotated tag, GitHub Release, published truth carrier
  - scheduler, write-side, content library, BI, UI, provider selector/fallback/marketplace
  - raw fixture payload files and any source/path/storage/private-field mapping

## 当前停点

- Phase `#444`：open。
- FR `#445`：open，已显式绑定 `v1.6.0 / 2026-S25`。
- Work Item `#446`：open，唯一进入 execution workspace 的 `#445` spec slice。
- Workspace key：`issue-446-445-v1-6-0-batch-dataset-spec`
- Branch：`issue-446-445-v1-6-0-batch-dataset-spec`
- Baseline：`6ed2c132d9f5ca4bd26e8c8834979a935a064321`

## 下一步动作

- 完成 spec/docs 增量。
- 运行 spec/docs/workflow/version/governance gates、diff check 与 leakage scan。
- 创建 spec PR，并在 PR review / guardian 后收口 `#446`。

## 当前 checkpoint 推进的 release 目标

- 为 `v1.6.0` 明确 Batch / Dataset Core Contract 的 planning truth。
- `v1.6.0` 只绑定 `#445` release slice，不由 `#382` 或 roadmap title 推导。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`#445` formal spec carrier。
- 阻塞：
  - `#447` runtime carrier 必须等待本 Work Item 合入和 spec review 通过。
  - 若发现 read-side contract defect，必须创建 remediation Work Item。

## 已验证项

- `#444/#445/#446-#450` GitHub admission 已完成。
- 独立 worktree 与 issue-scoped branch 已创建。
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
- 脱敏扫描
  - 结果：新增文档只包含 forbidden terms 的禁止/拒绝语境，未包含 raw payload files、source names、本地路径、storage handles 或 private account/media/creator values。

## 未决风险

- planning release index 被误写成 published truth。
- runtime 后续绕过 existing Core task/resource path。
- dataset sink 扩张为 content library 或 storage lifecycle。

## 回滚方式

- 使用独立 revert PR 撤销本 Work Item 新增的 spec/docs/artifact 增量。
- 保留 `#444/#445/#446` GitHub truth，由 FR 重新拆分下一步 Work Item。

## 最近一次 checkpoint 对应的 head SHA

- Initial branch checkpoint：`6ed2c132d9f5ca4bd26e8c8834979a935a064321`
