# FR-0003 TODO

## 关联信息

- item_key：`FR-0003-github-delivery-structure-and-repo-semantic-split`
- Issue：`#55`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`
- active_work_item：`GOV-0029-remove-legacy-todo-md`
- exec_plan：`docs/exec-plans/GOV-0029-remove-legacy-todo-md.md`

## 状态

- 当前成熟度：`implementation-ready`
- 当前阻塞：`FR-0003` 既有基线已通过 spec review 并支撑 `PR #59` / `PR #60` 合入；当前 active Work Item `GOV-0029` 正在以独立 formal spec PR `#61` 审查 legacy `TODO.md` 退出 formal governance flow 的增量规约，待其通过后再进入独立 governance 实现 PR

## 实施清单

- [x] 建立 `FR-0003` formal spec 套件并冻结治理目标与边界
- [x] 通过 `GOV-0027` 收敛顶层治理文档、release/sprint 索引与 decision / exec-plan，并完成 PR `#59` closeout
- [x] 通过 `GOV-0028` 处理 harness 兼容迁移，并完成 PR `#60` closeout
- [ ] 通过 `GOV-0029` 完成 legacy `TODO.md` 退出 formal governance flow 的增量规约审查与后续独立治理实现收口

## 验证清单

- [x] `PR #59` 已完成 `FR-0003` 基线规约收敛并合入主干
- [x] `PR #60` 已在既有 `FR-0003` 批准基线上完成 harness 兼容迁移并合入主干
- [x] 当前 `GOV-0029` 增量规约 PR `#61` 已通过 `docs_guard`、`spec_guard`、`pr_scope_guard --class spec` 与 `open_pr --class spec --dry-run`
- [ ] 当前 `GOV-0029` 增量规约 PR `#61` 的 guardian / reviewer / merge gate 已完成
- [ ] `GOV-0029` 的后续独立 governance 实现 PR 已完成 guardian / reviewer / merge gate

## spec review 结论

- 结论：`FR-0003` 既有基线已通过；`GOV-0029` 的增量规约 PR `#61` 审查中
- 进入实现前条件：`FR-0003` 既有基线已满足；`GOV-0029` 的新增语义待当前 formal spec PR 通过后，方可进入独立 governance 实现 PR
- 说明：`PR #59` / `PR #60` 的合法性来源保持不变，当前只对 legacy `TODO.md` 退出 formal governance flow 这条窄语义追加独立规约审查链路

## 会话恢复信息

- 当前停点：`FR-0003` 既有基线保持 `implementation-ready`；当前 active Work Item 已切换为 `GOV-0029`，正在通过 spec-only PR `#61` 审查 legacy `TODO.md` 退出 formal governance flow 的增量规约
- 下一步动作：等待 `PR #61` 的 guardian / merge gate 收口；合入后基于更新后的 `FR-0003` 基线继续执行 `GOV-0029` 的独立 governance 实现 PR
