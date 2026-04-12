# GOV-0029 执行计划

## 关联信息

- item_key：`GOV-0029-remove-legacy-todo-md`
- Issue：`#58`
- item_type：`GOV`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/`
- 额外关联 specs：docs/specs/FR-0001-governance-stack-v1/, docs/specs/FR-0002-content-detail-runtime-v0-1/
- 关联 decision：`docs/decisions/ADR-GOV-0029-remove-legacy-todo-md.md`
- active 收口事项：`GOV-0029-remove-legacy-todo-md`

## 目标

- 把 legacy `TODO.md` 从 formal governance flow、formal spec live 最小套件与模板中移除。
- 收敛 guard、policy、`open_pr`、治理测试与文档索引对 legacy `TODO.md` 的剩余依赖。
- 让 `Issue #58` 的关闭条件在仓内实现、GitHub 状态和主干事实三者间保持一致。

## 范围

- 本次纳入：
  - `docs/AGENTS.md`
  - `docs/exec-plans/GOV-0029-remove-legacy-todo-md.md`
  - `docs/exec-plans/FR-0002-content-detail-runtime-v0-1.md`
  - `docs/releases/v0.2.0.md`
  - `docs/specs/README.md`
  - `docs/specs/_template/`
  - `docs/specs/FR-0001-governance-stack-v1/`
  - `docs/specs/FR-0002-content-detail-runtime-v0-1/`
  - `docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/`
  - `docs/sprints/2026-S15.md`
  - `spec_review.md`
  - `scripts/docs_guard.py`
  - `scripts/context_guard.py`
  - `scripts/item_context.py`
  - `scripts/open_pr.py`
  - `scripts/spec_guard.py`
  - `scripts/policy/loader.py`
  - `scripts/policy/policy.json`
  - `tests/governance/test_context_guard.py`
  - `tests/governance/test_docs_guard.py`
  - `tests/governance/test_governance_gate.py`
  - `tests/governance/test_item_context.py`
  - `tests/governance/test_open_pr.py`
  - `tests/governance/test_pr_scope_guard.py`
  - `tests/governance/test_spec_guard.py`
- 本次不纳入：
  - formal spec 新语义变更
  - 与 legacy `TODO.md` 清理无关的 harness 兼容改造
  - `v0.2.0` 业务实现

## 当前停点

- `PR #61` 已在 `main@8f4096f` 完成 formal spec / governance contract 收口，当前实现回合以该主干真相为起点。
- 已从 backup 恢复 legacy `TODO.md` 清理所需的 guard、policy、`open_pr` 与治理测试链，并把 `FR-0002` foreign exec-plan 例外对齐到当前主干批准版本。
- 已删除模板与 `FR-0001` / `FR-0002` / `FR-0003` 套件中的 legacy `TODO.md` 实体，当前剩余工作是把引用、索引、门禁与 closing 语义收成一致。

## 下一步动作

- 补齐删除后剩余的文档引用与索引回写。
- 运行本地治理测试与门禁，随后以 `Fixes #58` 打开独立 governance implementation PR。
- 等待 GitHub checks 与 guardian 收敛后，用受控入口完成 squash merge 并关闭 `#58`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 的治理收敛回合真正移除 legacy `TODO.md` 这条并行恢复/状态表达路径，只保留 FR formal spec + active `exec-plan` 主链路。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0003 / #55` 下的第三个治理 Work Item，负责完成 formal governance flow 对 legacy `TODO.md` 的最终清理。
- 阻塞：无外部阻塞；当前只需完成实现 PR 的门禁、guardian 与 closeout 收口。

## 已验证项

- `#56 / PR #59` 已完成 GitHub 单一调度层与仓内单一语义层的契约收敛。
- `#57 / PR #60` 已完成 harness 兼容迁移，为 legacy `TODO.md` 清理提供兼容前提。
- `python3 -m unittest tests.governance.test_context_guard tests.governance.test_item_context tests.governance.test_open_pr tests.governance.test_spec_guard tests.governance.test_governance_gate tests.governance.test_docs_guard tests.governance.test_pr_scope_guard`
- `python3 scripts/spec_guard.py --all`
- `python3 scripts/workflow_guard.py`
- `python3 scripts/governance_gate.py --mode local --base-ref origin/main --head-ref HEAD`
- `python3 scripts/open_pr.py --class governance --issue 58 --item-key GOV-0029-remove-legacy-todo-md --item-type GOV --release v0.2.0 --sprint 2026-S15 --closing fixes --dry-run`

## 未决风险

- 若删除 legacy `TODO.md` 后仍残留仓内引用，`docs_guard` 与 guardian 会继续把主干视为未收口。
- 若本轮实现 PR 超出 `GOV-0029` 已批准边界，guardian 仍会再次阻断 merge gate。

## 回滚方式

- 使用独立 revert PR 恢复本事项对 legacy `TODO.md` 文件、治理脚本、测试与索引文档的实现侧清理。

## 最近一次 checkpoint 对应的 head SHA

- `8f4096f0f8385a9f1fd717e6a45987b0403887eb`
