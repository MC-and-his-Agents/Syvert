# CHORE-0068 执行计划

## 关联信息

- item_key：`CHORE-0068-fr-0004-formal-spec-closeout`
- Issue：`#68`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 状态：`inactive (historical spec closeout; superseded by implementation closeout round after PR #82 merged)`
- 关联 spec：`docs/specs/FR-0004-input-target-and-collection-policy/`
- 关联 PR：`#82`
- 历史收口事项：`CHORE-0068-fr-0004-formal-spec-closeout`

## 目标

- 通过独立 spec PR 收口 `FR-0004` formal spec，使 `InputTarget` 与 `CollectionPolicy` 成为主干上的共享契约真相。
- 满足当前仓库 `open_pr` / guardian / merge gate 对 active `exec-plan` 的受控入口要求，但不扩展为 implementation exec-plan。

## 范围

- 本次纳入：
  - `docs/specs/FR-0004-input-target-and-collection-policy/**`
  - `docs/exec-plans/FR-0004-input-target-and-collection-policy.md`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
  - 本 exec-plan
- 本次不纳入：
  - `src/**`
  - `scripts/**`
  - `tests/**`
  - implementation work item 的运行时代码、测试与执行证据

## 当前停点

- 历史 worktree / 分支：`issue-68-inputtarget-collectionpolicy`，已用于完成 `#68` 的 formal spec closeout 回合。
- 历史 PR `#75` 已因 GitHub checks 未绑定最新 head 而关闭；formal spec 审查最终由 PR `#82` 承接并完成。
- PR `#82` 已合入主干，`FR-0004` formal spec 套件、对应 release / sprint 索引与本 exec-plan 的历史记录已入库。
- 最近一次显式 checkpoint 绑定 `e600b4d26717227f2610c1434a39b350271c67ee`；后续 closeout 语义已由 implementation 聚合回合接管，不再在本文件上继续推进 active 执行动作。

## 下一步动作

- 无 active 动作。
- `FR-0004` 的后续执行与 GitHub closeout 由 `docs/exec-plans/CHORE-0068-fr-0004-implementation-closeout.md` 继续承接；本文件仅保留为 formal spec 历史收口记录。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 冻结共享输入模型与采集策略模型，使后续实现、registry、harness 与回归 gate 都可围绕统一 contract 推进。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`#64 / FR-0004` 下的 spec closeout Work Item，负责把共享输入模型与采集策略模型入库到主干。
- 阻塞：必须保持 spec-only 边界；若 formal spec 越界到错误模型、registry、harness、version gate 或实现代码，当前回合应停止并回退到规约边界。

## 已验证项

- `python3 scripts/create_worktree.py --issue 68 --class spec`
- 已阅读：`vision.md`
- 已阅读：`docs/roadmap-v0-to-v1.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`spec_review.md`
- 已阅读：`docs/releases/v0.2.0.md`
- 已核对 GitHub 真相：`#63=Phase`、`#64=FR`、`#68=Work Item`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/spec_guard.py --mode ci --all`
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
- `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
- `python3 scripts/open_pr.py --class spec --issue 68 --item-key CHORE-0068-fr-0004-formal-spec-closeout --item-type CHORE --release v0.2.0 --sprint 2026-S15 --title 'spec: 冻结 FR-0004 的 InputTarget 与 CollectionPolicy 模型' --closing refs --dry-run`
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
- 已创建当前受审 PR：`#82 https://github.com/MC-and-his-Agents/Syvert/pull/82`
- 已确认当前受审 head 的 GitHub checks：`Validate Commit Messages`、`Validate Docs And Guard Scripts`、`Validate Governance Tooling`、`Validate Spec Review Boundaries` 全绿
- 已完成多轮 guardian 审查，并按阻断收口了兼容映射、`spec review` 口径、active `exec-plan` 绑定、Adapter SDK 契约边界与恢复工件一致性
- 已完成 formal spec 合入：PR `#82` merged，`FR-0004` formal spec 成为主干真相

## 未决风险

- 若 formal spec 过拟合当前 URL-only detail 场景，后续共享模型会被迫回写 `FR-0004`。
- 若 `CollectionPolicy` 吞并后续 FR 的职责，implementation work item 会在无 formal spec 授权的情况下扩边界。
- 若事项上下文、active `exec-plan` 与受控入口字段不一致，PR 无法合法创建。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `FR-0004` formal spec 套件、索引更新与当前最小 exec-plan。

## 最近一次 checkpoint 对应的 head SHA

- `e600b4d26717227f2610c1434a39b350271c67ee`
