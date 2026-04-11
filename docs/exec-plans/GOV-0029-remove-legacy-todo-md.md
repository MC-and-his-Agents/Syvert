# GOV-0029 执行计划

## 关联信息

- item_key：`GOV-0029-remove-legacy-todo-md`
- Issue：`#58`
- item_type：`GOV`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/`
- active 收口事项：`GOV-0029-remove-legacy-todo-md`
- 关联 PR：`#61`

## 目标

- 把 legacy `TODO.md` 从正式治理流、formal spec 最小套件、guard 与模板中完全移除。
- 收敛仓内仍把 `TODO.md` 当作事项状态镜像、恢复入口或 formal spec 必需工件的引用。
- 保证后续事项只通过 GitHub + FR formal spec + active `exec-plan` 进入交付漏斗。

## 范围

- 本次纳入：
  - `WORKFLOW.md`
  - `docs/AGENTS.md`
  - `docs/process/agent-loop.md`
  - `docs/specs/README.md`
  - `spec_review.md`
  - `code_review.md`
  - `docs/exec-plans/README.md`
  - `docs/specs/FR-0001-governance-stack-v1/**`
  - `docs/specs/FR-0002-content-detail-runtime-v0-1/**`
  - `docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/**`
  - `docs/specs/_template/**`
  - `docs/decisions/ADR-0003-github-delivery-structure-and-repo-semantic-split.md`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
  - `scripts/context_guard.py`
  - `scripts/spec_guard.py`
  - `scripts/policy/loader.py`
  - `scripts/policy/policy.json`
  - `scripts/governance_gate.py`
  - `tests/governance/**`
- 本次不纳入：
  - 新治理契约正文重写
  - 与 `TODO.md` 清理无关的 harness 兼容改造
  - `v0.2.0` 业务实现

## 当前停点

- 已删除 `docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/TODO.md` 与 `docs/specs/_template/TODO.md`，并把 formal spec 最小套件收敛为 `spec.md + plan.md`。
- 当前 head `8e856d0b7df9b6506102d8ab50619f07dca7d02a` 已通过治理单测、`docs_guard`、`spec_guard`、`context_guard`、`workflow_guard`、`governance_gate` 与 `open_pr --dry-run`；PR `#61` 已创建，等待 GitHub checks 与 guardian 收口。

## 下一步动作

- 观察 PR `#61` 的 GitHub checks，确认全部通过。
- 在当前 PR head 上运行 guardian，确认拿到 `APPROVE + safe_to_merge=true`。
- 使用受控入口执行 squash merge，并核对 `#58` 自动关闭与远端分支删除。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 的治理收敛回合去除 legacy `TODO.md` 这条并行恢复/状态表达路径，只保留 FR formal spec + Work Item `exec-plan` 的主链路。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0003 / #55` 下的第三个治理 Work Item，负责完成 formal governance flow 对 legacy `TODO.md` 的最终清理。
- 阻塞：无外部阻塞；需要同时保持历史事项可追溯性，并阻断未来重新引入 `TODO.md` 的入口。

## 已验证项

- `#56 / PR #59` 已完成 GitHub 单一调度层与仓内单一语义层的契约收敛。
- `#57 / PR #60` 已完成 harness 兼容迁移，允许在不破坏现有治理流的前提下清理 `TODO.md` 残留。
- `python3 -m unittest tests.governance.test_spec_guard tests.governance.test_pr_scope_guard tests.governance.test_governance_gate tests.governance.test_context_guard tests.governance.test_item_context tests.governance.test_open_pr tests.governance.test_workflow_guard`
- `python3 scripts/commit_check.py --base-ref origin/main --head-ref HEAD`
- `python3 scripts/docs_guard.py`
- `python3 scripts/spec_guard.py --all`
- `python3 scripts/context_guard.py`
- `python3 scripts/workflow_guard.py`
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref issue-58-governance-remove-legacy-todo-md-from-the-formal-governance-flow`
- `python3 scripts/open_pr.py --class governance --issue 58 --item-key GOV-0029-remove-legacy-todo-md --item-type GOV --release v0.2.0 --sprint 2026-S15 --closing fixes --dry-run`

## 未决风险

- 若 formal spec、guard 与 policy 的更新不同步，可能出现“文档已删除 `TODO.md`，但 guard 仍把它视为合法或必需工件”的双轨状态。
- 若只删模板不删历史实体文件，后续事项仍可能把 legacy `TODO.md` 误认成可继续维护的状态镜像。

## 回滚方式

- 使用独立 revert PR 恢复本事项对 formal spec 文档、guard、policy、测试与 legacy `TODO.md` 文件的变更。

## 最近一次 checkpoint 对应的 head SHA

- `8e856d0b7df9b6506102d8ab50619f07dca7d02a`
