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
- 让 `open_pr`、guardian prompt 与相关状态面继续消费最小必要字段，而不是整段模板噪音。
- 让 guardian prompt 与新的 lean review context 模型保持一致，不削弱既有 merge gate、安全性与 head 绑定逻辑。

## 范围

- 本次纳入：`.github/PULL_REQUEST_TEMPLATE.md`、`scripts/open_pr.py`、`scripts/pr_guardian.py`、必要的治理测试、本事项 `exec-plan`
- 本次不纳入：重写整套 review 系统、改变 `open_pr -> guardian -> merge_pr` 主流程、回退 #24 的 guardian context 瘦身、引入新的治理主题或门禁机制

## 当前停点

- 已完成 `.github/PULL_REQUEST_TEMPLATE.md` 与 `open_pr` 的最小对齐改动，并确认 guardian 继续沿用 #24 的 lean review context builder；当前停在提交、推送、创建 PR 前。

## 下一步动作

- 以中文 Conventional Commits 提交当前改动并推送 issue-25 分支。
- 通过受控入口创建仅针对 Issue `#25` 的 governance PR。
- 继续推进 checks、guardian、受控 merge 与分支/worktree 清理。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 治理基线补齐“模板输入最小化 + 自动化入口对齐”的最后一环，避免 reviewer / guardian 再把 PR 模板噪音当主审查上下文。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：父事项 `#21` 下承接 #24 的收口项，负责把 lean review context 模型继续落到 PR 模板与受控入口。
- 阻塞：无外部阻塞；需严格限制在 review template / automation 对齐范围内。

## 已验证项

- `gh issue view 25 --repo MC-and-his-Agents/Syvert`
- `gh pr view 28 --repo MC-and-his-Agents/Syvert --json number,title,mergeCommit,state,url`
- `python3 scripts/create_worktree.py --issue 25 --class governance`
- 已创建 worktree：`/Users/claw/code/worktrees/syvert/issue-25-governance-align-review-templates-and-automation-with-lean-context-model`
- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`code_review.md`
- 已阅读：`docs/process/agent-loop.md`
- 已阅读：`docs/process/worktree-lifecycle.md`
- 已阅读：`docs/process/branch-retirement.md`
- 已阅读：`scripts/pr_guardian.py`
- 已阅读：`scripts/open_pr.py`
- 已阅读：`.github/PULL_REQUEST_TEMPLATE.md`
- 已阅读：`scripts/governance_status.py`
- 已阅读：`tests/governance/test_open_pr.py`
- 已阅读：`tests/governance/test_pr_guardian.py`
- 已阅读：`tests/governance/test_governance_status.py`
- 已完成最小改动文件：`.github/PULL_REQUEST_TEMPLATE.md`
- 已完成最小改动文件：`scripts/open_pr.py`
- 已完成最小改动文件：`tests/governance/test_open_pr.py`
- 已确认 `scripts/pr_guardian.py` 无需额外改动即可继续消费 `Issue 摘要 / 关联事项 / 风险 / 验证 / 回滚` 结构
- `python3 -m unittest tests.governance.test_open_pr tests.governance.test_pr_guardian tests.governance.test_governance_status`
- `python3 -m unittest tests.governance.test_cli_smoke`
- `python3 scripts/context_guard.py`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/open_pr.py --class governance --issue 25 --item-key GOV-0025-review-template-lean-context --item-type GOV --release v0.1.0 --sprint 2026-S14 --title "refactor(governance): 对齐审查模板与精简上下文入口" --dry-run`

## 未决风险

- 若把 PR 模板继续设计成冗长 checklist，会直接抵消 #24 的 guardian context 瘦身收益。
- 若 guardian raw-body fallback 仍把旧模板的 `检查清单` / `变更文件` 重新注入 prompt，会让 lean context 在提示层面回退。
- 若改动触碰 `merge_pr` 或 guardian verdict schema，会越界并削弱现有 merge gate 闭环。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对模板、`open_pr`、guardian prompt、测试与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `5b4c220d8983ccd452f44596099384af3b99696e`
