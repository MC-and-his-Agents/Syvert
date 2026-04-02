# GOV-0025 执行计划

## 关联信息

- item_key：`GOV-0025-review-template-lean-context`
- Issue：`#25`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S14`
- 关联 spec：无（治理脚本事项）
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 关联 PR：待补充
- active 收口事项：`GOV-0025-review-template-lean-context`

## 目标

- 让 `.github/PULL_REQUEST_TEMPLATE.md` 只保留 reviewer / guardian 真正消费的高价值输入。
- 让 `open_pr` 自动冻结最小 Issue 摘要，避免继续依赖冗余模板正文或 reviewer 二次读取远端 Issue。
- 让 guardian prompt 与新的 lean review context 模型保持一致，不削弱既有 merge gate、安全性与 head 绑定逻辑。

## 范围

- 本次纳入：`.github/PULL_REQUEST_TEMPLATE.md`、`scripts/open_pr.py`、`scripts/pr_guardian.py`、必要的治理测试、本事项 `exec-plan`
- 本次不纳入：重写整套 review 系统、改变 `open_pr -> guardian -> merge_pr` 主流程、回退 #24 的 guardian context 瘦身、引入新的治理主题或门禁机制

## 当前停点

- 已确认本地 `main` 原先与 `origin/main` 分叉；现已先对齐到包含 #24 的主线提交 `6fd5b55b8d8bc69e1eb573c522f9f77faeedf5b4`，并复用 issue-25 独立 worktree。当前停在模板/自动化偏差收敛与最小改动落地前。

## 下一步动作

- 收缩 PR 模板，去掉 `变更文件` / 检查清单等冗余正文输入。
- 让 `open_pr` 自动填充最小 Issue 摘要，并更新 guardian prompt 与测试。
- 跑最小必要验证、开 PR、推进 guardian / checks / merge，最后清理分支与 worktree。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 治理基线补齐“模板输入最小化 + 自动化入口对齐”的最后一环，避免 reviewer / guardian 再把 PR 模板噪音当主审查上下文。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：父事项 `#21` 下承接 #24 的收口项，负责把 lean review context 模型继续落到 PR 模板与受控入口。
- 阻塞：无外部阻塞；需严格限制在 review template / automation 对齐范围内。

## 已验证项

- `gh issue view 25 --repo MC-and-his-Agents/Syvert`
- `git fetch origin main`
- 已确认本地 `main` 与 `origin/main` 已同步到 `6fd5b55b8d8bc69e1eb573c522f9f77faeedf5b4`
- `python3 scripts/create_worktree.py --issue 25 --class governance --dry-run`
- 已复用 worktree：`/Users/claw/code/worktrees/syvert/issue-25-governance-align-review-templates-and-automation-with-lean-context-model`
- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`code_review.md`
- 已阅读：`docs/process/worktree-lifecycle.md`
- 已阅读：`docs/process/branch-retirement.md`
- 已阅读：`scripts/pr_guardian.py`
- 已阅读：`scripts/open_pr.py`
- 已阅读：`.github/PULL_REQUEST_TEMPLATE.md`
- 已阅读：`scripts/governance_status.py`
- 已阅读：`tests/governance/test_open_pr.py`
- 已阅读：`tests/governance/test_pr_guardian.py`
- 已阅读：`tests/governance/test_governance_status.py`

## 未决风险

- 若把 PR 模板继续设计成冗长 checklist，会直接抵消 #24 的 guardian context 瘦身收益。
- 若 `open_pr` 自动冻结的 Issue 摘要过宽，会重新把相邻事项噪音注入审查上下文。
- 若改动触碰 `merge_pr` 或 guardian verdict schema，会越界并削弱现有 merge gate 闭环。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对模板、`open_pr`、guardian prompt、测试与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `6fd5b55b8d8bc69e1eb573c522f9f77faeedf5b4`
