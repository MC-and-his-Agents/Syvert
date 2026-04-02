# GOV-0021 执行计划

## 关联信息

- item_key：`GOV-0021-review-rubrics-and-lean-context-closeout`
- Issue：`#21`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S14`
- 关联 spec：无（治理收口事项）
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 关联 PR：待补充
- active 收口事项：`GOV-0021-review-rubrics-and-lean-context-closeout`

## 目标

- 收口 review rubric / workflow role / lean guardian context / template alignment 这一轮治理主题的剩余小优化。
- 消除 `code_review.md` 与 guardian prompt 之间关于“最小必要上下文”的残余张力。
- 在不引入新治理主题的前提下，为父事项 `#21` 形成可关闭的收口状态。

## 范围

- 本次纳入：`code_review.md`、`scripts/pr_guardian.py`、相关治理测试、本事项 `exec-plan`
- 本次不纳入：新的治理主题、`codex review` 内核迁移、PR 模板重构、merge gate 重写

## 当前停点

- 已完成 `code_review.md` 的“最小必要审查输入”收紧、guardian rubric 节选范围收紧与对应测试；当前停在提 PR 前的最后自检。

## 下一步动作

- 通过受控入口为 `#21` 创建 governance PR。
- 推进 checks、guardian、受控 merge。
- 合并后清理分支 / worktree，并关闭父事项 `#21`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 治理基线完成 review 治理主题收口，确保审查标准、流程职责、上下文瘦身与模板对齐之间不存在残余矛盾。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：父事项收口项
- 阻塞：无外部阻塞；需保持在“小优化 + 关闭父事项”的范围内

## 已验证项

- `gh issue view 21 --json number,title,state,body,url`
- `gh issue view 22 --json number,title,state,url`
- `gh issue view 23 --json number,title,state,url`
- `gh issue view 24 --json number,title,state,url`
- `gh issue view 25 --json number,title,state,url`
- `git rev-parse main`
- 已创建 worktree：`/Users/claw/code/worktrees/syvert/issue-21-governance-strengthen-review-rubrics-and-lean-guardian-review-context`
- 已更新：`code_review.md`
- 已更新：`scripts/pr_guardian.py`
- 已更新：`tests/governance/test_pr_guardian.py`
- 已新增：`docs/exec-plans/GOV-0021-review-rubrics-and-lean-context-closeout.md`
- `python3 -m unittest tests.governance.test_pr_guardian`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/docs_guard.py --mode ci`

## 未决风险

- 若继续保留 `code_review.md` 中过宽的输入清单，容易削弱 #24 已建立的最小必要上下文原则。
- 若 guardian 继续把“审查输入”整段作为 rubric 节选喂给 prompt，会让 reviewer 继续收到宽而散的指导。

## 回滚方式

- 如需回滚，通过独立 revert PR 撤销本事项对 `code_review.md`、`scripts/pr_guardian.py`、测试与本 `exec-plan` 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `4096e0818849bc367bc0268c85cbf1794a1d3306`
