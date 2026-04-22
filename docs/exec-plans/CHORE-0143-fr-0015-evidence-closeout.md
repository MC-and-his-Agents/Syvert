# CHORE-0143-fr-0015-evidence-closeout 执行计划

## 关联信息

- item_key：`CHORE-0143-fr-0015-evidence-closeout`
- Issue：`#197`
- item_type：`CHORE`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 spec：`docs/specs/FR-0015-dual-reference-resource-capability-evidence/`
- 关联 PR：`#204`
- 状态：`active`
- active 收口事项：`CHORE-0143-fr-0015-evidence-closeout`

## 目标

- 把 `FR-0015` 的双参考适配器资源能力证据基线落成 machine-readable registry。
- 让 `#195 / #196` 能直接消费同一份 approved capability ids 与 canonical evidence refs，而不是继续复制字符串或依赖会话判断。
- 为 code review、guardian 与后续 release closeout 提供一份可复验的 artifact 证据载体。

## 范围

- 本次纳入：
  - `syvert/resource_capability_evidence.py`
  - `tests/runtime/test_resource_capability_evidence.py`
  - `docs/exec-plans/artifacts/CHORE-0143-fr-0015-resource-capability-evidence-baseline.md`
  - `docs/exec-plans/CHORE-0143-fr-0015-evidence-closeout.md`
  - `docs/exec-plans/FR-0015-dual-reference-resource-capability-evidence.md`
- 本次不纳入：
  - `syvert/runtime.py`
  - `syvert/adapters/xhs.py`
  - `syvert/adapters/douyin.py`
  - `syvert/version_gate.py`
  - `docs/specs/FR-0015-dual-reference-resource-capability-evidence/`
  - `docs/releases/**`
  - `docs/sprints/**`

## 当前停点

- 当前执行现场：`/Users/mc/code/worktrees/syvert/issue-197-fr-0015`
- 当前执行分支：`issue-197-fr-0015`
- 当前 Work Item：`#197`
- 当前受审 PR：`#204`
- 当前实现 checkpoint：`dd7934d07b062157de89a807668772df75ed1fa5`
- 当前实现已把 `FR-0015` evidence baseline 落成 `syvert.resource_capability_evidence`，冻结了 `EvidenceReferenceEntry`、`DualReferenceResourceCapabilityEvidenceRecord`、`ApprovedResourceCapabilityVocabularyEntry` 与对应 helper / validator。
- 当前实现已把 canonical evidence baseline artifact 落到 `docs/exec-plans/artifacts/CHORE-0143-fr-0015-resource-capability-evidence-baseline.md`，与 machine-readable registry 一一对应。
- 当前实现已新增 runtime 测试，直接复验 runtime 请求 slot、reference adapter account material 消费面与 real adapter regression 资源 seed 仍与 frozen evidence refs 对齐。
- 当前回合正进入 metadata-only follow-up：在不改写 `dd7934d07b062157de89a807668772df75ed1fa5` 这条实现真相的前提下，补 active exec-plan、FR requirement container 追溯入口、PR 与 merge gate 元数据。

## 下一步动作

- 运行 `py_compile`、focused runtime 回归、`docs_guard`、`workflow_guard` 与 `pr_scope_guard`。
- 对当前受审 PR `#204` 的 live head 运行 guardian；若 verdict=`APPROVE` 且 checks 全绿，则进入受控 squash merge。
- 若 guardian 或 checks 暴露阻断，仅允许继续以 metadata-only 或最小修复回合收口，不得重写 `dd7934d07b062157de89a807668772df75ed1fa5` 的 evidence baseline 语义。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.5.0` 建立可被 `FR-0013` / `FR-0014` 直接消费的共享资源能力证据基线，避免下游重复发明 `account`、`proxy` 或自行复制 evidence refs。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0015` 的 implementation closeout Work Item，负责把 formal spec 冻结的 evidence carrier 落成代码与 artifact 真相。
- 阻塞：
  - `#195` 与 `#196` 在 implementation 上不得绕过本事项自行定义 approved capability ids 或 evidence refs。
  - 本事项不得把 evidence closeout 扩张为 `version_gate` 接线、matcher 实现或 provider 选择逻辑。

## 已验证项

- `python3 -m py_compile syvert/resource_capability_evidence.py tests/runtime/test_resource_capability_evidence.py`
  - 结果：通过
- `python3 -m unittest tests.runtime.test_resource_capability_evidence`
  - 结果：`Ran 6 tests`，`OK`
- `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter`
  - 结果：`Ran 76 tests`，`OK`
- `git commit -m 'feat(runtime): 落盘 FR-0015 资源能力证据基线'`
  - 结果：已生成实现 checkpoint `dd7934d07b062157de89a807668772df75ed1fa5`

## 未决风险

- 若 `#195 / #196` 仍在实现中手写 `account`、`proxy` 或复制 evidence ref 字符串，`FR-0015` 的单一证据真相会再次分叉。
- 若后续事项试图把 `adapter_only` / `rejected` 候选重新提升为 matcher / declaration 的合法能力名，仍会破坏 `FR-0015` 的 fail-closed 边界。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `syvert/resource_capability_evidence.py`、新增测试、artifact 与本 exec-plan / requirement container 追溯入口的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `dd7934d07b062157de89a807668772df75ed1fa5`
- 当前回合已进入 `metadata-only follow-up`；后续 PR / guardian / merge gate / closeout 元数据同步不要求该 checkpoint SHA 与最新 HEAD 完全一致。
