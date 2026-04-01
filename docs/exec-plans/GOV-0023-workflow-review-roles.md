# GOV-0023 执行计划

## 关联信息

- item_key：`GOV-0023-workflow-review-roles`
- Issue：`#23`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S14`
- 关联 spec：无（治理文档事项）
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 关联 PR：`#27`
- active 收口事项：`GOV-0023-workflow-review-roles`

## 目标

- 让 `WORKFLOW.md` 与流程文档显式区分 reviewer、guardian、CI、merge gate 的职责边界。
- 把 #22 已落地的 review rubric 语义接入流程契约，避免 reviewer rubric 与 merge gate 再次混写。
- 明确 review / guardian 输入应优先使用最小必要上下文，避免重复探索与越界到 #24 / #25。

## 范围

- 本次纳入：`WORKFLOW.md`、`docs/AGENTS.md`、`docs/process/delivery-funnel.md`、本事项 `exec-plan`
- 本次不纳入：`scripts/pr_guardian.py`、guardian prompt/context 瘦身、`.github/PULL_REQUEST_TEMPLATE.md`、`open_pr.py`、`merge_pr.py`、`governance_status.py`、#24 / #25 的自动化与模板改动

## 当前停点

- PR `#27` 已绑定 Issue `#23` 打开；当前文档改动与职责边界口径已落盘，停在等待 checks 全绿、guardian 审查与受控 merge。

## 下一步动作

- 补齐 PR 摘要中的验证与范围说明，确保审查输入围绕当前 diff 的最小必要上下文。
- 等待 GitHub checks 全绿后执行 guardian 审查。
- 继续推进 checks、guardian、受控 merge 与分支/worktree 清理。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 治理基线补齐“审查职责边界”层面的流程契约，避免后续 #24 / #25 在错误职责模型上继续迭代。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：父事项 `#21` 下承接 #22 的串行治理收口项，负责把 rubric 语义对齐到流程层。
- 阻塞：依赖 `main` 已包含 #22；当前已满足。

## 已验证项

- `gh issue view 23 --repo MC-and-his-Agents/Syvert`
- `gh issue view 21 --repo MC-and-his-Agents/Syvert`
- `git fetch origin --prune`
- 已确认 `origin/main` 包含 `6d1b4fd 治理: 强化 spec review 与 code review rubric (#26)`
- `python3 scripts/create_worktree.py --issue 23 --class governance`
- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`docs/process/agent-loop.md`
- 已阅读：`docs/process/worktree-lifecycle.md`
- 已阅读：`docs/process/branch-retirement.md`
- 已阅读：`spec_review.md`
- 已阅读：`code_review.md`
- 已完成最小改动文件：`WORKFLOW.md`
- 已完成最小改动文件：`docs/AGENTS.md`
- 已完成最小改动文件：`docs/process/delivery-funnel.md`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/context_guard.py`
- `python3 scripts/open_pr.py --class governance --issue 23 --item-key GOV-0023-workflow-review-roles --item-type GOV --release v0.1.0 --sprint 2026-S14 --title "docs(governance): 对齐 reviewer guardian 与 CI 职责边界" --dry-run`
- 已确认 PR：`#27 https://github.com/MC-and-his-Agents/Syvert/pull/27`
- 已确认 checks：`Validate Commit Messages` / `Validate Docs And Guard Scripts` / `Validate Spec Review Boundaries` 通过，`Validate Governance Tooling` 处理中
- 已用关键词检索复核 `WORKFLOW.md` / `docs/AGENTS.md` / `docs/process/delivery-funnel.md` 与 `spec_review.md` / `code_review.md` 的职责边界口径一致

## 未决风险

- 若把 reviewer rubric 与 guardian / merge gate 再次写混，会直接违背 #22 与本事项目标。
- 若把“最小必要上下文”写成脚本或模板行为承诺，会越界到 #24 / #25。
- 需在验证阶段再次确认 `WORKFLOW.md` 新增的 `merge_pr` 入口表述没有把 reviewer 审查错误并入 merge gate 定义。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对流程文档与 `exec-plan` 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `dc4a0fbbc507b977d3e50e61233e350358a20ef9`
