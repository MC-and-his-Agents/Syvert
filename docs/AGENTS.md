# Syvert 文档工作流

本文档只定义 `docs/` 子树语义与交付工件职责。
根级约束以 [AGENTS.md](../AGENTS.md) 为准，运行契约以 [WORKFLOW.md](../WORKFLOW.md) 为准。

## 目录职责

- `docs/roadmap-v0-to-v1.md`：阶段目标与版本边界
- `docs/process/delivery-funnel.md`：唯一交付漏斗
- `docs/process/agent-loop.md`：长任务协议与恢复规则
- `docs/process/worktree-lifecycle.md`：worktree 生命周期规则
- `docs/specs/`：正式规约区
- `docs/decisions/`：决策记录
- `docs/exec-plans/`：执行计划与恢复工件

## 术语与状态

- 事项术语：`轻量事项` / `中等事项` / `核心事项`
- 成熟度术语：`spec-ready` / `implementation-ready` / `merge-ready`

## 正式规约区规则

`docs/specs/` 只承载正式规约，不承载 backlog 草稿。

- FR 目录命名：`FR-XXXX-<slug>`
- 最小套件：`spec.md`、`plan.md`、`TODO.md`
- `TODO.md` 可在实现 PR 回写进度，但不得修改正式契约语义
- 正式规约与实现默认分 PR；例外按 [spec_review.md](../spec_review.md) 执行

## 载体职责

- Issue：事项边界与关闭条件
- Project：状态、优先级、排期
- `spec.md`：需求、验收、异常与边界
- `plan.md`：实施拆分、依赖、验证、进入实现前条件
- `TODO.md`：执行停点、恢复入口、阻断项
- PR：变更范围、风险、验证证据、关闭语义

## 门禁关系

- 本地 hook：早反馈，不替代 CI
- CI：仓库门禁，不替代 guardian
- guardian：merge gate，不替代方向判断
