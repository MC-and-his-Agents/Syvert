# FR-0003 TODO

> legacy optional: 本文件仅保留 FR-0003 历史检查清单与迁移备注。当前 authoritative 恢复入口是 `docs/exec-plans/GOV-0028-harness-compat-migration.md`，GitHub 仍是状态真相源。

## 关联信息

- item_key：`FR-0003-github-delivery-structure-and-repo-semantic-split`
- Issue：`#55`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`
- active_work_item：`GOV-0028-harness-compat-migration`
- exec_plan：`docs/exec-plans/GOV-0028-harness-compat-migration.md`

## legacy 用途说明

- 当前 active Work Item：`GOV-0028-harness-compat-migration`
- 当前 authoritative 恢复入口：`docs/exec-plans/GOV-0028-harness-compat-migration.md`
- 本文件不再作为成熟度、阻塞、checkpoint 或下一步动作的权威载体。

## 历史检查清单

- [x] 建立 `FR-0003` formal spec 套件并冻结治理目标与边界
- [x] 通过 `GOV-0027` 收敛顶层治理文档、release/sprint 索引与 decision / exec-plan，并完成 PR `#59` closeout
- [ ] 通过 `GOV-0028` 处理 harness 兼容迁移，并将 `TODO.md` 从 required file 降为 legacy optional
- [ ] 通过 `GOV-0029` 单独处理 `TODO.md` 治理清理

## 历史验证备注

- [x] `pr_scope_guard` 证明当前 PR 只含 governance/docs/spec 变更
- [x] `open_pr --dry-run` 通过
- [x] `workflow_guard`、`docs_guard`、`governance_gate`、`tests/governance` 通过
- [x] `commit_check` 已覆盖本事项提交
- [ ] guardian / reviewer / merge gate 已完成

## spec review 结论

- 结论：通过
- 进入实现前条件：已满足
- 说明：`GOV-0027` 已冻结 formal spec / decision / release-sprint 边界；当前 active Work Item 切换到 `GOV-0028`，继续收口 harness / guard / review 输入的兼容迁移。

## 历史备注

- `FR-0003` formal spec 已完成 spec review 并进入 `implementation-ready`。
- 当前 PR / 恢复上下文以 `GOV-0028` 的 active `exec-plan` 为准；本文件仅保留 legacy 参考。
