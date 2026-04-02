# CHORE-0034 执行计划

## 关联信息

- item_key：`CHORE-0034-review-recovery`
- Issue：`#34`
- item_type：`CHORE`
- release：`v0.1.0`
- sprint：`2026-S14`
- 关联 spec：无（文档回滚与流程恢复事项）
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 关联 PR：`https://github.com/MC-and-his-Agents/Syvert/pull/35`
- active 收口事项：`CHORE-0034-review-recovery`

## 目标

- 通过受控 PR 回滚 `PR #33` 的合并结果，恢复到合并前文档状态。
- 在恢复后重新发起文档变更 PR，并按 guardian / merge gate 完整执行审查。

## 范围

- 本次纳入：`vision.md` 与 `docs/roadmap-v0-to-v1.md` 回滚、`CHORE-0032` 历史 exec-plan 保留、本回合 `exec-plan` 建立。
- 本次不纳入：新增文档策略内容、实现代码修改、治理协议重写。

## 当前停点

- 已完成受控回滚 PR `#35` 创建并通过 CI 门禁，当前处于 guardian 审查与合并前收口阶段。

## 下一步动作

- 依据 guardian 审查意见补齐证据或上下文（若有）。
- 通过 `merge_pr` 受控入口执行 squash merge。
- 回滚完成后在新回合重新提交原文档调整并等待完整审查。

## 当前 checkpoint 推进的 release 目标

- 纠正 `v0.1.0` 回合中的流程偏差，恢复“先受控审查再合并”的治理纪律。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：回滚与流程恢复事项。
- 阻塞：无。

## 已验证项

- `git revert --no-commit 97cd992cca67369667842b602de94a4c290641c9`
- `git commit -m "revert(docs): 回滚 PR33 以恢复受控审查前状态"`
- `git diff --exit-code 30bc127683b8905c4c2a2115213d61e308b29742 -- vision.md docs/roadmap-v0-to-v1.md`
- `git diff --name-only origin/main...HEAD`
- `python3 scripts/docs_guard.py --mode ci`
- `gh pr checks 35`
- `git rev-parse HEAD`

## 未决风险

- 若后续重提 PR 仍绕过受控链路，会重复触发同类流程风险。
- 若重提事项不复用清晰的 item 上下文，会导致审查证据难以追踪。

## 回滚方式

- 如需撤销本次回滚，可在后续受控 PR 中重新引入经过审查的文档改动。

## 最近一次 checkpoint 对应的 head SHA

- `b9c54a01c3f91d1f4e5cfd74c830d0c678c0404b`
