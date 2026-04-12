# FR-0003 TODO

## 关联信息

- item_key：`FR-0003-github-delivery-structure-and-repo-semantic-split`
- Issue：`#55`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`
- active_work_item：`GOV-0027-governance-contract-rewrite`
- exec_plan：`docs/exec-plans/GOV-0027-governance-contract-rewrite.md`

## 状态

- 当前成熟度：`implementation-ready`
- 当前阻塞：当前 active Work Item `GOV-0027` 仍在 PR `#59` 审查中；后续 `#57`、`#58` 仍待独立 Work Item 收口

## 实施清单

- [x] 建立 `FR-0003` formal spec 套件并冻结治理目标与边界
- [ ] 通过 `GOV-0027` 收敛顶层治理文档、release/sprint 索引与 decision / exec-plan，并完成 PR `#59` closeout
- [ ] 通过 `GOV-0028` 处理 harness 兼容迁移
- [ ] 通过 `GOV-0029` 单独处理 `TODO.md` 治理清理

## 验证清单

- [x] `pr_scope_guard` 证明当前 PR 只含 governance/docs/spec 变更
- [x] `open_pr --dry-run` 通过
- [x] `workflow_guard`、`docs_guard`、`governance_gate`、`tests/governance` 通过
- [x] `commit_check` 已覆盖本事项提交
- [ ] guardian / reviewer / merge gate 已完成

## spec review 结论

- 结论：通过
- 进入实现前条件：已满足
- 说明：本轮 formal spec 与 governance contract 收敛共用同一条 `GOV-0027` Work Item / PR 链路，spec review 通过后进入当前治理 PR 审查与 merge gate

## 会话恢复信息

- 当前停点：`FR-0003` formal spec 已完成 spec review 并进入 `implementation-ready`；当前 active Work Item `GOV-0027` 已进入 PR `#59` 审查，等待 guardian / merge gate 收口
- 下一步动作：继续执行 `GOV-0027`，根据 guardian 反馈完成收口，随后走 merge gate 与 closeout
