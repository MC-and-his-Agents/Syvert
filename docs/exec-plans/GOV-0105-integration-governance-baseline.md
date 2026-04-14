# GOV-0105 执行计划

## 关联信息

- item_key：`GOV-0105-integration-governance-baseline`
- Issue：`#105`
- item_type：`GOV`
- release：`governance-baseline`
- sprint：`integration-governance`
- 关联 spec：无（治理联动事项）
- 关联 decision：`docs/decisions/ADR-GOV-0105-integration-governance-baseline.md`
- 关联 PR：`#115`
- active 收口事项：`GOV-0105-integration-governance-baseline`

## 目标

- 把 `open_pr / pr_guardian / merge_pr / governance_status` 全部接到仓库内唯一的 canonical integration contract 上，让 issue / PR / reviewer / guardian / merge gate 真正消费同一份真相源。
- reviewer packet 在本批只消费 canonical issue/PR contract 对比与本地工件；`integration_ref` 的 live-state 证据改由 `governance_status` 状态面展示，并继续只在 merge gate 阶段作为阻断条件强制执行。
- 保持 `Syvert` 继续作为本地执行真相源，并为后续 PR-C / PR-D 的 carrier alignment 与 evidence 收口提供稳定的运行时治理链路。

## 范围

- 已合并的 PR-A 只纳入：`scripts/policy/integration_contract.json`、`scripts/integration_contract.py`、`scripts/common.py` 中与 integration contract 直接相关的最小辅助逻辑、`tests/governance/test_integration_contract.py`，以及当前 bootstrap contract 文档。
- 当前 PR-B 纳入：`open_pr / pr_guardian / merge_pr / governance_status` 的共享消费链路、对应治理测试，以及保证该链路在独立 worktree 上可执行的最小兼容修正。
- 后续 PR-C 再纳入：`WORKFLOW.md`、`code_review.md`、PR template、issue forms 的 carrier alignment。
- 后续 PR-D 再纳入：ADR / exec-plan 的最终叙事收口与 platform evidence。
- 本次不纳入：自动 bot / 自动同步系统、新的产品仓库、跨仓实现代码、对现有 `Phase / FR / sprint` 语义做统一改造。

## 当前停点

- `#107` 保持 Draft 并冻结，不再继续修 findings 或提交 guardian；它只作为拆分母体和审查历史容器保留。
- `PR-A Contract Kernel` 已合并到 `main`，当前仓库内 canonical integration contract 已成为后续替代 PR 的 bootstrap truth source。
- 当前真正需要收口的是 `PR-B Consumer Wiring`，即让 `open_pr / pr_guardian / merge_pr / governance_status` 只消费 shared contract，并把 reviewer packet、status 面、merge-time recheck、guardian cache 身份模型与 issue-side canonical integration 证据统一到同一链路。
- 当前 PR-B 已以 Draft PR `#115` 打开；本地门禁与 GitHub checks 已通过，当前停点转为 reviewer / guardian 对 `#115` latest head 的收口。

## 下一步动作

- 在同一 head 上等待 reviewer 与 guardian 收口，再执行 `#115` 的受控合并。
- `#115` 合并后，再按同一 `Issue #105` 串行推进 PR-C、PR-D。

## 当前 checkpoint 推进的 release 目标

- 让 canonical integration contract 从“内核已存在”推进到“所有核心消费者已接线”，使 reviewer / guardian / merge gate 的运行时决策不再各自维护第二套 integration 语义。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：替代链路的第二批 `PR-B Consumer Wiring`。
- 阻塞：在 PR-B 合并前，`open_pr / pr_guardian / merge_pr / governance_status` 仍未完全共享同一份 canonical integration contract；PR-C / PR-D 的 carrier 和 evidence 收口缺少稳定的运行时治理链路可依赖。

## 已验证项

- 已执行：`python3 -m unittest tests.governance.test_integration_contract`
- 已执行：`python3 -m unittest tests.governance.test_open_pr tests.governance.test_pr_guardian tests.governance.test_governance_status`
- 已执行：`python3 scripts/workflow_guard.py --mode pre-commit`
- 已执行：`python3 scripts/governance_gate.py --mode ci --base-sha origin/main --head-sha HEAD --head-ref issue-105-integration-governance-baseline-consumer-wiring`

## 未决风险

- 若 PR-B 继续夹带 carrier alignment 或 evidence 叙事，scope 会再次膨胀，guardian finding 也会重新跨层连锁。
- `main` 在替代链路推进期间继续前进；每一批 PR 在进入 guardian 和 merge 前都必须基于最新 `origin/main` 重跑本地门禁。
- 由于当前 issue 已声明 canonical integration 字段，后续所有替代 PR 都必须完整对齐 contract，不允许退回 legacy 路径。
- 当前 PR-B 仍处于 PR-C 之前的阶段，因此 PR 模板尚未成为唯一 carrier；在 PR-C 合并前，`open_pr` 需要继续保证缺失模板 section 时也能生成 canonical `integration_check` 区块。
- reviewer 阶段不能把外部 integration project 的 live-state 漂移升级为审查阻断；相关 live-state 只允许出现在 `governance_status` 诊断面与 merge gate 入口。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 consumer wiring 接线与对应最小兼容修正，让 `#105` 回退到“只有 contract kernel、尚未完成消费者统一接线”的状态。

## 最近一次 checkpoint 对应的 head SHA

- 最近一次完成 PR-B consumer wiring 代码收口并同步验证证据的 checkpoint：`3165cb69ae5eacae33e59d2833c7e0f671b92008`
- 当前 PR 审查态以 `#115` 的 latest head 为准；本轮最小验证集与 guardian 必须绑定同一 latest head，不得继续复用旧 checkpoint 的验证摘要。
