# CHORE-0135 执行计划

## 关联信息

- item_key：`CHORE-0135-fr-0007-regression-baseline-repair`
- Issue：`#179`
- item_type：`CHORE`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 spec：`docs/specs/FR-0007-release-gate-and-regression-checks/`
- 关联 decision：
- 关联 PR：
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
- 基线 head：`2c71a6d1be6eb965198cd984f2bcb17439ae6a02`
- 已确认主干存在 3 个既有失败：
  - `tests.runtime.test_platform_leakage.PlatformLeakageTests.test_run_check_maps_success_envelope_leak_to_shared_result_contract`
  - `tests.runtime.test_platform_leakage.PlatformLeakageTests.test_run_check_maps_exception_failure_return_to_shared_error_model`
  - `tests.runtime.test_real_adapter_regression.RealAdapterRegressionTests.test_end_to_end_real_adapter_regression_report_feeds_version_gate`
- 已确认第三项失败的真实根因是测试 payload 漂移，而不是 `real_adapter_regression` 逻辑回归。

## 下一步动作

- 为 `execute_task()` 构建语句级 boundary override，并补针对 return dict / failure envelope 参数行的回归。
- 抽出共享 platform leakage payload fixture，统一 `test_version_gate` 与 `test_real_adapter_regression` 的 canonical evidence refs。
- 先跑 3 个既有失败用例，再跑 `platform_leakage / version_gate / real_adapter_regression` 与 executor/runtime/registry 回归收口。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.4.0` 清理 FR-0007 历史回归噪音，恢复版本门禁与平台泄漏检查的主干测试真相。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：清理主干既有回归噪音，恢复 FR-0007 相关 gate 的可信基线。
- 阻塞：待实现修复并完成回归验证后进入 PR / guardian。

## 已验证项

- `gh issue create` 已创建 Work Item `#179`
- `python3 scripts/create_worktree.py --issue 179 --class implementation`
  - 结果：已创建 worktree `/Users/mc/code/worktrees/syvert/issue-179-fr-0007`

## 未决风险

- `platform_leakage` 当前按行号归类，若 override 设计不精确，可能影响非 `execute_task()` 语句的既有边界判断。
- 测试 helper 抽取如果直接复用测试类静态方法，容易引入循环依赖；需要落独立 fixture 模块。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对应的实现与测试调整。

## 最近一次 checkpoint 对应的 head SHA

- `2c71a6d1be6eb965198cd984f2bcb17439ae6a02`
