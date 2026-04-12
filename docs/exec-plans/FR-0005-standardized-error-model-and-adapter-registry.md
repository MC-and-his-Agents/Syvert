# FR-0005-standardized-error-model-and-adapter-registry 执行计划

## 关联信息

- item_key：`FR-0005-standardized-error-model-and-adapter-registry`
- Issue：`#65`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`FR-0005-standardized-error-model-and-adapter-registry`

## 目标

- 为父事项 `#65` 建立可审查、可合并、可追溯的 formal spec 套件，冻结错误模型与 adapter registry 的 requirement、边界与验收语义。
- 把 `#69` 与 `#70` 收敛为后续独立实现 Work Item，而不是让当前 formal spec PR 提前进入实现回合。

## 范围

- 本次纳入：
  - `docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`
  - `docs/exec-plans/FR-0005-standardized-error-model-and-adapter-registry.md`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
- 本次不纳入：
  - Core / Adapter 实现改动
  - harness、fake adapter、gate 或 validator 设计细节
  - `src/**`、`scripts/**`、`tests/**` 的运行时改造

## 当前停点

- GitHub `#65` 已明确当前 FR 只要求 formal spec 收口，并把 `#69`、`#70` 指定为下游 Work Item。
- 仓库主干尚不存在 `docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`，当前 formal spec 入口仍待创建。
- 当前执行现场为独立 worktree：`/Users/mc/code/worktrees/syvert/issue-65-fr-0005-v0-2-0`。

## 下一步动作

- 起草 `FR-0005` 的 `spec.md`、`plan.md`、`risks.md` 与 `contracts/README.md`。
- 运行 formal spec 相关门禁，并通过受控入口创建 `spec` PR。
- 等待 checks 全绿后执行 guardian；若存在阻断，只修当前 head 的最新阻断项。
- 合并后同步 `#65` 的 formal spec 入口，保持 GitHub 与主干真相一致。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 冻结“标准化错误模型 + adapter registry”这一共享契约，使后续 harness、validator 与版本 gate 能围绕统一失败语义与统一 adapter 发现语义展开。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`v0.2.0` formal spec 主线事项。
- 阻塞：
  - 无外部阻塞；当前主要工作是 formal spec 收口、受控 PR、guardian 与 merge gate。

## 已验证项

- `gh issue view 65`
  - 结果：`FR-0005` 为 `v0.2.0` FR 容器，formal spec 待创建，子 Work Item 为 `#69`、`#70`
- `gh issue view 69`
  - 结果：`#69` 为“实现标准化错误模型”的后续 Work Item
- `gh issue view 70`
  - 结果：`#70` 为“实现适配器注册表”的后续 Work Item
- `gh issue view 64`
  - 结果：`FR-0004` 负责 `InputTarget` 与 `CollectionPolicy`
- `gh issue view 66`
  - 结果：`FR-0006` 负责 adapter contract test harness
- `gh issue view 67`
  - 结果：`FR-0007` 负责版本 gate 与回归检查
- 已阅读：`vision.md`
- 已阅读：`docs/roadmap-v0-to-v1.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`spec_review.md`
- 已阅读：`docs/releases/v0.2.0.md`

## 未决风险

- 若 formal spec 没有把 `invalid_input`、`unsupported`、`runtime_contract` 与 `platform` 拆开，`#69` 将难以形成稳定实现边界。
- 若 registry 被写成带平台副作用的发现机制，`FR-0006` 的 fake adapter / harness 将无法建立稳定入口。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`、`docs/exec-plans/FR-0005-standardized-error-model-and-adapter-registry.md`、`docs/releases/v0.2.0.md` 与 `docs/sprints/2026-S15.md` 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `f9bf12ad92f6f9afab3d3761c7df8c8b48a07ef9`
- 说明：当前为 formal spec kickoff 停点；后续如只补充 checks / guardian / merge gate 元数据，可由 guardian state 绑定当前受审 head。
