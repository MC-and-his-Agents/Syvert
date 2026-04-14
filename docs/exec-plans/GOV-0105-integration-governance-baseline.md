# GOV-0105 执行计划

## 关联信息

- item_key：`GOV-0105-integration-governance-baseline`
- Issue：`#105`
- item_type：`GOV`
- release：`governance-baseline`
- sprint：`integration-governance`
- 关联 spec：无（治理联动事项）
- 关联 decision：`docs/decisions/ADR-GOV-0105-integration-governance-baseline.md`
- 关联 PR：`#107`
- active 收口事项：`GOV-0105-integration-governance-baseline`

## 目标

- 为 `Syvert × WebEnvoy` 的跨仓协同补齐最小治理插槽，使当前仓库继续作为本地执行真相源，但在触及共享契约、跨仓依赖或联合验收时有明确的 integration 联动入口。

## 范围

- 本次纳入：canonical integration contract、其消费者载体（`WORKFLOW.md`、`code_review.md`、`.github/PULL_REQUEST_TEMPLATE.md`、`.github/ISSUE_TEMPLATE/**`、`scripts/open_pr.py`、`scripts/pr_guardian.py`、`scripts/merge_pr.py`）、review packet、当前 exec-plan、`ADR-GOV-0105` 与外部 rollout evidence 入口。
- 本次不纳入：自动 bot / 自动同步系统、新的产品仓库、跨仓实现代码、对现有 `Phase / FR / sprint` 语义做统一改造。

## 当前停点

- 当前回合的中心目标已收缩为“仓库内 canonical integration contract + 消费方接线”，不再把 owner project、repo project fields、labels 与 issue 回填写成 repo 内已完成事实。
- repo 内改造需要同时收口三件事：单一机器可读 contract、`open_pr/pr_guardian/merge_pr` 的共享消费链路、以及 reviewer 可见的 integration review packet。
- 外部 GitHub 平台 rollout 改为独立 evidence 包，当前 exec-plan 只保留 repo 内 contract、review packet 与受控 merge gate 的执行停点。
- `integration_ref` 对应 integration item 的当前状态、依赖与联合验收结果属于 merge gate 的运行时输入，不属于 evidence 文档中的“已完成事实”。
- 存量事项继续走受控兼容：issue lookup failure fail-closed；issue 存在但未声明 canonical integration 字段时允许 legacy 路径；一旦 issue 已声明 canonical integration 字段，PR 就必须完整对齐。

## 下一步动作

- 完成 canonical integration contract、共享模块、review packet 与消费者载体之间的统一接线。
- 用 focused governance tests 锁定 contract 枚举、组合约束、legacy 策略、`integration_ref` 归一与 doc/template 一致性。
- 推送最新 contract 收口 head，等待 checks 全绿，并在同一 head 上重新运行 guardian。
- 若 guardian 给出 `APPROVE + safe_to_merge=true`，再 rebase 到最新 `origin/main`，重跑 checks 与 guardian，然后通过 `python3 scripts/merge_pr.py 107 --delete-branch --confirm-integration-recheck` 受控合并。

## 当前 checkpoint 推进的 release 目标

- 为当前治理基线建立可审查、可恢复、可合并的单一执行上下文，使 integration 联动规则不再只停留在 project 与 issue 字段层，而是进入受控 PR 流程。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`Syvert × WebEnvoy` integration governance baseline 的 Syvert 侧治理收口项。
- 阻塞：当前事项自身属于 `integration_touchpoint=active`、`external_dependency=both`、`merge_gate=integration_check_required` 的治理基线收口项；除本仓库 checks 与 guardian 外，merge 前还必须把 `integration_ref` 对应状态复核收口到 PR 元数据与受控 merge gate。

## 已验证项

- `python3` 成功解析 `.github/ISSUE_TEMPLATE/*.yml`
- 当前事项已把 external rollout 的验证入口独立到 `docs/governance-rollouts/GOV-0105-platform-evidence.md`
- 已执行：`python3 -m unittest tests.governance.test_integration_contract`
- 已执行：`python3 -m unittest tests.governance.test_open_pr tests.governance.test_pr_guardian tests.governance.test_governance_status`
- 已执行：`python3 scripts/workflow_guard.py --mode pre-commit`
- 已执行：`python3 scripts/governance_gate.py --mode ci --base-sha origin/main --head-sha HEAD --head-ref issue-105-integration-governance-baseline`

## 未决风险

- `Syvert/main` 在当前审查回合内继续前进；任何基于旧 head 的 guardian 结论都不能直接用于最终合并，必须在最后一次 rebase 后重跑 checks 与 guardian。
- merge 前仍需再次核对 `integration_ref` 与 owner 级 integration project 的当前状态，但这属于 merge gate 运行时读取范围，不由 evidence 文档或 exec-plan 直接宣称已完成。
- 当前 `integration_ref` 对应 item 的 `Joint Acceptance` 若仍为 `pending` / `failed`，则 `#107` 不应进入受控合并，除非先完成外部状态收口或更正 canonical issue 元数据。
- 若后续仍有未回填 canonical integration 字段的存量 issue / PR，需要在进入下一轮执行前补齐，避免长期依赖 legacy 兼容路径。
- 若后续继续扩张 integration 枚举或 gate 语义，需要再走独立治理回合，不应直接在当前 PR 上扩 scope。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销当前治理文档、issue forms 与 exec-plan 增量，并同步回退对应 project / issue 联动口径。

## 最近一次 checkpoint 对应的 head SHA

- 当前受审 head：以 PR `#107` 的 latest head 为准。
- 当前 checkpoint 只记录 repo 内 contract 收口停点；guardian verdict 与最终 merge gate 继续绑定 latest head，而不在 exec-plan 中手写逐轮审查日志。
- 最近一次完成的 repo 内 checkpoint：`9c0fd9a7d76d79f45bd9eb9594f09e214a04650c`
