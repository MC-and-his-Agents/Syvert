# FR-0009 执行计划（requirement container）

## 关联信息

- item_key：`FR-0009-cli-task-query-and-core-path`
- Issue：`#128`
- item_type：`FR`
- release：`v0.3.0`
- sprint：`2026-S16`
- 关联 spec：`docs/specs/FR-0009-cli-task-query-and-core-path/`
- 状态：`inactive requirement container`

## 说明

- `FR-0009` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- `#141` 负责冻结 `FR-0009` formal spec 套件；`#142` 负责 CLI query public surface；`#143` 负责同路径闭环与端到端证据；`#144` 负责父事项 closeout。
- `FR-0009` 只消费 `FR-0008` 已冻结的 durable `TaskRecord` contract，不新增影子 schema、影子结果文件或 query 私有持久化 truth。

## 最近一次 checkpoint 对应的 head SHA

- 本地实现准备 checkpoint：`36a7db38b3ff0f37d91dfc4090b3d86dc1c3318c`
- 说明：当前 requirement container 首次把 `FR-0009` 的 spec 路径、Work Item 拆分与 release / sprint 索引落盘；后续由 `#141/#142/#143/#144` 各自的 exec-plan 记录独立执行事实。
