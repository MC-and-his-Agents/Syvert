# CHORE-0103-fr-0006-contract-samples-minimal-automation 执行计划

## 关联信息

- item_key：`CHORE-0103-fr-0006-contract-samples-minimal-automation`
- Issue：`#103`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0006-adapter-contract-test-harness/`
- active Work Item：`CHORE-0103-fr-0006-contract-samples-minimal-automation`

## 目标

- 基于 `FR-0006` spec 的 contract harness 架构，落地 contract samples 清单、最小 automation 聚合执行与自动化断言。
- 固定四类样例：`pass`、`legal_failure`、`contract_violation`、`execution_precondition_not_met`。
- 为后续 `FR-0007` 提供不依赖真实平台的稳定 harness 输入。

## 范围

- 本次纳入：
  - `tests/runtime/contract_harness/samples.py`
  - `tests/runtime/contract_harness/automation.py`
  - `tests/runtime/contract_harness/__init__.py`
  - `tests/runtime/test_contract_harness_automation.py`
  - 本 exec-plan
- 本次不纳入：
  - fake adapter / harness host 的实现细节（`#102` 范围）
  - validator 本体实现（`#101` 范围）
  - 真实平台回归、版本 gate、平台泄漏检查
  - GitHub closeout 与父 FR `#66` 收口

## 当前停点

- 当前 worktree：`/Users/mc/code/worktrees/syvert/issue-103-fr-0006`。
- contract samples 已补齐四组稳定样例：
  - `success-full-envelope`
  - `legal-failure-platform-envelope`
  - `contract-violation-missing-normalized`
  - `execution-precondition-not-met`
- automation 聚合入口已落地，可批量执行样例、交给 validator 分类，并输出按 `sample_id` 可追溯的 verdict 结果。
- 最小自动化验证已落地，当前在本地可证明四组样例的 observed verdict 与 spec 一致。

## 下一步动作

1. 等 `#101` 合入主干后，剥离当前分支历史中夹带的 `#101` 提交，确保 `#103` PR diff 只保留本事项改动。
2. 补齐 `docs/releases/v0.2.0.md` 与 `docs/sprints/2026-S15.md` 对 `#101/#102/#103` 与对应 PR 的证据回链。
3. 完成 guards、开 PR，并进入 reviewer / guardian / merge gate。

## 已验证项

- `gh issue view 103 --json number,title,state`
  - 结果：确认 `#103` 已 open 并关联 `FR-0006` harness automation Work Item。
- `python3 scripts/create_worktree.py --issue 103 --class implementation`
  - 结果：should produce `/Users/mc/code/worktrees/syvert/issue-103-fr-0006` (current context).
- `python3 -m unittest tests.runtime.test_executor tests.runtime.test_runtime tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation`
  - 结果：`Ran 55 tests`，`OK`

## 未决风险

- 当前分支历史仍包含 `#101` 的旧提交；若不在开 PR 前剥离，会让 `#103` PR 范围污染。
- release / sprint 文档尚未回链 `#101/#102/#103` 的实现 PR 事实，当前仍未满足本事项最终 closeout 证据要求。

## 回滚方式

- 若 contract samples 或 automation 与 spec 语义冲突，使用独立 revert PR 撤销本事项对 `tests/runtime/contract_harness/`、`tests/runtime/test_contract_harness_automation.py` 与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `d2e18aa1d608d4572662978549cc5d01f6d9f047`
