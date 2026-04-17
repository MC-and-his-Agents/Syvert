# CHORE-0124 执行计划

## 关联信息

- item_key：`CHORE-0124-fr-0008-local-persistence-and-serialization`
- Issue：`#139`
- item_type：`CHORE`
- release：`v0.3.0`
- sprint：`2026-S16`
- 关联 spec：`docs/specs/FR-0008-task-record-persistence/`
- 关联 PR：`#148`
- active 收口事项：`CHORE-0124-fr-0008-local-persistence-and-serialization`

## 目标

- 在不改写 `#138` 已冻结共享模型的前提下，为 `TaskRecord` 落地最小本地稳定存储与共享序列化管线。
- 让 Core 内部主路径可以在 `accepted` / `running` / `succeeded|failed` 三个阶段把同一条 `TaskRecord` durable 写入本地存储。
- 保持 `FR-0009` 的 CLI 查询与同路径执行闭环留在后续 Work Item，不在当前 PR 提前展开查询 surface。

## 范围

- 本次纳入：
  - `syvert/task_record_store.py`
  - `syvert/runtime.py`
  - `tests/runtime/test_task_record_store.py`
  - 视需要最小补充 `tests/runtime/test_task_record.py`
  - 当前 active `exec-plan`
- 本次不纳入：
  - CLI 查询命令与输出格式
  - 旁路结果文件或 `scripts/*` 状态路径
  - 远程存储、嵌入式数据库、索引层
  - `#143` 的 CLI/Core 同路径执行闭环

## 当前停点

- `#138` 已通过 PR `#147` 把共享 `TaskRecord` 模型与 runtime 生命周期接线合入主干。
- 当前分支已把 `LocalTaskRecordStore`、runtime durable 接线与回归测试落到 worktree，并通过当前受审 PR `#148` 进入 implementation 审查。
- 当前受审 head 为 `157c377eacb118884d8b92a257c2cdba1533b4d2`，已把 accepted / running / completion 三段 durable 写入、冲突/无效化处理、accepted/running 幂等重放与默认本地 store 路径接入到 `execute_task_with_record()`。

## 下一步动作

- 新增 runtime 侧本地 `TaskRecordStore`，负责 `TaskRecord` 的 JSON-safe 落盘、回读与幂等/冲突校验。
- 在 `execute_task_with_record()` 中接入 accepted/running/terminal 三次 durable 写入，并在持久化失败时 fail-closed。
- 通过单元测试证明：accepted 写入失败不会触发 adapter 执行；success / failed 任务都可从稳定存储回读；冲突写入保持 fail-closed。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.3.0` 建立可被后续 `FR-0009` 查询层直接消费的本地 durable task record truth，而不是继续停留在单进程内存对象。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0008` 的持久化实现 Work Item，负责把 `#138` 的共享模型落到最小本地稳定存储。
- 阻塞：
  - 不能让 runtime 依赖 `scripts/state_paths.py` 或其他治理层路径助手。
  - 不能把 `#139` 扩张成 CLI 查询或 `#143` 的同路径执行改造。

## 已验证项

- `gh issue view 139 --json number,title,body,state,projectItems,url`
- `sed -n '1,240p' docs/specs/FR-0008-task-record-persistence/spec.md`
- `sed -n '1,220p' docs/specs/FR-0008-task-record-persistence/data-model.md`
- `sed -n '1,260p' syvert/runtime.py`
- `sed -n '1,260p' syvert/task_record.py`
- `python3 scripts/create_worktree.py --issue 139 --class implementation`
  - 结果：已创建独立 worktree `/Users/mc/code/worktrees/syvert/issue-139-fr-0008`
- `python3 scripts/open_pr.py --class implementation --issue 139 --item-key CHORE-0124-fr-0008-local-persistence-and-serialization --item-type CHORE --release v0.3.0 --sprint 2026-S16 --title 'feat(runtime): 落地 FR-0008 本地任务记录持久化' --closing fixes --dry-run`
  - 结果：通过；当前受审 PR 为 `#148 https://github.com/MC-and-his-Agents/Syvert/pull/148`
- `python3 -m unittest tests.runtime.test_task_record_store tests.runtime.test_task_record tests.runtime.test_runtime tests.runtime.test_executor tests.runtime.test_models tests.runtime.test_cli`
  - 结果：在当前受审 head `157c377eacb118884d8b92a257c2cdba1533b4d2` 上通过，覆盖 accepted/running/terminal 持久化与幂等回归
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
  - 结果：在当前受审 head `157c377eacb118884d8b92a257c2cdba1533b4d2` 上通过
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：在当前受审 head `157c377eacb118884d8b92a257c2cdba1533b4d2` 上通过
- `python3 scripts/governance_gate.py --mode ci --base-sha $(git merge-base origin/main HEAD) --head-sha $(git rev-parse HEAD) --head-ref issue-139-fr-0008`
  - 结果：在当前受审 head `157c377eacb118884d8b92a257c2cdba1533b4d2` 上通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：在当前受审 head `157c377eacb118884d8b92a257c2cdba1533b4d2` 上通过
- `python3 scripts/spec_guard.py --mode ci --base-sha $(git merge-base origin/main HEAD) --head-sha $(git rev-parse HEAD)`
  - 结果：在当前受审 head `157c377eacb118884d8b92a257c2cdba1533b4d2` 上通过

## 未决风险

- 若持久化路径直接绑定到 CLI 或 `scripts/*`，会破坏 `FR-0008` 对 Core-only durable truth 的边界。
- 若终态写入失败仍把任务暴露为 success / completed history，会违反 fail-closed contract。

## 回滚方式

- 使用独立 revert PR 撤销本地 `TaskRecordStore`、runtime durable 接线与对应测试。

## 最近一次 checkpoint 对应的 head SHA

- 当前受审 head：`157c377eacb118884d8b92a257c2cdba1533b4d2`
- 说明：该 head 已绑定当前 implementation PR `#148`，并补齐 accepted / running / completion durable 写入、accepted/running 幂等重放、失效标记与 running-at-adapter-boundary 回归测试的最新事实。
