# CHORE-0300-fr-0027-matcher-runtime-contract 执行计划

## 关联信息

- item_key：`CHORE-0300-fr-0027-matcher-runtime-contract`
- Issue：`#301`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0027-multi-profile-resource-requirement-contract/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0300-fr-0027-matcher-runtime-contract`
- 状态：`active`

## 目标

- 基于 `FR-0027` 与 `#300` 已合入的 profile evidence truth，落地 multi-profile declaration runtime consumption 与 matcher `one-of` 语义，同时保持非法声明 fail-closed、合法未命中继续映射为 `resource_unavailable`。

## 范围

- 本次纳入：
  - `syvert/resource_capability_evidence.py`
  - `syvert/registry.py`
  - `syvert/runtime.py`
  - `tests/runtime/test_resource_capability_evidence.py`
  - `tests/runtime/test_resource_capability_matcher.py`
  - `tests/runtime/test_registry.py`
  - `tests/runtime/test_runtime.py`
  - `docs/exec-plans/CHORE-0300-fr-0027-matcher-runtime-contract.md`
  - `docs/releases/v0.8.0.md`
  - `docs/sprints/2026-S21.md`
- 本次不纳入：
  - reference adapter declaration migration
  - provider compatibility / priority / fallback
  - 新共享能力词汇
  - `#294` parent closeout

## 当前停点

- `#299` formal spec 与 `#300` profile evidence truth 已合入主干。
- 当前执行现场位于 `issue-301-fr-0027-matcher-profile-runtime-contract` worktree，基线为 `8414b0625ec0b9c4f17be135cb47d75998765056`。
- 已新增 machine-readable `ResourceRequirementProfileEvidenceRecord` 与 `ApprovedSharedResourceRequirementProfileEvidenceEntry` carrier，并与 `FR-0015` research 表格 fail-closed 对齐。
- 已新增 `AdapterResourceRequirementDeclarationV2` 与 `AdapterResourceRequirementProfile`，registry 可双读 V1/V2。
- 已把 matcher 扩展为 V2 `one-of` 语义；V1 matcher 兼容路径保留。
- runtime 对 V2 合法未命中仍映射为 `resource_unavailable`，并返回 profile-aware details。

## 下一步动作

- 运行完整 runtime / docs / governance 门禁。
- 提交并创建 `#301` 受控 PR。
- 等待 reviewer / guardian / checks 收口后执行受控合并，并关闭 `#301`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 的 FR-0027 reference adapter declaration migration 提供可运行、可验证的 multi-profile matcher/runtime contract。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0027` 的 matcher/runtime implementation Work Item。
- 阻塞：
  - `#302` reference adapter declaration migration 必须等待本事项提供 V2 carrier、registry validation 与 matcher runtime path。

## 已验证项

- `python3 -m unittest tests.runtime.test_resource_capability_matcher`
  - 结果：通过，17 tests。
- `python3 -m unittest tests.runtime.test_registry tests.runtime.test_adapter_resource_requirement_declaration`
  - 结果：通过，25 tests。
- `python3 -m unittest tests.runtime.test_resource_capability_evidence`
  - 结果：通过，27 tests。
- `python3 -m unittest tests.runtime.test_runtime`
  - 结果：通过，59 tests。
- `python3 -m unittest tests.runtime.test_resource_capability_matcher tests.runtime.test_resource_capability_evidence tests.runtime.test_registry tests.runtime.test_adapter_resource_requirement_declaration tests.runtime.test_runtime tests.runtime.test_task_record`
  - 结果：通过，151 tests。
- `python3 -m py_compile syvert/resource_capability_evidence.py syvert/registry.py syvert/runtime.py`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-301-fr-0027-matcher-profile-runtime-contract`
  - 结果：通过。

## 未决风险

- `#302` 迁移前 reference adapters 仍使用 V1 declaration；本事项通过双读避免提前混入 adapter migration。
- 当前 approved shared profile truth 只覆盖 `account+proxy` 与 `account-only`；`none` 的 matcher 语义已支持，但主干当前没有 approved `none` proof。

## 回滚方式

- 使用独立 revert PR 撤销本事项对 runtime / registry / evidence carrier / tests / exec-plan / release-sprint 索引的增量修改。
- 若发现 declaration model 不足，必须回到 `FR-0027` formal spec 或 `FR-0015` evidence truth，不在 runtime 层私自补字段。

## 最近一次 checkpoint 对应的 head SHA

- `02e1e54361878fcce34d20e3a0a50b48a27b8b58`
- 说明：该 checkpoint 首次把 FR-0027 V2 profile evidence carrier、registry V2 declaration validation、matcher `one-of` runtime path、runtime unmatched 映射与测试同步落盘；后续若只补 PR / guardian / merge gate 元数据，则作为 review-sync follow-up，不把版本化 exec-plan 退化为 live head 状态面。
