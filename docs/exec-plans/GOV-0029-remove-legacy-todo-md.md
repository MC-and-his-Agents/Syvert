# GOV-0029 执行计划

## 关联信息

- item_key：`GOV-0029-remove-legacy-todo-md`
- Issue：`#58`
- item_type：`GOV`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/`
- 关联 decision：`docs/decisions/ADR-GOV-0029-remove-legacy-todo-md.md`
- active 收口事项：`GOV-0029-remove-legacy-todo-md`
- 关联 PR：`#61`

## 目标

- 为 `GOV-0029` 先补齐一条独立的 formal spec 审查链路，合法授权 legacy `TODO.md` 退出 formal governance flow。
- 把当前事项需要的规约、decision、release / sprint 索引与 exec-plan 工件链先收成一致。
- 为后续独立 governance 实现 PR 提供可审查、已批准的 formal spec 输入。

## 范围

- 本次纳入：
  - `WORKFLOW.md`
  - `docs/AGENTS.md`
  - `docs/process/agent-loop.md`
  - `spec_review.md`
  - `docs/specs/README.md`
  - `docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/spec.md`
  - `docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/plan.md`
  - `docs/decisions/ADR-GOV-0029-remove-legacy-todo-md.md`
  - `docs/exec-plans/GOV-0029-remove-legacy-todo-md.md`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
- 本次不纳入：
  - `FR-0001` / `FR-0002` 的 legacy `TODO.md` 实体清理
  - 治理 guard、policy、`open_pr` 与测试的实现改造
  - `FR-0002` exec-plan 收口与其他存量文档引用修正
  - 与 `TODO.md` 清理无关的 harness 兼容改造
  - `v0.2.0` 业务实现

## 当前停点

- 上一轮把 `FR-0003` formal spec 语义与治理实现代码放在同一 PR 中，guardian 因“formal spec / implementation 必须分离”给出 `REQUEST_CHANGES`。
- 当前分支已回退为 governance contract 范围，只保留 `FR-0003` formal spec、当前事项 decision / exec-plan、release / sprint 索引，以及使 TODO-exit 语义成为仓内权威口径所必需的治理文档变更；legacy `TODO.md` 的文件删除与实现侧收口留在后续独立 governance 实现 PR。
- 当前目标是先让 PR `#61` 作为独立 formal spec 审查入口合入 `main`，再基于已批准规约继续后续 governance 实现 PR。

## 下一步动作

- 推送当前分支并把 PR `#61` 的标题 / 描述改成 `spec` 审查语义，关闭自动 `Fixes #58`。
- 在当前 PR head 上等待 GitHub checks 与 guardian 收敛，并确认 `APPROVE + safe_to_merge=true`。
- 使用受控入口执行 squash merge，但保持 Issue `#58` 继续打开。
- 基于合入后的 `main` 重建 `GOV-0029` 的独立 governance 实现 PR，完成 `docs/specs/_template/**`、guard、policy、`open_pr`、测试与存量 legacy `TODO.md` 清理。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 的治理收敛回合补齐 legacy `TODO.md` 退出 formal governance flow 所需的正式规约授权，确保后续实现 PR 不再混审规约与实现。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0003 / #55` 下的第三个治理 Work Item，负责完成 formal governance flow 对 legacy `TODO.md` 的最终清理。
- 阻塞：后续实现 PR 必须等待当前 formal spec PR 先合入 `main`。

## 已验证项

- `#56 / PR #59` 已完成 GitHub 单一调度层与仓内单一语义层的契约收敛。
- `#57 / PR #60` 已完成 harness 兼容迁移，为 `TODO.md` 清理的后续实现侧收口提供兼容前提。
- `python3 scripts/docs_guard.py`
- `python3 scripts/spec_guard.py --all`
- `python3 scripts/pr_scope_guard.py --class governance --base-ref origin/main --head-ref HEAD`
- `python3 scripts/open_pr.py --class governance --issue 58 --item-key GOV-0029-remove-legacy-todo-md --item-type GOV --release v0.2.0 --sprint 2026-S15 --closing refs --dry-run`

## 未决风险

- 若当前 spec PR 合入后没有及时跟进独立 governance 实现 PR，formal spec 与实际 guard / policy 行为会暂时不一致。
- 若后续实现 PR 超出本次 formal spec 批准边界，guardian 仍会再次阻断 merge gate。

## 回滚方式

- 使用独立 revert PR 撤销本事项对 `FR-0003` formal spec、decision、release / sprint 索引与当前 exec-plan 的变更。

## 最近一次 checkpoint 对应的 head SHA

- `dda042a01c02c7bef38978321d9a9199291e0b59`
