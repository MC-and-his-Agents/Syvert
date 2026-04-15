# GOV-0105 执行计划

## 关联信息

- item_key：`GOV-0105-integration-governance-baseline`
- Issue：`#105`
- item_type：`GOV`
- release：`governance-baseline`
- sprint：`integration-governance`
- 关联 spec：无（治理联动事项）
- 关联 decision：`docs/decisions/ADR-GOV-0105-integration-governance-baseline.md`
- 关联 PR：当前 `PR-D Evidence / Rollout` docs closeout round（创建后以 GitHub PR 元数据为准）
- active 收口事项：`GOV-0105-integration-governance-baseline`

## 目标

- 把 GOV-0105 的 repo 内治理终态收口到“一份 canonical integration contract + 一份独立 rollout evidence”。
- 让 ADR 只保留 repo 内 single-source contract 决策，让 active `exec-plan` 只保留当前 docs closeout round 的停点、风险、验证与下一步。
- 把 owner 级 GitHub Project、labels、backfill 与 replacement chain 事实集中记录到独立 evidence 文档，不再写回 contract 主体。

## 范围

- 当前 PR-D 只纳入：`docs/decisions/ADR-GOV-0105-integration-governance-baseline.md`、本 `exec-plan` 与 `docs/governance-rollouts/GOV-0105-platform-evidence.md`。
- 本次负责：清理 ADR / `exec-plan` 中仍残留的批次叙事与外部 rollout 事实，并为外部 GitHub rollout 建立独立 evidence 入口。
- 本次不纳入：`WORKFLOW.md`、`code_review.md`、PR template、issue forms、`open_pr / pr_guardian / merge_pr / governance_status`、共享 contract 内核、外部系统自动同步。

## 当前停点

- `PR-A/#114`、`PR-B/#115`、`PR-C/#116` 已合并到 `main`，仓库内 canonical integration contract、运行时治理链路与 carrier 已经完成收口。
- 当前剩余 repo 内动作是 `PR-D Evidence / Rollout`：把外部 GitHub rollout 事实移出 ADR / active `exec-plan` 主体，并单独落盘为 rollout evidence。
- `#107` 仍保持冻结的 superseded closeout 候选状态，等待替代链完全收口后补 replacement chain 并关闭。

## 下一步动作

- 完成 ADR、`exec-plan` 与 rollout evidence 文档改写。
- 运行 `python3 scripts/workflow_guard.py --mode pre-commit` 与 `python3 scripts/docs_guard.py --mode ci`。
- 通过 `open_pr.py` 开 Draft PR，收口 checks、guardian 与 merge gate 后合并。
- PR-D 合并后，在 `#107` 补 replacement chain comment 并关闭为 superseded；必要时在 `#105` 补最终收口说明。

## 当前 checkpoint 推进的 release 目标

- 让 GOV-0105 从“carrier 已对齐”推进到“repo 内 contract 主体与 repo 外 rollout evidence 已彻底分离”的最终治理终态。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：替代链路的第四批 `PR-D Evidence / Rollout` docs closeout round。
- 阻塞：在 docs closeout 完成前，ADR / active `exec-plan` 仍带有批次性叙事；`#107` 也还不能按完整 replacement chain 关闭为 superseded。

## 已验证项

- 待本轮 docs 变更完成后刷新。

## 未决风险

- 若 ADR / `exec-plan` 再次回写外部 GitHub rollout 事实，repo 内 contract 主体会重新失焦。
- rollout evidence 文档若不在合并前刷新到最新 GitHub 状态，`#107` 的 replacement chain 与 `#105` 的外部 evidence 可能与 live state 漂移。
- 当前分支使用自定义 GOV-0105 split worktree；在 PR-D 合并后必须按分支是否仍存在分别清理 worktree、state 与 branch。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本批 docs-only closeout，让 ADR / `exec-plan` 与 rollout evidence 恢复到 PR-C 合并后的状态；该回滚不影响 runtime tooling 或 carrier 行为。

## 最近一次 checkpoint 对应的 head SHA

- 当前 docs closeout round 的内容 checkpoint 将在本批文档收口与最小门禁验证完成后刷新到最新 head。
- 本轮 guardian 与 merge gate 必须绑定当前 docs closeout PR 的 latest head，不得继续复用 `#116` 收口阶段的审查态摘要。
