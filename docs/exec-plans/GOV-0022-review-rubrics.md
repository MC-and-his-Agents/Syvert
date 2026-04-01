# GOV-0022 执行计划

## 关联信息

- item_key：`GOV-0022-review-rubrics`
- Issue：`#22`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S14`
- 关联 spec：无（治理文档事项）
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 关联 PR：待补充
- active 收口事项：`GOV-0022-review-rubrics`

## 目标

- 将 `spec review` 与 `code review` 从“格式/门禁说明”升级为正式的 reviewer rubric。
- 在文档层面清晰拆分 `review rubric`、`merge gate` 与 `工件完整性检查` 三类语义。

## 范围

- 本次纳入：`spec_review.md`、`code_review.md`、本事项 `exec-plan`
- 本次不纳入：`WORKFLOW.md`、流程文档、脚本、PR 模板、guardian prompt、自动化入口

## 当前停点

- `spec_review.md` 与 `code_review.md` 已完成 rubric 增强和章节拆分，当前停在提交前自检完成、准备生成提交与 PR 描述。

## 下一步动作

- 复核最终 diff 与范围边界，确认未触及 #23 / #24 / #25。
- 生成中文 Conventional Commit，推送分支并创建仅针对 Issue `#22` 的 governance PR。
- 在 PR 描述中明确本次仅增强 review rubric，不涉及自动化和 guardian prompt 瘦身。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 治理基线补齐可执行的人审标准，降低后续 #23 / #24 / #25 对审查语义继续返工的风险。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：父事项 `#21` 下的串行前置治理文档收口项
- 阻塞：无外部阻塞；需严格避免越界修改到 #23 / #24 / #25

## 已验证项

- `gh issue view 22 --repo MC-and-his-Agents/Syvert`
- `python3 scripts/create_worktree.py --issue 22 --class governance`
- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/process/worktree-lifecycle.md`
- 已阅读：`docs/process/agent-loop.md`
- 已阅读：`spec_review.md`
- 已阅读：`code_review.md`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/docs_guard.py --mode ci`
- 已核对当前 diff 仅涉及 `spec_review.md`、`code_review.md` 与本事项 `exec-plan`

## 未决风险

- 若 rubric 描述过于流程化，可能与 #23 的职责对齐事项产生边界重叠。
- 若把 merge gate 条件继续混入 reviewer rubric，会直接违背本事项目标。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `spec_review.md`、`code_review.md` 与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `2f4d1258076c3507d0d331ed29047dda9ba41c55`
