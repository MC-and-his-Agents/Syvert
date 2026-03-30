# Syvert 文档工作流

本文档只定义 `docs/` 子树语义与交付工件职责。
根级约束以 [AGENTS.md](../AGENTS.md) 为准，运行契约以 [WORKFLOW.md](../WORKFLOW.md) 为准。

## 目录职责

- `docs/roadmap-v0-to-v1.md`：阶段目标与版本边界
- `docs/process/delivery-funnel.md`：唯一交付漏斗
- `docs/process/agent-loop.md`：长任务协议与恢复规则
- `docs/process/worktree-lifecycle.md`：worktree 生命周期规则
- `docs/process/branch-retirement.md`：分支归档与退役规则
- `docs/specs/`：正式规约区
- `docs/decisions/`：决策记录
- `docs/exec-plans/`：事项执行上下文、执行计划与恢复工件

## 术语与状态

- 事项上下文字段：`Issue` / `item_key` / `item_type` / `release` / `sprint`
- 事项类型：`FR` / `HOTFIX` / `GOV` / `CHORE`
- 事项术语：`轻量事项` / `中等事项` / `核心事项`
- 层次术语：`版本层` / `冲刺层` / `事项层`
- 成熟度术语：`spec-ready` / `implementation-ready` / `merge-ready`

## 层次职责

- `版本层`
  - 定义当前版本要证明的目标、边界与完成判据
- `冲刺层`
  - 定义当前执行轮次内事项的推进顺序、依赖关系与优先级
- `事项层`
  - 定义单事项的规约、执行上下文、恢复入口、验证与交付状态

本仓库当前不在 `docs/` 下维护 release / sprint 状态镜像；`release` 与 `sprint` 在 PR1 中只作为事项执行绑定字段存在。

## 正式规约区规则

`docs/specs/` 只承载正式规约，不承载 backlog 草稿。

- FR 目录命名：`FR-XXXX-<slug>`
- 最小套件：`spec.md`、`plan.md`、`TODO.md`
- `TODO.md` 可在实现 PR 回写进度，但不得修改正式契约语义
- 正式规约与实现默认分 PR；例外按 [spec_review.md](../spec_review.md) 执行
- `FR` 是事项类型之一；formal spec 可通过 `item_key` 与 `exec-plan`、decision、PR 关联

## 载体职责

- Issue：事项边界与关闭条件
- Project：状态、优先级、排期
- `spec.md`：需求、验收、异常与边界
- `plan.md`：实施拆分、依赖、验证、进入实现前条件
- `TODO.md`：事项级状态、执行停点、恢复入口、阻断项
- `exec-plan`：长任务执行细节、事项上下文与恢复上下文
- PR：变更范围、风险、验证证据、关闭语义，并显式映射回事项上下文

## 门禁关系

- 本地 hook：早反馈，不替代 CI
- CI：仓库门禁，不替代 guardian
- guardian：merge gate，不替代方向判断
