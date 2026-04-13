# CHORE-0101-fr-0006-validation-tooling 执行计划

## 关联信息

- item_key：`CHORE-0101-fr-0006-validation-tooling`
- Issue：`#101`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0006-adapter-contract-test-harness/`
- 关联 decision：
- 关联 PR：`#108`
- 状态：`active`
- active 收口事项：`CHORE-0101-fr-0006-validation-tooling`

## 目标

- 在 `FR-0006` 边界内落地 validation tool：消费 contract sample 定义与 harness 执行结果，稳定输出统一 verdict 结构。
- 保证最小四类结果可判定：`pass`、`legal_failure`、`contract_violation`、`execution_precondition_not_met`。
- 保持 `FR-0005` 运行时错误模型原语义；validation tool 只做验证层分类，不改写 runtime `error.category`。

## 范围

- 本次纳入：
  - `tests/runtime/contract_harness/validation_tool.py`
  - `tests/runtime/contract_harness/__init__.py`
  - `tests/runtime/test_contract_harness_validation_tool.py`
  - 本 exec-plan
- 本次不纳入：
  - release / sprint 文档更新
  - GitHub 状态与 closeout 操作
  - fake adapter / harness host 的实现细节（`#102` 范围）
  - contract samples 与最小自动化验证聚合（`#103` 范围）
  - 真实 adapter 与平台逻辑

## 当前停点

- `FR-0006` formal spec 已合入主干；`#101` 当前作为 implementation Work Item 承接“验证工具与结果分类”。
- 当前 worktree：`/Users/mc/code/worktrees/syvert/issue-101-fr-0006`，仅处理测试侧 harness 验证工具与必要最小测试改动。
- 当前分支已 rebase 到 `origin/main@1dbf4c6`（`#102` 已合入后的主干状态）。
- validation tool 已在测试侧落地，包含单样例与批量样例两条分类入口；当前受审 PR 为 `#108`。

## 下一步动作

- 等当前 PR `#108` 完成 reviewer / guardian / merge gate。
- 若再出现阻断，仅做 `FR-0006` 验证层边界内的最小修复，不扩展到 `#102/#103`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 提供稳定的 contract harness 验证分类层，作为后续 `FR-0007` 消费 `FR-0006` 输出的前置基座。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0006` implementation 第二步，负责 validation tool。
- 阻塞：
  - 需保持与 `#102/#103` 并行实现边界，避免越界到 fake adapter/harness host 或样例聚合自动化。

## 已验证项

- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`spec_review.md`
- 已阅读：`code_review.md`
- 已阅读：`docs/specs/FR-0006-adapter-contract-test-harness/`
- 已核对：以 `origin/main@1dbf4c6` 为基线，本分支仅新增 validation tool 与对应测试，并更新 `__init__.py` 导出与本 exec-plan 元数据
- `python3 -m unittest tests.runtime.test_contract_harness_validation_tool`
  - 结果：`Ran 13 tests`，`OK`
- `python3 -m unittest tests.runtime.test_executor tests.runtime.test_runtime tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool`
  - 结果：`Ran 57 tests`，`OK`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：`通过`
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：`通过`
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：`通过`
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
  - 结果：`通过`
- `python3 scripts/open_pr.py --class implementation --issue 101 --item-key CHORE-0101-fr-0006-validation-tooling --item-type CHORE --release v0.2.0 --sprint 2026-S15 --title 'feat(test): 落地 FR-0006 验证工具与结果分类' --closing fixes --dry-run`
  - 结果：`通过`
- guardian 首轮审查：`REQUEST_CHANGES`
  - 阻断项已修复：
    - success 样例不再接受缺失 `raw` / `normalized` 的伪 success envelope
    - `runtime_contract` 失败不再被归类为 `legal_failure`
- guardian 次轮审查：`REQUEST_CHANGES`
  - 阻断项已修复：
    - success 样例与 legal failure 样例改为校验完整 runtime envelope，而非只看局部字段
    - active exec-plan 已与已创建的 PR `#108`、当前 review 状态和后续动作对齐
- guardian 三轮审查：`REQUEST_CHANGES`
  - 阻断项已修复：
    - 混合 `precondition_code` 与 `runtime_envelope` 的非法状态不再被误判为执行前置不满足
    - contract violation 样例在观察到 success envelope 时恢复独立 reason code
    - 新增一条由 `execute_harness_sample()` 驱动的 platform legal failure -> validator 联动测试
- review gate 语义：当前分支已满足 `implementation` 类 PR 的本地测试与 guard 前置条件；后续仅需按流程进入 reviewer / guardian / checks 与 merge gate

## 未决风险

- 若将 `execution_precondition_not_met` 与进入 Core 后的 `invalid_input` 混淆，会破坏 `FR-0006` 对分类边界的要求。
- 若 validation tool 擅自改写 runtime `error.category`，会越界到 `FR-0005` 的上位语义。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `tests/runtime/contract_harness/`、`tests/runtime/test_contract_harness_validation_tool.py` 与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `cf98c8a4e7fa6d7b8a54e1608f2fe810e0f41d64`
