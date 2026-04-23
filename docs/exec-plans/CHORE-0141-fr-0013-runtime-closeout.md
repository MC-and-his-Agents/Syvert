# CHORE-0141-fr-0013-runtime-closeout 执行计划

## 关联信息

- item_key：`CHORE-0141-fr-0013-runtime-closeout`
- Issue：`#195`
- item_type：`CHORE`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 spec：`docs/specs/FR-0013-adapter-resource-requirement-declaration/`
- 关联 PR：`待补充`
- 状态：`active`
- active 收口事项：`CHORE-0141-fr-0013-runtime-closeout`

## 目标

- 收口 `FR-0013` 的 runtime implementation 回合，确保 Adapter 资源需求声明在 Core 运行时链路中按统一契约落地、可追溯、可验证。
- 把 `#195` 的执行真相（实现范围、验证证据、阻塞与风险）统一沉淀到单一 active exec-plan，作为后续 review 与 merge gate 的唯一执行上下文。

## 范围

- 本次纳入：
  - `syvert/registry.py`
  - `syvert/adapters/xhs.py`
  - `syvert/adapters/douyin.py`
  - `tests/runtime/test_adapter_resource_requirement_declaration.py`
  - `tests/runtime/test_registry.py`
  - `tests/runtime/test_resource_capability_evidence.py`
  - `docs/exec-plans/CHORE-0141-fr-0013-runtime-closeout.md`
- 本次不纳入：
  - `docs/specs/FR-0013-adapter-resource-requirement-declaration/` formal spec 语义改写
  - `FR-0014` matcher 实现
  - `syvert/runtime.py` 资源匹配语义改写
  - 其他 Work Item/FR 的执行计划或治理文档

## 当前停点

- 当前 worktree：`/Users/mc/code/worktrees/syvert/issue-195-fr-0013`
- 当前分支：`issue-195-fr-0013`
- 当前状态：
  - `AdapterResourceRequirementDeclaration` 已在 registry 层落地 canonical carrier、discover/lookup API 与 fail-closed 校验。
  - xhs / douyin reference adapter 已声明 `content_detail -> required [account, proxy]` baseline declaration，并绑定到 `FR-0015` frozen evidence baseline。
  - declaration contract tests、registry tests、resource capability evidence tests 与运行时回归已经通过。
  - 待完成提交、推送、`open_pr`、guardian 与 merge gate。

## 下一步动作

- 提交当前 implementation 增量并推送 `issue-195-fr-0013`。
- 通过受控入口创建 implementation PR，回填 PR 编号与 head 绑定状态。
- 运行 guardian review；若存在阻断，按根因继续收口；若 `APPROVE`，进入 `merge-if-safe`。
- 在合入后同步 `#195`、exec-plan、PR、guardian 与 main 真相。

## 当前 checkpoint 推进的 release 目标

- 支撑 `v0.5.0`：完成 `FR-0013` runtime closeout 的执行闭环，使 Adapter 资源需求声明能力具备可审计的实现与验证证据。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0013` 的 implementation closeout Work Item，负责把 runtime 执行回合收敛为可合入状态。
- 阻塞：
  - 在验证证据与门禁状态未完整回填前，不满足 closeout 条件。
  - 若 review/guardian 与当前受审 head 不一致，不能进入合入动作。
  - 需保持与关联 spec 的边界一致，避免 closeout 期间引入超范围语义漂移。

## 已验证项

- `python3 -m py_compile syvert/registry.py syvert/adapters/xhs.py syvert/adapters/douyin.py tests/runtime/test_adapter_resource_requirement_declaration.py tests/runtime/test_registry.py tests/runtime/test_resource_capability_evidence.py`
  - 结果：通过
- `python3 -m unittest tests.runtime.test_adapter_resource_requirement_declaration tests.runtime.test_registry tests.runtime.test_resource_capability_evidence`
  - 结果：`Ran 43 tests in 0.099s`，`OK`
- `python3 -m unittest tests.runtime.test_adapter_resource_requirement_declaration tests.runtime.test_registry tests.runtime.test_resource_capability_evidence tests.runtime.test_runtime tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter tests.runtime.test_real_adapter_regression`
  - 结果：`Ran 168 tests in 2.528s`，`OK`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：当前工作树尚未形成提交时返回“当前分支相对基线没有变更，无法创建或校验 PR”；待提交后复跑
- `python3 scripts/governance_gate.py --mode ci --base-sha \"$(git merge-base origin/main HEAD)\" --head-sha \"$(git rev-parse HEAD)\" --head-ref issue-195-fr-0013`
  - 结果：通过

## 未决风险

- 若 runtime 实现与 `FR-0013` formal spec 在声明字段、校验口径或边界职责上存在漂移，closeout 可能被 review/guardian 持续阻断。
- 若验证矩阵覆盖不足，可能在合入后暴露 Adapter 声明与 Core 契约不一致问题。
- 当前 registry 对显式提供 declaration 的 adapter 执行严格完整覆盖校验；若后续新增 adapter 选择声明该 surface，但 declaration 不完整，会在 registry materialization 阶段 fail-closed。
- 若同类阻断重复出现，需要做系统性根因修复，避免仅做局部补丁导致反复返工。

## 回滚方式

- 如需回滚，采用独立 revert PR 撤销 `#195` 对应 implementation 回合增量，并在本 exec-plan 同步记录回滚原因与影响范围。

## 最近一次 checkpoint 对应的 head SHA

- `cf5fafbf467810715d19d201ed9382268531b967`
