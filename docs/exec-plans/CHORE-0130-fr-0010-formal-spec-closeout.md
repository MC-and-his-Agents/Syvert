# CHORE-0130-fr-0010-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0130-fr-0010-formal-spec-closeout`
- Issue：`#164`
- item_type：`CHORE`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 spec：`docs/specs/FR-0010-minimal-resource-lifecycle/`
- 关联 PR：`#170`
- 状态：`active`
- active 收口事项：`CHORE-0130-fr-0010-formal-spec-closeout`

## 目标

- 建立并收口 `FR-0010` formal spec 套件，冻结账号资源、代理资源、最小资源包、`AVAILABLE / IN_USE / INVALID` 状态集合，以及 Core 侧 `acquire / release` 主 contract。

## 范围

- 本次纳入：
  - `docs/specs/FR-0010-minimal-resource-lifecycle/`
  - `docs/exec-plans/FR-0010-minimal-resource-lifecycle.md`
  - `docs/exec-plans/CHORE-0130-fr-0010-formal-spec-closeout.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `FR-0011` 的资源 tracing / audit schema
  - `FR-0012` 的 Adapter 注入 boundary
  - 共享 release/sprint 索引

## 当前停点

- `issue-164-fr-0010-formal-spec` 已作为 `#164` 的独立 spec worktree 建立。
- `FR-0010` formal spec 套件与 requirement container / Work Item exec-plan 已在当前分支首次落盘。
- 最新 formal spec 语义 checkpoint `f1b8ea89a54e754356b428aa01aebd900d246991` 已生成，并已通过本地 `spec_guard`、`docs_guard`、`workflow_guard` 与 `governance_gate`。
- spec PR `#170` 已创建并绑定当前分支。
- 当前停点是最新 semantic checkpoint 已对齐到 review-sync / checkpoint 记录，等待 PR checks / guardian 基于当前 live head 继续收口。

## 下一步动作

- 刷新最新 PR checks 与 guardian verdict。
- 若 guardian 放行，则执行受控 merge 并关闭 `#164`。
- `#164` 合入主干后，再把 `FR-0011` / `FR-0012` rebase 到新主干继续收口。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.4.0` 把“最小资源生命周期”从 GitHub 意图推进到 implementation-ready 的主 contract。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0010` 的 formal spec closeout Work Item。
- 阻塞：
  - lifecycle 主 contract 未冻结前，后续资源实现会被迫重新做 requirement 决策。
  - 若 `FR-0011` / `FR-0012` 先写实现或边界而本 FR 未冻结，三个事项会产生交叉漂移。

## 已验证项

- 已核对 `#162`、`#163`、`#164` 对 `v0.4.0` 最小资源系统与本 Work Item 的目标、非目标与关闭条件描述。
- 已核对 `AGENTS.md`、`vision.md`、`docs/roadmap-v0-to-v1.md`、`WORKFLOW.md` 与 `spec_review.md` 的上位约束。
- 已核对 formal spec 模板与近期 closeout 示例 `docs/exec-plans/CHORE-0126-fr-0009-formal-spec-closeout.md`。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-164-fr-0010-formal-spec`
  - 结果：通过
- `git commit -m 'docs(spec): 补齐 FR-0010 资源分配与失败回填契约'`
  - 结果：已生成最新语义 checkpoint `f1b8ea89a54e754356b428aa01aebd900d246991`

## 未决风险

- 若 `ResourceBundle` 与 `ResourceLease` 没有作为 host-side canonical carrier 一次写清，`FR-0011` 与 `FR-0012` 很容易各自长出第二套 schema。
- 若 `resource_unavailable`、冲突 release 与非法状态迁移的 fail-closed 语义不清，实现阶段可能宽松放行并污染共享 truth。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `FR-0010` formal spec 套件与当前 closeout exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `f1b8ea89a54e754356b428aa01aebd900d246991`
- review-sync 说明：后续若只追加 exec-plan checkpoint 同步、`plan.md` 审查口径同步或 PR metadata，则不把 metadata-only follow-up 伪装成新的语义 checkpoint。
