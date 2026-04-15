# GOV-0105 执行计划

## 关联信息

- item_key：`GOV-0105-integration-governance-baseline`
- Issue：`#105`
- item_type：`GOV`
- release：`governance-baseline`
- sprint：`integration-governance`
- 关联 spec：无（治理联动事项）
- 关联 decision：`docs/decisions/ADR-GOV-0105-integration-governance-baseline.md`
- 关联 PR：`#116`
- active 收口事项：`GOV-0105-integration-governance-baseline`

## 目标

- 把 `WORKFLOW.md`、`code_review.md`、PR template 与 issue forms 收口到仓库内唯一的 canonical integration contract 上，让 carrier 侧不再维护第二套 integration 规则。
- 明确 `Phase` 不是 canonical integration metadata carrier，并把 integration metadata 的合法落点限制在 FR / Work Item / governance issue 与 PR `integration_check`。
- 保持 `Syvert` 继续作为本地执行真相源，并在已完成 PR-B consumer wiring 的前提上，为后续 PR-D evidence / rollout 收口提供稳定的 carrier 基线。

## 范围

- 已合并的 PR-A 只纳入：`scripts/policy/integration_contract.json`、`scripts/integration_contract.py`、`scripts/common.py` 中与 integration contract 直接相关的最小辅助逻辑、`tests/governance/test_integration_contract.py`，以及当前 bootstrap contract 文档。
- 已合并的 PR-B 纳入：`open_pr / pr_guardian / merge_pr / governance_status` 的共享消费链路、对应治理测试，以及保证该链路在独立 worktree 上可执行的最小兼容修正。
- 当前 PR-C 纳入：`WORKFLOW.md`、`code_review.md`、PR template、issue forms 的 carrier alignment，以及保证这些 carrier 与 canonical contract 顺序 / 角色一致的最小一致性测试。
- 后续 PR-D 再纳入：platform evidence 与本事项最终叙事收口。
- 本次不纳入：自动 bot / 自动同步系统、新的产品仓库、跨仓实现代码、对现有 `Phase / FR / sprint` 语义做统一改造。

## 当前停点

- `#107` 保持 Draft 并冻结，不再继续修 findings 或提交 guardian；它只作为拆分母体和审查历史容器保留。
- `PR-A Contract Kernel` 已合并到 `main`，当前仓库内 canonical integration contract 已成为后续替代 PR 的 bootstrap truth source。
- `PR-B Consumer Wiring` 已合并到 `main`，当前仓库内运行时治理链路已统一到 canonical integration contract。
- 当前真正需要收口的是 `PR-C Carrier Alignment`，即让 `WORKFLOW.md`、`code_review.md`、PR template 与 issue forms 只暴露 canonical carrier，不再维护第二套 integration 规则，并明确 `Phase` carve-out。
- 当前 PR-C 已以 Draft PR `#116` 打开；本地门禁与 GitHub checks 已通过，当前停点转为 reviewer / guardian 对 `#116` latest head 的收口。

## 下一步动作

- 在同一 head 上等待 reviewer 与 guardian 收口，再执行 `#116` 的受控合并。
- `#116` 合并后，再按同一 `Issue #105` 推进 PR-D 并在最后关闭 `#107`。

## 当前 checkpoint 推进的 release 目标

- 让 canonical integration contract 从“运行时治理链路已统一”推进到“carrier 已完成对齐”，使 workflow / review / template / issue forms 不再各自维护第二套 integration 语义。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：替代链路的第三批 `PR-C Carrier Alignment`。
- 阻塞：在 PR-C 合并前，workflow / review / template / issue forms 仍未完全对齐 canonical carrier；`Phase` 仍缺少明确的 integration metadata carve-out，PR-D 也还无法在稳定 carrier 基线之上完成最终 evidence 收口。

## 已验证项

- 已执行：`python3 -m unittest tests.governance.test_integration_carriers`
- 已执行：`python3 scripts/workflow_guard.py --mode pre-commit`
- 已执行：`python3 scripts/docs_guard.py --mode ci`

## 未决风险

- 若 PR-C 再继续夹带 evidence rollout 或运行时治理逻辑，scope 会再次膨胀，guardian finding 也会重新跨层连锁。
- `main` 在替代链路推进期间继续前进；每一批 PR 在进入 guardian 和 merge 前都必须基于最新 `origin/main` 重跑本地门禁。
- 由于当前 issue 已声明 canonical integration 字段，后续所有替代 PR 都必须完整对齐 contract，不允许退回 legacy 路径。
- 当前 PR-C 仍在 carrier 收口阶段，因此 reviewer / guardian 应聚焦 carrier 是否与 canonical contract 一致，而不是重新解释运行时 integration 语义。
- reviewer 阶段不能把外部 integration project 的 live-state 漂移升级为审查阻断；相关 live-state 只允许出现在运行时治理链路与 merge gate 入口。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 carrier alignment 与对应一致性测试，让 `#105` 回退到“运行时治理链路已统一，但 carrier 尚未完全对齐”的状态。

## 最近一次 checkpoint 对应的 head SHA

- 最近一次完成 PR-C carrier alignment 收口、补强 carrier 与运行时解析器兼容性测试并同步验证证据的 checkpoint：`71030f6802d8db6336ff7228530943aae58d9891`
- 当前 PR 审查态与本轮最小验证集均绑定 `#116` 的 latest head `71030f6802d8db6336ff7228530943aae58d9891`；guardian 与 merge gate 不得继续复用旧 checkpoint 的验证摘要。
