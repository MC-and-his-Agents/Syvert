# CHORE-0137 执行计划

## 关联信息

- item_key：`CHORE-0137-fr-0011-runtime-closeout`
- Issue：`#183`
- item_type：`CHORE`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 spec：`docs/specs/FR-0011-task-bound-resource-tracing/`
- 关联 PR：
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
  - `syvert/runtime.py`
  - `tests/runtime/test_resource_trace_store.py`
  - `tests/runtime/test_resource_lifecycle.py`
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
- 当前实现将 tracing truth 绑定到 lifecycle 提交后的同一 host-side 协调入口，优先保证主路径不发生并发死锁；后续如需更强的跨 store 原子性，需要新的 formal spec 或 backend 事务语义支撑。

## 下一步动作

- 跑通 `FR-0011` 相关 runtime / lifecycle / trace store 回归，并收掉失败分类或并发语义问题。
- 补 `pr_scope_guard`、`open_pr --dry-run` 与需要的治理门禁。
- 创建 implementation PR，等待 guardian / merge gate，然后收口 `#183`、`#165`、`#173` 的 GitHub 真相。

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

## 未决风险

- 独立 trace store 当前没有跨文件事务；若未来要把 lifecycle truth 与 trace truth 做到更强原子性，需要新的 store / backend contract。
- tracing 失败当前会 fail-closed 返回错误，但若失败发生在 lifecycle durable truth 提交之后，仍可能留下“状态已切换但 trace 缺席”的局部异常，需要后续更强 backend 语义收口。
- 需要在更大回归面上确认 `FR-0010` / `FR-0012` 既有 contract 没有被 tracing 接线误伤。

## 回滚方式

- 使用独立 revert PR 撤销 tracing 模块、store、runtime 接线、相关测试与本 exec-plan。

## 最近一次 checkpoint 对应的 head SHA

- `b004b73da8a30c898200b497c94d351013154612`
