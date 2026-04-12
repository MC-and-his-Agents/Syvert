# FR-0004 执行计划

## 关联信息

- item_key：`FR-0004-input-target-and-collection-policy`
- Issue：`#68`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0004-input-target-and-collection-policy/`
- 关联 PR：
- active 收口事项：`FR-0004-input-target-and-collection-policy`

## 目标

- 通过独立 spec PR 收口 `FR-0004` formal spec，使 `InputTarget` 与 `CollectionPolicy` 成为主干上的共享契约真相。
- 满足当前仓库 `open_pr` / guardian / merge gate 对 active `exec-plan` 的受控入口要求，但不扩展为 implementation exec-plan。

## 范围

- 本次纳入：
  - `docs/specs/FR-0004-input-target-and-collection-policy/**`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
  - 本 exec-plan
- 本次不纳入：
  - `src/**`
  - `scripts/**`
  - `tests/**`
  - implementation work item 的运行时代码、测试与执行证据

## 当前停点

- 已建立 `issue-68-inputtarget-collectionpolicy` worktree，并核对 `#64=FR`、`#68=Work Item`、`release=v0.2.0`、`sprint=2026-S15`。
- 当前停在 formal spec 套件编写、索引补齐与本地门禁前置校验阶段。

## 下一步动作

- 运行 `docs_guard`、`workflow_guard`、`spec_guard`、`governance_gate`、`pr_scope_guard` 与 `open_pr --class spec --dry-run`。
- 提交 spec PR，等待 checks 全绿后执行 guardian。
- guardian 通过后使用受控 `merge_pr` 合入，并回写 closeout 状态。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 冻结共享输入模型与采集策略模型，使后续实现、registry、harness 与回归 gate 都可围绕统一 contract 推进。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`#64 / FR-0004` 的 formal spec 收口执行回合，负责把共享输入模型与采集策略模型入库到主干。
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

## 未决风险

- 若 formal spec 过拟合当前 URL-only detail 场景，后续共享模型会被迫回写 `FR-0004`。
- 若 `CollectionPolicy` 吞并后续 FR 的职责，implementation work item 会在无 formal spec 授权的情况下扩边界。
- 若事项上下文、active `exec-plan` 与受控入口字段不一致，PR 无法合法创建。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `FR-0004` formal spec 套件、索引更新与当前最小 exec-plan。

## 最近一次 checkpoint 对应的 head SHA

- `f9bf12ad92f6f9afab3d3761c7df8c8b48a07ef9`
