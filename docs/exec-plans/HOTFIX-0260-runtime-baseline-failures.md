# HOTFIX-0260 Runtime baseline failures 执行计划

## 关联信息

- item_key：`HOTFIX-0260-runtime-baseline-failures`
- Issue：`#260`
- item_type：`HOTFIX`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 spec：`docs/specs/FR-0007-release-gate-and-regression-checks/`
- 关联 decision：
- 关联 PR：`#261`
- active 收口事项：`HOTFIX-0260-runtime-baseline-failures`
- 状态：`active`

## 目标

- 收敛 `#259` Loom adoption 过程中显式拆出的 Syvert runtime baseline residual。
- 恢复 `python3.11 -m unittest discover -s tests/runtime -p 'test_*.py'` 在主干上的稳定通过状态。

## 范围

- 本次纳入：`tests/runtime` 当前失败与异常耗时的最小修复，包括 CLI durable truth 等价测试规范化、Douyin browser bridge 单测签名依赖隔离、platform leakage 扫描性能修复，以及由此解除的 version gate 超时。
- 本次不纳入：Loom runtime / governance carrier 变更、Core / Adapter SDK public contract 变更、v0.6.0 tag 或 GitHub Release 改写。

## 当前停点

- `#258/#257/#259` 已关闭，Loom adoption 已合入主干。
- `#260` 已补齐事项上下文，当前 worktree 已完成 runtime baseline 最小修复。
- PR `#261` 已创建，`tests/runtime` discovery 已在当前分支通过，等待最新 head 的 CI、guardian 与受控合并。

## 下一步动作

- 完成 PR `#261` 的 CI、guardian 与受控合并。
- 合入后回写并关闭 `#260`。

## 当前 checkpoint 推进的 release 目标

- 为已发布的 `v0.6.0` 补齐 post-closeout runtime baseline hotfix，使后续治理迁移不再携带 `tests/runtime` waiver。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`v0.6.0` 发布后的 runtime baseline hotfix。
- 阻塞：`#260` 关闭前，`tests/runtime` discovery 不能作为主干稳定门禁恢复使用。

## 已验证项

- `python3.11 -m unittest tests.runtime.test_cli.CliTests.test_run_subcommand_and_legacy_entrypoint_persist_equivalent_durable_truth`
  - 结果：通过，`Ran 1 test`，`OK`。
- `python3.11 -m unittest tests.runtime.test_douyin_browser_bridge.DouyinBrowserBridgeTests.test_extract_page_state_falls_back_to_authenticated_detail_request_when_page_state_misses_target`
  - 结果：通过，`Ran 1 test`，`OK`。
- `python3.11 -m unittest tests.runtime.test_platform_leakage`
  - 结果：通过，`Ran 111 tests in 69.782s`，`OK`。
- `python3.11 -m unittest tests.runtime.test_version_gate`
  - 结果：通过，`Ran 99 tests in 2.546s`，`OK`。
- `python3.11 -m unittest discover -s tests/runtime -p 'test_*.py'`
  - 结果：通过，`Ran 832 tests in 79.697s`，`OK`。
- `python3.11 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3.11 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3.11 -m py_compile syvert/*.py syvert/adapters/*.py`
  - 结果：通过。
- `python3.11 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref issue-260-fix-runtime-tests-runtime-baseline-failures`
  - 结果：通过。

## 未决风险

- platform leakage 扫描器属于 release gate 证据链的一部分，性能修复必须保持 payload/report 形状不变。
- Douyin browser bridge 的 signer 注入只能作为 adapter-private 测试隔离入口，默认运行路径必须继续使用既有签名请求。
- CLI durable truth 等价修复只允许规范化测试中的动态 ID / 时间 / duration，不应放宽 production contract。

## 回滚方式

- 使用独立 revert PR 撤销本事项对 `tests/runtime/test_cli.py`、`tests/runtime/test_douyin_browser_bridge.py`、`syvert/adapters/douyin_browser_bridge.py`、`syvert/platform_leakage.py`、本 exec-plan 与 sprint 索引的增量。

## 最近一次 checkpoint 对应的 head SHA

- `a0279906a05dde60296445a28277d49909fdfe52`
- 说明：该 SHA 为本 hotfix worktree 从 `origin/main` 创建时的基线；进入 review 前会以当前 PR head 和验证证据更新执行状态。
