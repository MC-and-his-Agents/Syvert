# FR-0003 TODO

## 关联信息

- item_key：`FR-0003-github-delivery-structure-and-repo-semantic-split`
- Issue：`#55`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`
- exec_plan：`docs/exec-plans/GOV-0027-governance-contract-rewrite.md`

## 状态

- 当前成熟度：`spec-ready`
- 当前阻塞：等待 `GOV-0027` 完成治理文档、索引与 PR closeout；后续 `#57`、`#58` 仍待独立 Work Item 收口

## 实施清单

- [x] 建立 `FR-0003` formal spec 套件并冻结治理目标与边界
- [ ] 通过 `GOV-0027` 收敛顶层治理文档、release/sprint 索引与 decision / exec-plan
- [ ] 通过 `GOV-0028` 处理 harness 兼容迁移
- [ ] 通过 `GOV-0029` 单独处理 `TODO.md` 治理清理

## 验证清单

- [ ] `pr_scope_guard` 证明当前 PR 只含 governance/docs/spec 变更
- [x] `open_pr --dry-run` 通过
- [x] `workflow_guard`、`docs_guard`、`governance_gate`、`tests/governance` 通过
- [ ] `commit_check` 已覆盖本事项提交

## 会话恢复信息

- 当前停点：formal spec、治理文档、release/sprint 索引与 decision / exec-plan 已落盘，本地门禁已通过，等待提交后重跑基于提交图的 preflight 并开 PR
- 下一步动作：继续执行 `GOV-0027`，提交、重跑 `pr_scope_guard` / `commit_check`，开 PR 并完成 review / guardian / merge gate
