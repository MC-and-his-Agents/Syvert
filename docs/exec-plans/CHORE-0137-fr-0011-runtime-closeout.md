# CHORE-0137 执行计划

## 关联信息

- item_key：`CHORE-0137-fr-0011-runtime-closeout`
- Issue：`#183`
- item_type：`CHORE`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 spec：`docs/specs/FR-0011-task-bound-resource-tracing/`
- 关联 PR：`#184`
- active 收口事项：`CHORE-0137-fr-0011-runtime-closeout`

## 目标

- 为 `FR-0011` 落地 task-bound `ResourceTraceEvent`、独立 append-only trace store 与最小 usage-log 投影。
- 让 Core 在 `acquire / release` 成功路径上写入 canonical tracing truth，并把 tracing 读取能力收口到本地共享模块。
- 在不改写 `FR-0010` 生命周期主 contract 与 `FR-0012` adapter 边界的前提下，补齐 tracing 集成与回归验证。

## 范围

- 本次纳入：
  - `syvert/resource_trace.py`
  - `syvert/resource_trace_store.py`
  - `syvert/resource_lifecycle.py`
  - `syvert/resource_lifecycle_store.py`
  - `syvert/runtime.py`
  - `tests/runtime/test_resource_trace_store.py`
  - `tests/runtime/test_resource_lifecycle.py`
  - `tests/runtime/test_resource_lifecycle_store.py`
  - `tests/runtime/test_runtime.py`
  - `tests/runtime/resource_fixtures.py`
  - 当前 active `exec-plan`
- 本次不纳入：
  - CLI / UI 查询面
  - `FR-0010` formal spec 或生命周期主 contract 改写
  - `FR-0012` adapter 注入 contract 改写
  - 审计平台、报表与跨租户分析

## 当前停点

- 已创建 runtime Work Item `#183`，并通过 `python3 scripts/create_worktree.py --issue 183 --class implementation` 建立独立 worktree `/Users/mc/code/worktrees/syvert/issue-183-fr-0011`。
- 当前工作树已新增 tracing 共享模型、本地 trace store、`runtime/resource_lifecycle` 接线与首批 tracing 回归测试。
- 当前工作树已根据 guardian 的五轮阻断把 tracing 协调层继续收紧：`commit_with_trace` 与 fallback 路径统一为 `trace -> lifecycle` 锁顺序，避免 AB/BA 死锁；trace store 在 append/load/projection 三条路径上拒绝跨 task、跨 lease/bundle 身份漂移、不完整 resource timeline（缺失 acquired、双重收口）以及 `resource_type` / `adapter_key` / `capability` 漂移的非法事件流。

## 下一步动作

- 提交并推送第五轮 guardian 修复，刷新 `#184` merge gate。
- 等待 guardian / merge gate，并在合入后收口 `#183`、`#165`、`#173` 与 `v0.4.0` closeout truth sweep。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.4.0` 补齐“资源使用可以按任务追踪”的 runtime truth，使最小资源系统具备 task-bound tracing / usage log 的实现闭环。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0011` 的 implementation Work Item，负责把 formal spec 落地为 tracing truth 与最小投影能力。
- 阻塞：
  - 不得让 tracing 重写 `FR-0010` 生命周期主 contract。
  - 不得让 adapter 直接写 tracing truth 或自行来源化执行资源。
  - 不得因为独立 trace store 引入 runtime 并发死锁或影子 schema。

## 已验证项

- `gh issue create --title '工作项：实现 FR-0011 任务级资源追踪与使用日志' --body-file /tmp/fr0011_work_item_body.md`
  - 结果：已创建 Work Item `#183`
- `python3 scripts/create_worktree.py --issue 183 --class implementation`
  - 结果：已创建独立 worktree `/Users/mc/code/worktrees/syvert/issue-183-fr-0011`
- `python3 -m unittest -q tests.runtime.test_resource_trace_store`
  - 结果：通过（5 tests, OK）
- `python3 -m unittest -q tests.runtime.test_resource_lifecycle.ResourceLifecycleTests.test_acquire_retries_when_unrelated_write_advances_revision_without_changing_selection tests.runtime.test_resource_lifecycle.ResourceLifecycleTests.test_release_is_idempotent_under_concurrent_same_semantics tests.runtime.test_resource_lifecycle.ResourceLifecycleTests.test_release_rejects_concurrent_conflicting_semantics tests.runtime.test_resource_lifecycle.ResourceLifecycleTests.test_acquire_returns_failed_envelope_when_trace_write_fails`
  - 结果：通过（4 tests, OK）
- `python3 -m unittest -q tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_settles_success_without_hint_as_available tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_settles_failure_without_hint_as_available tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_applies_invalidating_hint_without_leaking_internal_field tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_releases_bundle_when_host_side_validation_fails_after_acquire`
  - 结果：通过（4 tests, OK）
- `python3 -m unittest -q tests.runtime.test_resource_trace_store tests.runtime.test_resource_lifecycle tests.runtime.test_runtime`
  - 结果：通过（98 tests, OK）
- `python3 -m unittest -q tests.runtime.test_resource_trace_store tests.runtime.test_resource_lifecycle tests.runtime.test_resource_lifecycle_store tests.runtime.test_runtime`
  - 结果：通过（141 tests, OK）
- `python3 -m unittest -q tests.runtime.test_cli tests.runtime.test_executor tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter tests.runtime.test_real_adapter_regression tests.runtime.test_version_gate`
  - 结果：通过（211 tests, OK）
- FR-0010 / FR-0012 边界核验（人工复核）
  - `syvert/resource_lifecycle_store.py` 仍只持久化 `ResourceLifecycleSnapshot`，`resource_trace` durable truth 独立落在 `syvert/resource_trace_store.py`，未把 tracing 字段混入 `FR-0010` snapshot/lease contract。
  - `syvert/runtime.py` 仍由 Core 统一 acquire / release / tracing；adapter 侧只消费 `resource_bundle` 并返回 `resource_disposition_hint`，未新增 tracing 写入口或资源来源入口。
  - `tests.runtime.test_resource_lifecycle`、`tests.runtime.test_runtime` 与 `tests.runtime.test_real_adapter_regression` 已覆盖 snapshot/revision 语义、host-side hint 收口和真实参考适配器回归，未观察到 `FR-0010` / `FR-0012` 漂移。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/open_pr.py --class implementation --issue 183 --item-key CHORE-0137-fr-0011-runtime-closeout --item-type CHORE --release v0.4.0 --sprint 2026-S17 --title 'feat(runtime): 落地 FR-0011 任务级资源追踪与使用日志' --closing fixes --dry-run`
  - 结果：通过
- `python3 scripts/open_pr.py --class implementation --issue 183 --item-key CHORE-0137-fr-0011-runtime-closeout --item-type CHORE --release v0.4.0 --sprint 2026-S17 --title 'feat(runtime): 落地 FR-0011 任务级资源追踪与使用日志' --closing fixes`
  - 结果：已创建 PR `#184`

## 未决风险

- 独立 trace store 当前仍不是跨文件硬事务；默认本地 store 已通过 lifecycle 锁内双写补偿收口主路径，但若未来要扩展到更复杂 backend，仍需要新的 store / backend contract 明确冻结。

## 回滚方式

- 使用独立 revert PR 撤销 tracing 模块、store、runtime 接线、相关测试与本 exec-plan。

## 最近一次 checkpoint 对应的 head SHA

- `6728f23b2511c5c5d229fe4b98cfbac1728f2366`
