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
- 当前实现 checkpoint：`c6272cecd11f070c43c5c1f06ed949dbac109f0a`
- 当前实现已把 `FR-0015` evidence baseline 落成 `syvert.resource_capability_evidence`，冻结了 `EvidenceReferenceEntry`、`DualReferenceResourceCapabilityEvidenceRecord`、`ApprovedResourceCapabilityVocabularyEntry` 与对应 helper / validator。
- 当前实现已把 canonical evidence baseline artifact 落到 `docs/exec-plans/artifacts/CHORE-0143-fr-0015-resource-capability-evidence-baseline.md`，与 machine-readable registry 一一对应。
- 当前实现已新增 runtime 测试，直接复验 runtime 请求 slot、reference adapter account material 消费面与 real adapter regression 资源 seed 仍与 frozen evidence refs 对齐。
- 当前实现已按 guardian 同类阻断把 validator 收紧为“由 shared records 派生 canonical approved vocabulary，并要求 frozen vocabulary 与该派生结果精确等价”的 fail-closed 模式，不再只做局部字段检查。
- 当前实现已新增负向测试，覆盖未批准 shared capability 漂移、duplicate shared adapter/capability pair，以及 approved vocabulary evidence refs 漂移三类同源回归。
- 当前实现已按 guardian 第二轮同类阻断继续把“证据可复验 / 可追溯”收紧为通用不变量：
  - `proxy` shared evidence 现在直接穿过 `execute_task()` 的公开运行时路径，验证 `content_detail_by_url + hybrid` 上的 slot 解析、resource acquire 与 bundle 绑定确实包含 `proxy`
  - evidence registry 现在会对 `source_file` 与 `source_symbol` 做 fail-closed 追溯校验，要求文件真实存在且符号仍能从源码 AST 解析到
- 当前实现已按 guardian 第三轮阻断继续把 fail-closed 落到公开消费边界：所有对外 accessor 现在都会先执行 `validate_frozen_resource_capability_evidence_contract()`，不再允许下游在 drifted baseline 上静默读取 approved capability ids 或 frozen registry。
- 当前回合再次进入 metadata-only follow-up：在不改写 `c6272cecd11f070c43c5c1f06ed949dbac109f0a` 这条实现真相的前提下，同步最新 checkpoint、guardian 恢复状态与 merge gate 元数据。

## 下一步动作

- 对当前受审 PR `#204` 的 live head 重新运行 guardian；若 verdict=`APPROVE` 且 checks 全绿，则进入受控 squash merge。
- 若 guardian 或 checks 继续暴露阻断，只允许围绕 shared-record-to-vocabulary canonical mapping 同类边界做最小修复，不得扩张为 runtime / version gate 语义改写。

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
  - 结果：`Ran 12 tests`，`OK`
- `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter`
  - 结果：`Ran 76 tests`，`OK`
- `git commit -m 'feat(runtime): 落盘 FR-0015 资源能力证据基线'`
  - 结果：已生成实现 checkpoint `dd7934d07b062157de89a807668772df75ed1fa5`
- `python3 scripts/pr_guardian.py review 204 --post-review`
  - 结果：guardian 首轮 `REQUEST_CHANGES`
  - 同类阻断已按系统性方式收口：
    - validator 现在会从 shared records 派生 canonical approved vocabulary，并反向拒绝任何不属于冻结批准词汇的 `shared + approve_for_v0_5_0` 记录
    - validator 现在要求 approved vocabulary entries 与 shared records 派生出的 canonical approval basis evidence refs 精确一致
    - 新增负向测试覆盖 stray shared capability、duplicate shared pair 与 approval basis drift 三类回归
- `python3 -m unittest tests.runtime.test_resource_capability_evidence tests.runtime.test_real_adapter_regression tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter`
  - 结果：在 checkpoint `aa3f41f2a7d2e9567edc951ab9ee2a4ce30b61f8` 上通过，`Ran 85 tests`，`OK`
- `python3 scripts/pr_guardian.py review 204 --post-review`
  - 结果：guardian 第二轮 `REQUEST_CHANGES`
  - 同类阻断已按系统性方式继续收口：
    - 新增运行时级验证，直接覆盖 `content_detail_by_url + hybrid` 路径上 `proxy` slot 的解析、acquire 与 bundle 绑定闭环
    - evidence registry 现在要求 `source_file` 可读且 `source_symbol` 能从对应源码 AST 解析到，避免追溯指针静默失效
- `python3 -m unittest tests.runtime.test_resource_capability_evidence tests.runtime.test_real_adapter_regression tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter`
  - 结果：在 checkpoint `4076e02a68b802b8d1b94ff0bd7ab57a45472790` 上通过，`Ran 87 tests`，`OK`
- `python3 scripts/pr_guardian.py review 204 --post-review`
  - 结果：guardian 第三轮 `REQUEST_CHANGES`
  - 同类阻断已按系统性方式继续收口：
    - 所有对外 accessor 现在都会先执行 `validate_frozen_resource_capability_evidence_contract()`，把 fail-closed 从 validator 扩展到公开消费边界
    - 新增回归，证明 downstream-facing accessor 在 baseline 漂移时不会静默返回 frozen data
- `python3 -m unittest tests.runtime.test_resource_capability_evidence tests.runtime.test_real_adapter_regression tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter`
  - 结果：在 checkpoint `c6272cecd11f070c43c5c1f06ed949dbac109f0a` 上通过，`Ran 88 tests`，`OK`

## 未决风险

- 若 `#195 / #196` 仍在实现中手写 `account`、`proxy` 或复制 evidence ref 字符串，`FR-0015` 的单一证据真相会再次分叉。
- 若后续事项试图把 `adapter_only` / `rejected` 候选重新提升为 matcher / declaration 的合法能力名，仍会破坏 `FR-0015` 的 fail-closed 边界。
- 若后续修改重新把 shared records 与 approved vocabulary 拆成两套独立 truth，而不是保持派生式精确等价，guardian 同类阻断仍会再次出现。
- 若后续重构改变运行时路径或源码入口而没有同步 evidence registry，新的 source-pointer 校验和 runtime-path 校验会直接 fail-closed；这类失败应优先视为证据基线漂移，而不是测试偶发。
- 若后续实现直接读取底层 frozen 常量而不是走公开 accessor，仍会绕开 fail-closed；`#195 / #196` 必须坚持只消费公开 accessor。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `syvert/resource_capability_evidence.py`、新增测试、artifact 与本 exec-plan / requirement container 追溯入口的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `c6272cecd11f070c43c5c1f06ed949dbac109f0a`
- 当前回合已进入 `metadata-only follow-up`；后续 PR / guardian / merge gate / closeout 元数据同步不要求该 checkpoint SHA 与最新 HEAD 完全一致。
