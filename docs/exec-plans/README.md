# Syvert 执行计划区

本目录用于承载跨多轮任务的事项执行上下文、执行计划、恢复入口和阶段性交付工件。

## 最小元数据要求

- 任一 `长任务` 的 `exec-plan` 至少记录以下字段：
  - `Issue`
  - `item_key`
  - `item_type`
  - `release`
  - `sprint`
  - 当前 checkpoint 推进的 `release` 目标
  - 当前事项在 `sprint` 中的角色 / 阻塞关系
  - 已验证项
  - 未决风险
  - 最近一次 checkpoint 对应的 head SHA
- `存量事项` 在进入新的执行回合前补齐上述字段。
- `exec-plan` 中的 head SHA 用于恢复最近一次 checkpoint，不替代 guardian 对当前受审 head SHA 的绑定与 merge gate 校验。
- 若当前 PR 在最近一次 checkpoint 之后仍有跟进 commit，但尚未形成新的 checkpoint，可保留最近一次 checkpoint head，并由 guardian state 绑定当前受审 head。
- review 结论、GitHub checks、PR 关联与索引入口的更新，只要未显式推进新的执行停点，就属于审查态元数据补充，不要求单独刷新 checkpoint head。

## 职责边界

- `Issue` 仍是任务状态真相源入口。
- `item_key`、`release`、`sprint` 是执行绑定字段，不替代 GitHub Issues / Projects。
- `exec-plan` 负责记录长任务执行细节、事项上下文、停点、下一步、风险与恢复入口。
- `exec-plan` 在进入 review 前必须更新到可恢复状态，至少覆盖最近一次 checkpoint head、已验证项、未决风险与 checkpoint 语义。
- `exec-plan` 不是 sprint 状态面，不承担 backlog 或 sprint 镜像职责。
- `长任务`、`新事项`、`存量事项` 的判定以 [WORKFLOW.md](../../WORKFLOW.md) 与 [docs/AGENTS.md](../AGENTS.md) 为准。

## 命名与模板

- 从 PR2 起，新事项默认使用 `<item_key>.md` 命名。
- 历史文件允许保留旧文件名，不要求在 PR2 一次性重命名。
- 新增事项优先从 [./_template.md](./_template.md) 复制。
- 历史事项若需要补充 `item_key`、`release`、`sprint` 关联，可在不重命名文件的前提下增量补齐。

## 聚合而不嵌套

- 不采用“每个事项目录中混放 `spec`、`exec-plan`、`decision`”的物理嵌套方案。
- 继续使用“按工件类型分区、按绑定关系逻辑聚合”的模型：formal spec 使用 FR `item_key`，active `exec-plan` 使用当前 Work Item `item_key`。
- `docs/releases/` 与 `docs/sprints/` 只作为横向索引层，不替代 GitHub Issues / Projects。

## 示例链路

- formal spec：`docs/specs/FR-XXXX-<slug>/spec.md`
- exec-plan：`docs/exec-plans/<item_key>.md`
- 绑定关系：formal spec 绑定 FR `item_key`，exec-plan 绑定当前 Work Item `item_key`
- 目标：通过 FR / Work Item 绑定关系，以及 `Issue`、`release`、`sprint` 串起规约、恢复工件与 PR
