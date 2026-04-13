# CHORE-0102-fr-0006-fake-adapter-harness 执行计划

## 关联信息

- item_key：`CHORE-0102-fr-0006-fake-adapter-harness`
- Issue：`#102`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0006-adapter-contract-test-harness/`
- 关联 PR：`#104`
- 状态：`active`
- active 收口事项：`CHORE-0102-fr-0006-fake-adapter-harness`

## 目标

- 在测试侧落地受控 fake adapter 与最小 harness host。
- 通过 `syvert.runtime.execute_task` + `AdapterRegistry` 标准路径执行样例，不依赖真实平台。
- 固定验证 `success`、受控 `legal failure` 与 `illegal payload` 三条最小分支，且非法 payload 继续归入既有 `runtime_contract` 语义。

## 范围

- 本次纳入：
  - `tests/runtime/contract_harness/**`
  - `tests/runtime/test_contract_harness_host.py`
  - 本 exec-plan
- 本次不纳入：
  - release / sprint 索引更新
  - GitHub 状态变更
  - 真实 adapter 或 `FR-0006` 以外事项
  - validator 与契约样例聚合自动化（留给 `#101/#103`）

## 当前停点

- `FR-0006` formal spec 已合入主干，并明确 `#102` 负责 fake adapter 与最小 harness host。
- 运行时现状：`execute_task` 已具备标准 registry materialization、capability projection 与 success payload fail-closed 校验能力，可直接作为 harness 宿主。
- 本地已完成测试侧 `contract_harness` 最小实现与单测，覆盖 `success`、受控 `legal failure` 与 `illegal payload` 三条最小分支。

## 下一步动作

- 进入当前 Work Item 的评审与门禁回合。
- 仅在评审阻断要求下进行最小增量修复，不扩展到 validator、sample automation 或 closeout 索引事项。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 落地 `FR-0006` 第一个 implementation 子事项，提供后续 validator 与 contract samples 的稳定执行基座。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0006` implementation Work Item `#102`。
- 阻塞：
  - 不得改写 `FR-0002/FR-0005` 上位错误模型与 contract 语义。
  - 不得引入真实平台依赖或 reference adapter 逻辑。

## 已验证项

- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`spec_review.md`
- 已阅读：`code_review.md`
- 已阅读：`docs/specs/FR-0006-adapter-contract-test-harness/`
- `python3 -m unittest tests.runtime.test_executor tests.runtime.test_runtime tests.runtime.test_contract_harness_host`
  - 结果：`Ran 44 tests in 0.005s`，`OK`
- 当前受审 PR：`#104`
- 当前实现 head：`9e4623687ced99df65cebbaffc8835d0d7b59e46`
- 说明：`9e4623687ced99df65cebbaffc8835d0d7b59e46` 补齐 fake adapter 的受控 `legal_failure` 分支与 host-level 验证，并以当前受审 head 重新绑定验证证据。

## 未决风险

- 若 fake adapter 绕过 `execute_task`/registry 直调内部函数，会破坏 `FR-0006` 的标准宿主路径要求。
- 若 legal failure 或 illegal payload 在 harness 层被提前重分类，会与 `FR-0005` 既有错误模型语义冲突。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `tests/runtime/contract_harness/**`、`tests/runtime/test_contract_harness_host.py` 与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `9e4623687ced99df65cebbaffc8835d0d7b59e46`
