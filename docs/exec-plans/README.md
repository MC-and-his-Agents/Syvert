# Syvert 执行计划区

本目录用于承载跨多轮任务的事项执行上下文、执行计划、恢复入口和阶段性交付工件。

## 最小元数据要求

- 任一 `长任务` 的 `exec-plan` 至少记录以下字段：
  - `Issue`
  - `item_key`
  - `item_type`
  - `release`
  - `sprint`
- `存量事项` 在进入新的执行回合前补齐上述字段。

## 职责边界

- `Issue` 仍是任务状态真相源入口。
- `item_key`、`release`、`sprint` 是执行绑定字段，不替代 GitHub Issues / Projects。
- `exec-plan` 负责记录长任务执行细节、事项上下文、停点、下一步、风险与恢复入口。
- `exec-plan` 不是 sprint 状态面，不承担 backlog 或 sprint 镜像职责。
- `长任务`、`新事项`、`存量事项` 的判定以 [WORKFLOW.md](../../WORKFLOW.md) 与 [docs/AGENTS.md](../AGENTS.md) 为准。

## 命名与模板

- 从 PR2 起，新事项默认使用 `<item_key>.md` 命名。
- 历史文件允许保留旧文件名，不要求在 PR2 一次性重命名。
- 新增事项优先从 [./_template.md](./_template.md) 复制。
- 历史事项若需要补充 `item_key`、`release`、`sprint` 关联，可在不重命名文件的前提下增量补齐。

## 聚合而不嵌套

- 不采用“每个事项目录中混放 `spec`、`exec-plan`、`decision`”的物理嵌套方案。
- 继续使用“按工件类型分区、按 `item_key` 逻辑聚合”的模型。
- `docs/releases/` 与 `docs/sprints/` 只作为横向索引层，不替代 GitHub Issues / Projects。

## 示例链路

- `item_key`：`FR-0001-governance-stack-v1`
- formal spec：`docs/specs/FR-0001-governance-stack-v1/spec.md`
- TODO：`docs/specs/FR-0001-governance-stack-v1/TODO.md`
- exec-plan：`docs/exec-plans/governance-stack-v1.md`
- release：`v0.1.0`
- sprint：`2026-S13`
