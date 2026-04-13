# CHORE-0103-fr-0006-contract-samples-minimal-automation 执行计划

## 关联信息

- item_key：`CHORE-0103-fr-0006-contract-samples-minimal-automation`
- Issue：`#103`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0006-adapter-contract-test-harness/`
- 关联 PR：`#109`
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
- 当前受审 PR：`#109`

## 下一步动作

1. 当前受审 PR `#109` 进入 reviewer / guardian / merge gate。
2. 若审查出现阻断，仅在 `#103` 的 contract samples / automation / 索引证据范围内做最小修复。

## 已验证项

- `gh issue view 103 --json number,title,state`
  - 结果：确认 `#103` 已 open 并关联 `FR-0006` harness automation Work Item。
- `python3 scripts/create_worktree.py --issue 103 --class implementation`
  - 结果：should produce `/Users/mc/code/worktrees/syvert/issue-103-fr-0006` (current context).
- `python3 -m unittest tests.runtime.test_executor tests.runtime.test_runtime tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation`
  - 结果：`Ran 65 tests`，`OK`
- guardian 首轮审查：`REQUEST_CHANGES`
  - 阻断项已修复：
    - execution_precondition_not_met 样例若意外进入 runtime，不再可能被误判为 `pass`
    - 新增 precondition 样例误入 runtime 的负向回归测试
- guardian 次轮审查：`REQUEST_CHANGES`
  - 阻断项已修复：
    - `build_contract_sample_definitions()` 不再把 precondition 样例降格为 `success`
    - precondition 样例改由 dedicated validation path 输出，避免 exported helper 丢失第四类 verdict 语义
- guardian 三轮审查：`REQUEST_CHANGES`
  - 阻断项已修复：
    - precondition verdict 改为来自真实前置检查，不再靠 expected 值直接硬编码
    - sample metadata 现在实际驱动 adapter 声明与 harness 前置校验，元数据漂移会 fail-close
    - 新增一条经过真实 execution path 的 metadata drift 负向回归测试
- guardian 四轮审查：`REQUEST_CHANGES`
  - 阻断项已修复：
    - adapter 声明/输入约束不匹配不再前移成 precondition，而是保留为经 Core 产出的运行时 failed envelope
    - 新增重复 `sample_id` fail-close，保证样例级索引不被静默覆盖
- guardian 五轮审查：`REQUEST_CHANGES`
  - 阻断项已修复：
    - `SampleInput` 不再暴露当前宿主未执行的 `target_type` / `collection_mode` 字段，避免样例 contract 与实际执行路径漂移

## 未决风险

- 若 `#103` 的 automation 断言后续与 `#101` validator 语义漂移，会削弱 `FR-0007` 对 harness 基座的复用稳定性。

## 回滚方式

- 若 contract samples 或 automation 与 spec 语义冲突，使用独立 revert PR 撤销本事项对 `tests/runtime/contract_harness/`、`tests/runtime/test_contract_harness_automation.py` 与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `26c25591d08d7857f5471b3f99656b64a1524bc7`
