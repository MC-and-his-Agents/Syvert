# CHORE-0032 执行计划

## 关联信息

- item_key：`CHORE-0032-review-recovery`
- Issue：`#32`
- item_type：`CHORE`
- release：`v0.1.0`
- sprint：`2026-S14`
- 关联 spec：无（文档回滚与流程恢复事项）
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 关联 PR：待补充
- active 收口事项：`CHORE-0032-review-recovery`

## 目标

- 回滚 `PR #33` 的合并结果，恢复到合并前文档状态。
- 在受控流程下重新发起文档变更审查回合，避免绕过 guardian / merge gate。

## 范围

- 本次纳入：`vision.md`、`docs/roadmap-v0-to-v1.md` 的回滚，以及当前回合 `exec-plan` 建立。
- 本次不纳入：新的产品或实现改动；重写治理协议。

## 当前停点

- 已在 `origin/main` 基础上生成回滚提交，正准备通过受控入口创建回滚 PR。

## 下一步动作

- 推送回滚分支并创建 docs 类受控 PR。
- 回滚 PR 合入后，基于受控流程重新发起原文档调整 PR 并等待 guardian 结果。

## 当前 checkpoint 推进的 release 目标

- 纠正 `v0.1.0` 交付流程偏差，恢复“先审查后合并”的治理纪律。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：流程恢复与风险隔离事项。
- 阻塞：无。

## 已验证项

- `git rev-parse HEAD`
- `git revert --no-commit 97cd992cca67369667842b602de94a4c290641c9`
- `git commit -m "revert(docs): 回滚 PR33 以恢复审查前状态"`

## 未决风险

- 若回滚 PR 再次绕过受控入口，会重复触发流程风险。
- 回滚后重提文档调整若不绑定同一事项上下文，可能导致审查链路断裂。

## 回滚方式

- 如需撤销本次回滚，可在后续受控 PR 中重新引入已回滚文档改动。

## 最近一次 checkpoint 对应的 head SHA

- `7b950b2d5d1aa02d3282ec6ddc41f35d29ff8e01`
