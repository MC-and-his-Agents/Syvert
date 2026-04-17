# CHORE-0123 执行计划

## 关联信息

- item_key：`CHORE-0123-fr-0008-task-record-model`
- Issue：`#138`
- item_type：`CHORE`
- release：`v0.3.0`
- sprint：`2026-S16`
- 关联 spec：`docs/specs/FR-0008-task-record-persistence/`
- 关联 PR：
- active 收口事项：`CHORE-0123-fr-0008-task-record-model`

## 目标

- 在 `FR-0008` 范围内把任务状态、终态结果与执行日志的共享模型落地到 runtime 主路径。
- 提供 JSON-safe 的任务记录序列化 / 回读能力，为 `#139` 的本地持久化管线提供稳定输入。
- 保持现有 `execute_task()` success / failed envelope 行为不变，不提前引入本地存储或 CLI 查询 surface。

## 范围

- 本次纳入：
  - `syvert/runtime.py`
  - `syvert/task_record.py`
  - `tests/runtime/test_task_record.py`
  - 视需要最小调整 `tests/runtime/test_runtime.py` / `tests/runtime/test_executor.py`
  - 当前 active `exec-plan`
- 本次不纳入：
  - 本地稳定存储写入 / 回读实现
  - CLI 查询命令或输出格式改造
  - `scripts/**` 治理工具链
  - `#139` 的持久化收口

## 当前停点

- `FR-0008` formal spec 已由 PR `#145` 合入主干，当前实现入口切到真实 Work Item `#138`。
- 当前 runtime 仍只返回 success / failed envelope，尚未在共享主路径中构建可回读的 `TaskRecord` 聚合。
- 现有 pre-accepted 失败（invalid request / unsupported capability / unsupported target_type / unsupported collection_mode / registry failure 等）必须继续停留在 durable task history 边界之外。

## 下一步动作

- 落地 `TaskRecord` / `TaskRequestSnapshot` / `TaskTerminalResult` / `TaskLogEntry` 模型与 JSON-safe 序列化函数。
- 在 runtime 中补出 accepted/running/terminal 三段共享生命周期，并保持 `execute_task()` 对外 envelope 不漂移。
- 运行 runtime 测试、受控入口 dry-run、推送并创建 implementation PR。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.3.0` 提供可被持久化层直接消费的共享任务记录模型，使后续 `#139` 只需解决本地存储管线，而不再重新定义状态/结果/日志语义。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0008` 的模型层 implementation Work Item，负责把 formal spec 里的共享 task record contract 实际落到 runtime。
- 阻塞：
  - 必须守住 `FR-0008` 规定的 pre-`accepted` / post-`accepted` 边界，不把 admission/pre-execution 失败误写入 durable history。
  - 不得让 runtime 依赖 `scripts/*` 或治理状态文件。

## 已验证项

- `gh issue view 138 --json number,title,body,state,projectItems,url`
- `sed -n '1,260p' docs/specs/FR-0008-task-record-persistence/spec.md`
- `sed -n '1,220p' docs/specs/FR-0008-task-record-persistence/data-model.md`
- `sed -n '1,260p' syvert/runtime.py`
- `sed -n '1,260p' tests/runtime/test_runtime.py`
- `sed -n '1,220p' tests/runtime/test_models.py`
- `sed -n '1,240p' tests/runtime/test_executor.py`
- `python3 scripts/create_worktree.py --issue 138 --class implementation`
  - 结果：已创建独立 worktree `/Users/mc/code/worktrees/syvert/issue-138-fr-0008`

## 未决风险

- 若 `TaskRecord` 模型与既有 envelope 语义漂移，`#139` 和 `FR-0009` 会被迫建立影子 schema。
- 若 accepted 建档时点放得过早，会把上游 `FR-0004` / `FR-0005` 已冻结的 pre-execution 失败错误纳入 durable history。

## 回滚方式

- 使用独立 revert PR 撤销 `TaskRecord` 模型、runtime 生命周期接线与对应测试。

## 最近一次 checkpoint 对应的 head SHA

- `093141b5dfbde9d5912963fe72497081334bc6bd`
