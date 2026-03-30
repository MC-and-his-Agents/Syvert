# Syvert 执行计划区

本目录用于承载跨多轮任务的事项执行上下文、执行计划、恢复入口和阶段性交付工件。

## 最小建议元数据

新的长任务执行计划建议至少记录：

- `issue`
- `item_key`
- `item_type`
- `release`
- `sprint`

## 职责边界

- `Issue` 仍是任务状态真相源入口
- `item_key`、`release`、`sprint` 是执行绑定字段，不替代 GitHub Issues / Projects
- `exec-plan` 负责记录长任务执行细节、事项上下文、停点、下一步、风险与恢复入口
- `exec-plan` 不是 sprint 状态面，不承担 backlog 或 sprint 镜像职责
