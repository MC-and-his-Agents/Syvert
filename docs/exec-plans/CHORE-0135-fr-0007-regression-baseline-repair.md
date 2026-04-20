# CHORE-0135 执行计划

## 关联信息

- item_key：`CHORE-0135-fr-0007-regression-baseline-repair`
- Issue：`#179`
- item_type：`CHORE`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 spec：`docs/specs/FR-0007-release-gate-and-regression-checks/`
- 关联 decision：
- 关联 PR：`#180`
- active 收口事项：`CHORE-0135-fr-0007-regression-baseline-repair`

## 目标

- 修复 `platform_leakage` 对 `execute_task()` success / failure return path 的边界归类漂移。
- 修复 `tests.runtime.test_real_adapter_regression` 中 platform leakage payload 与 `version_gate` canonical evidence refs 不一致的问题。
- 在不修改 formal spec、不放宽 `version_gate` validator 的前提下，消除主干既有 3 个失败。

## 范围

- 本次纳入：
  - `syvert/platform_leakage.py`
  - `tests/runtime/test_platform_leakage.py`
  - `tests/runtime/test_real_adapter_regression.py`
  - `tests/runtime/test_version_gate.py`
  - `tests/runtime/platform_leakage_fixtures.py`
  - 当前 active `exec-plan`
- 本次不纳入：
  - `FR-0010` / `FR-0011` / `FR-0012`
  - `syvert/version_gate.py` contract 放宽
  - CLI / adapter runtime surface 变更
  - formal spec 改写

## 当前停点

- 当前执行现场：`/Users/mc/code/worktrees/syvert/issue-179-fr-0007`
- 当前执行分支：`issue-179-fr-0007`
- 当前受审 PR：`#180`
- 基线 head：`2c71a6d1be6eb965198cd984f2bcb17439ae6a02`
- 当前实现 checkpoint：`cb5eaadbeff4cd3efa9a8f235cb72ef6297ddc85`
- 当前代码已收口两类修复：
  - `syvert/platform_leakage.py` 对 `execute_task` / `execute_task_internal` 内 success envelope dict 与 `failure_envelope(...)` 语句值做 statement-level boundary override，success 归 `shared_result_contract`、failure 归 `shared_error_model`。
  - `tests/runtime/platform_leakage_fixtures.py` 已成为 canonical platform leakage payload 的单一测试真相源，`test_version_gate` 与 `test_real_adapter_regression` 已去除漂移副本。

## 下一步动作

- 运行 `pr_scope_guard` 与 `open_pr --dry-run`，确认 implementation PR carrier 干净。
- 推送当前分支并创建 PR。
- 提交 reviewer / guardian，若未获 `APPROVE`，优先做同类阻断复盘而不是逐条被动补丁。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.4.0` 清理 FR-0007 历史回归噪音，恢复版本门禁与平台泄漏检查的主干测试真相。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：清理主干既有回归噪音，恢复 FR-0007 相关 gate 的可信基线。
- 阻塞：待 PR、review、guardian 与 merge gate 收口。

## 已验证项

- `gh issue create` 已创建 Work Item `#179`
- `python3 scripts/create_worktree.py --issue 179 --class implementation`
  - 结果：已创建 worktree `/Users/mc/code/worktrees/syvert/issue-179-fr-0007`
- `python3 -m unittest -q tests.runtime.test_platform_leakage.PlatformLeakageTests.test_run_check_maps_success_envelope_leak_to_shared_result_contract tests.runtime.test_platform_leakage.PlatformLeakageTests.test_run_check_maps_exception_failure_return_to_shared_error_model tests.runtime.test_platform_leakage.PlatformLeakageTests.test_run_check_keeps_non_envelope_execute_task_statement_in_core_runtime tests.runtime.test_real_adapter_regression.RealAdapterRegressionTests.test_end_to_end_real_adapter_regression_report_feeds_version_gate`
  - 结果：`Ran 4 tests in 24.822s`，`OK`
- `python3 -m unittest -q tests.runtime.test_executor tests.runtime.test_runtime tests.runtime.test_registry`
  - 结果：`Ran 48 tests in 0.020s`，`OK`
- `python3 -m unittest -q tests.runtime.test_real_adapter_regression`
  - 结果：`Ran 20 tests in 0.185s`，`OK`
- `python3 -m unittest -q tests.runtime.test_version_gate`
  - 结果：`Ran 99 tests in 30.849s`，`OK`
- `python3 -m unittest -q tests.runtime.test_platform_leakage`
  - 结果：`Ran 111 tests in 775.039s`，`OK (skipped=6)`
- `python3 -m unittest -q tests.runtime.test_platform_leakage tests.runtime.test_version_gate tests.runtime.test_real_adapter_regression`
  - 结果：`Ran 229 tests in 823.275s`，`OK (skipped=6)`
- `python3 -m py_compile syvert/platform_leakage.py tests/runtime/test_platform_leakage.py tests/runtime/platform_leakage_fixtures.py tests/runtime/test_real_adapter_regression.py tests/runtime/test_version_gate.py`
  - 结果：通过

## 未决风险

- `tests.runtime.test_platform_leakage` 全量回归耗时较长；后续 guardian / closeout 需要避免把该慢用例误判为卡死。
- 当前实现只修复 FR-0007 历史回归噪音，不触碰 formal spec 与 `version_gate` validator；后续若发现新的 evidence drift，应继续向共享 fixture 收敛，而不是放宽 contract。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对应的实现与测试调整。

## 最近一次 checkpoint 对应的 head SHA

- `cb5eaadbeff4cd3efa9a8f235cb72ef6297ddc85`
- 当前回合已进入 `metadata-only closeout follow-up`；后续 PR / review / merge gate 元数据同步不要求该 checkpoint SHA 与最新 HEAD 完全一致。
