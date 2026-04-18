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
- 当前缺口只剩 same-path 端到端证据：需要把 `run`、legacy 平铺执行入口、shared store truth 与 `query` 回读结果绑定成同一条验证链。
- canonical worktree `issue-143-fr-0009-cli-core` 已登记到 `worktrees.json` 并承接当前执行回合；same-path 证据已在 PR `#157` 上进入 guardian 复审。
- 当前停点是 guardian 阻断修复已提交为 checkpoint `7c23eb02e20bbd8ad3b617c8d34cc61d3138611b`，并已重新通过本地回归；下一步是推送回 `#157` 并重跑 guardian / merge gate。

## 下一步动作

- 提交 guardian 修复后的 same-path evidence checkpoint，并推送到 PR `#157`。
- 更新 verification matrix 与 exec-plan 的证据口径，确保不再夸大 legacy/query round-trip 或 no-shadow-path 证明。
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
- `FR-0009` verification matrix 中 `scope owner=#143` 的 same-path 条目已全部回填到具体测试名，并在 guardian 阻断修复后重新验证通过。

## 未决风险

- 若继续把 legacy/query round-trip 当成 legacy/run durable-truth 等价性，会再次偏离 `FR-0009` formal spec 的冻结条款。
- 若 no-shadow-path 证据没有把额外文件系统咨询显式 fail-closed，后续 shadow payload 回归仍可能绕过 same-path closeout。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 same-path 证据测试、matrix 回填与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `7c23eb02e20bbd8ad3b617c8d34cc61d3138611b`
