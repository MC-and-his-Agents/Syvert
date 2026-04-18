# GOV-0031 执行计划

## 关联信息

- item_key：`GOV-0031-guardian-live-head-binding`
- Issue：`#150`
- item_type：`GOV`
- release：`v0.3.0`
- sprint：`2026-S16`
- 关联 spec：无（治理脚本事项）
- 关联 decision：`docs/decisions/ADR-GOV-0031-guardian-live-head-binding.md`
- 关联 PR：
- active 收口事项：`GOV-0031-guardian-live-head-binding`

## 目标

- 修复 guardian / closeout 流程在 metadata-only docs follow-up 下对“当前受审 head”进行自引用追逐的问题。
- 把 live review head 与 checkpoint head 的 carrier 边界固定回 `PR metadata + guardian state` vs `versioned exec-plan`。
- 为 guardian prompt 与治理测试补齐明确约束，避免后续 closeout 回合再次围绕静态 SHA 追逐。

## 范围

- 本次纳入：`scripts/pr_guardian.py`、`tests/governance/test_pr_guardian.py`、`WORKFLOW.md`、`docs/process/agent-loop.md`、`docs/exec-plans/README.md`、`docs/exec-plans/_template.md`、本事项 `decision` / `exec-plan`、必要的 release / sprint 索引
- 本次不纳入：`merge_pr` 条件放宽、guardian verdict schema 调整、已有历史 closeout 工件的大规模迁移、`FR-0008` runtime / formal spec 语义改写

## 当前停点

- `#149` 合入后，`FR-0008` 已完成主干收口，但暴露出 guardian 对 metadata-only closeout head 的自引用追逐问题。
- 当前已确认根因不在 runtime 或 closeout 语义，而在于 live review head 被错误地期待写回会继续被 PR 改动的 versioned `exec-plan`。
- 当前治理修复已在 checkpoint `a1f1cba463e7036e0fe7155d8b1b99789f84b03e` 落盘：guardian prompt、回归测试、bootstrap decision、active `exec-plan` 与 release / sprint 索引已同步对齐。
- 当前停在推送分支与创建 PR 前；下一步进入受控 `open_pr`、guardian gate 与 merge gate 收口。

## 下一步动作

- 推送 `issue-150-chore-guardian-metadata-only-closeout-head` 分支。
- 通过受控入口创建治理 PR，并把 `Issue` / `item_key` / `release` / `sprint` 与 canonical `integration_check` carrier 对齐。
- 运行 guardian 审查与受控 merge，随后同步关闭 `#150` 并更新 Project 状态。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.3.0` 的 closeout 治理链补齐稳定的 live head / checkpoint carrier 边界，避免 parent closeout PR 因 metadata-only sync 陷入自引用循环。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0008` closeout 后的治理修复项，负责把 guardian gate 对 live head 的消费边界恢复为单一 contract。
- 阻塞：无外部实现阻塞；需要确保改动只修复 live head carrier，不误放宽 merge gate 或 reviewer rubric。

## 已验证项

- `gh issue view 150 --repo MC-and-his-Agents/Syvert`
- `gh issue edit 150 --title "[GOV] 修复 guardian 对 metadata-only closeout head 的自引用追逐"`
- `python3 scripts/create_worktree.py --issue 150 --class governance`
- 已创建 worktree：`/Users/mc/code/worktrees/syvert/issue-150-chore-guardian-metadata-only-closeout-head`
- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/process/agent-loop.md`
- 已阅读：`docs/exec-plans/README.md`
- 已阅读：`scripts/pr_guardian.py`
- 已阅读：`tests/governance/test_pr_guardian.py`
- 已完成最小改动文件：`scripts/pr_guardian.py`
- 已完成最小改动文件：`tests/governance/test_pr_guardian.py`
- 已完成最小改动文件：`WORKFLOW.md`
- 已完成最小改动文件：`docs/process/agent-loop.md`
- 已完成最小改动文件：`docs/exec-plans/README.md`
- 已完成最小改动文件：`docs/exec-plans/_template.md`
- 已完成最小改动文件：`docs/releases/v0.3.0.md`
- 已完成最小改动文件：`docs/sprints/2026-S16.md`
- 已完成最小改动文件：`docs/decisions/ADR-GOV-0031-guardian-live-head-binding.md`
- 已完成最小改动文件：`docs/exec-plans/GOV-0031-guardian-live-head-binding.md`
- `python3 -m unittest tests.governance.test_pr_guardian`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/open_pr.py --class governance --issue 150 --item-key GOV-0031-guardian-live-head-binding --item-type GOV --release v0.3.0 --sprint 2026-S16 --title "fix(governance): 固化 guardian live head 与 checkpoint 边界" --dry-run`

## 未决风险

- 若只修改 prompt 文案而不补治理测试，后续重构仍可能让 guardian 再次回到“要求 exec-plan 追写 live head”的错误边界。
- 若把 metadata-only closeout 例外扩大成任意 PR 的通用放宽，会削弱当前 merge gate 的 head 一致性要求。
- 若 release / sprint / exec-plan 文档继续把 versioned `exec-plan` 当 live head 状态面，治理口径仍可能再次分裂。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `scripts/pr_guardian.py`、`tests/governance/test_pr_guardian.py`、本事项 decision / exec-plan 与相关治理文档的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `a1f1cba463e7036e0fe7155d8b1b99789f84b03e`
- 说明：该 checkpoint 首次把 guardian live head / checkpoint carrier 边界、回归测试、bootstrap decision 与 sprint / release 索引同步落盘；后续若只补 PR / guardian / merge gate 追账，则作为 metadata-only follow-up 记录，不把版本化 `exec-plan` 退化为 live head 状态面。
