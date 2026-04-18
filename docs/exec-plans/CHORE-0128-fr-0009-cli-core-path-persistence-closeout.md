# CHORE-0128-fr-0009-cli-core-path-persistence-closeout 执行计划

## 关联信息

- item_key：`CHORE-0128-fr-0009-cli-core-path-persistence-closeout`
- Issue：`#143`
- item_type：`CHORE`
- release：`v0.3.0`
- sprint：`2026-S16`
- 关联 spec：`docs/specs/FR-0009-cli-task-query-and-core-path/`
- 状态：`active`
- active 收口事项：`CHORE-0128-fr-0009-cli-core-path-persistence-closeout`

## 目标

- 在不重开 `FR-0009` query public surface 的前提下，收口 `run/legacy-run -> durable record -> query` 的 same-path 闭环证据，并证明 query 只消费共享 `TaskRecord` durable truth。

## 范围

- 本次纳入：
  - `docs/exec-plans/CHORE-0128-fr-0009-cli-core-path-persistence-closeout.md`
  - `docs/exec-plans/artifacts/FR-0009-cli-query-and-core-path-verification-matrix.md`
  - `tests/runtime/test_cli.py`
- 本次不纳入：
  - `syvert/cli.py` public surface 或错误 contract 改写
  - `FR-0009` formal spec 目录
  - `#144` parent closeout 工件

## 当前停点

- `#142 / PR #156` 已于 2026-04-18 合入主干，`run/query` public surface、query 错误 contract 与 verification matrix carrier 已成为主干真相。
- canonical worktree `issue-143-fr-0009-cli-core` 已登记到 `worktrees.json` 并承接当前执行回合；same-path 证据在 PR `#157` 上进入 guardian 后，于 2026-04-19 再次收到 `REQUEST_CHANGES`。
- 本轮 guardian 阻断不是新 contract，而是两条 `scope owner=#143` 证据仍然不够判别式：
  - legacy 平铺执行入口与 `run` 子命令的 durable truth 等价性，只比较了 `request/status/result`，没有覆盖 `created_at/updated_at/terminal_at/logs`
  - `query` 无 shadow payload / secondary filesystem consultation 的证明仍过度依赖狭窄 mock success path
- 当前停点是把这两条 finding 回填到 verification matrix 和本 exec-plan，再补强同路径证据测试后重跑 guardian / merge gate。

## 下一步动作

- 更新 verification matrix 与 exec-plan 的证据口径，确保 `#143` 只声明已被判别式测试覆盖的 same-path 条目。
- 补强 legacy/run durable truth 等价性测试，仅规范化真正易变的 task_id 与时间字段，并比较完整 persisted `TaskRecord` JSON-safe 载荷。
- 补强 `query` success path regression，使 `load() + task_record_to_dict()` 之外的 secondary filesystem consultation 在测试中直接失败。
- 在当前 head 上重跑 guardian / merge gate，合入后再切换到 `#144` parent closeout。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.3.0` 把“CLI 查询任务状态/结果”与“CLI 仍走同一条 Core 执行路径”收敛成同一条可验证证据链。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0009` 的 same-path closeout Work Item。
- 阻塞：
  - `#144` 必须等待本事项合入主干后再进入 parent closeout。

## 已验证项

- 已核对 `#142 / PR #156` 已合入主干，并把 query contract、verification matrix 与 `CHORE-0127` 收口到仓内真相。
- 已核对当前主干上的 `tests/runtime/test_cli.py` 已剔除 same-path 证明类测试，避免与 `#142` 边界重叠。
- `python3 -m unittest tests.runtime.test_cli tests.runtime.test_task_record tests.runtime.test_task_record_store`
  - 结果：通过（68 tests, OK）
- `python3 -m unittest tests.runtime.test_xhs_adapter.XhsAdapterTests.test_cli_module_path_can_load_xhs_adapter_from_shared_registry`
  - 结果：通过（1 test, OK）
- `FR-0009` verification matrix 中 `scope owner=#143` 的 same-path 条目已全部回填到具体测试名；本轮 guardian finding 已回映到对应条目的 clause/test 口径，避免继续把宽泛成功路径当成完成证据。

## 未决风险

- 若继续把 legacy/query round-trip 当成 legacy/run durable-truth 等价性，会再次偏离 `FR-0009` formal spec 的冻结条款。
- 若 no-shadow-path 证据没有把额外文件系统咨询显式击穿，后续 shadow payload / secondary history source 回归仍可能绕过 same-path closeout。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 same-path 证据测试、matrix 回填与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `1e482af26edbf638baa9339dcb37015a2162b5bb`
