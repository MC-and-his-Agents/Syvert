# GOV-0105 执行计划

## 关联信息

- item_key：`GOV-0105-integration-governance-baseline`
- Issue：`#105`
- item_type：`GOV`
- release：`governance-baseline`
- sprint：`integration-governance`
- 关联 spec：无（治理联动事项）
- 关联 decision：`docs/decisions/ADR-GOV-0105-integration-governance-baseline.md`
- 关联 PR：待创建（`PR-A: Contract Kernel`）
- active 收口事项：`GOV-0105-integration-governance-baseline`

## 目标

- 先把仓库内唯一的 canonical integration contract 落到 `main`，为后续消费者接线、载体对齐和 evidence 收口建立稳定真相源。
- 保持 `Syvert` 继续作为本地执行真相源，同时为后续 `Syvert × WebEnvoy` integration 协同提供可执行的 contract 基线。

## 范围

- 当前 PR-A 只纳入：`scripts/policy/integration_contract.json`、`scripts/integration_contract.py`、`scripts/common.py` 中与 integration contract 直接相关的最小辅助逻辑、`tests/governance/test_integration_contract.py`，以及当前 bootstrap contract 文档。
- 后续 PR-B 再纳入：`open_pr / pr_guardian / merge_pr / governance_status` 的共享消费链路。
- 后续 PR-C 再纳入：`WORKFLOW.md`、`code_review.md`、PR template、issue forms 的 carrier alignment。
- 后续 PR-D 再纳入：ADR / exec-plan 的最终叙事收口与 platform evidence。
- 本次不纳入：自动 bot / 自动同步系统、新的产品仓库、跨仓实现代码、对现有 `Phase / FR / sprint` 语义做统一改造。

## 当前停点

- `#107` 保持 Draft 并冻结，不再继续修 findings 或提交 guardian；它只作为拆分母体和审查历史容器保留。
- 当前真正需要先落地的是 `PR-A Contract Kernel`，否则 `#105` 在 `main` 上没有 active bootstrap contract，后续替代 PR 无法通过受控入口。
- 当前 PR-A 必须只声明 contract kernel 与最小 bootstrap contract，不提前宣称消费者、载体和 evidence 已完成。

## 下一步动作

- 从 `#107` 母体裁出 contract kernel 与最小 bootstrap contract，形成独立分支和 Draft PR。
- 运行 `tests.governance.test_integration_contract`、`workflow_guard --mode pre-commit` 与 `governance_gate --mode ci`，确保第一批能独立成立。
- PR-A 合并后，再按同一 `Issue #105` 串行推进 PR-B、PR-C、PR-D。

## 当前 checkpoint 推进的 release 目标

- 为当前治理基线先建立可审查、可恢复、可复用的 canonical integration contract 内核，使后续联动规则有唯一真相源可依赖。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：替代链路的第一批 `PR-A Contract Kernel`。
- 阻塞：在 PR-A 合并前，`main` 上不存在 `#105` 的 active bootstrap contract，后续替代 PR 无法通过 `open_pr` 的事项上下文校验。

## 已验证项

- 待本轮 contract kernel 裁剪完成后补记。

## 未决风险

- 若 PR-A 继续夹带消费者、carrier 或 evidence 叙事，scope 会再次膨胀，guardian finding 也会重新跨层连锁。
- `main` 在替代链路推进期间继续前进；每一批 PR 在进入 guardian 和 merge 前都必须基于最新 `origin/main` 重跑本地门禁。
- 由于当前 issue 已声明 canonical integration 字段，后续所有替代 PR 都必须完整对齐 contract，不允许退回 legacy 路径。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 contract kernel 与当前 bootstrap contract 文档，让 `#105` 回到未建立 repo 内真相源的状态。

## 最近一次 checkpoint 对应的 head SHA

- 待 PR-A 首次 checkpoint 生成后补记当前 head SHA。
