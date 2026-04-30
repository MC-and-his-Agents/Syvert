# CHORE-0301-fr-0027-reference-adapter-declaration-migration 执行计划

## 关联信息

- item_key：`CHORE-0301-fr-0027-reference-adapter-declaration-migration`
- Issue：`#302`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0027-multi-profile-resource-requirement-contract/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0301-fr-0027-reference-adapter-declaration-migration`
- 状态：`active`

## 目标

- 将小红书、抖音 reference adapter 的 resource requirement declarations 从 V1 单声明迁移到 `FR-0027` V2 multi-profile carrier，并保持当前执行路径、resource acquisition 与错误口径不漂移。

## 范围

- 本次纳入：
  - `syvert/registry.py`
  - `syvert/adapters/xhs.py`
  - `syvert/adapters/douyin.py`
  - `tests/runtime/resource_fixtures.py`
  - `tests/runtime/test_registry.py`
  - `tests/runtime/test_resource_capability_evidence.py`
  - `tests/runtime/test_runtime.py`
  - `tests/runtime/test_task_record.py`
  - `docs/exec-plans/CHORE-0301-fr-0027-reference-adapter-declaration-migration.md`
  - `docs/releases/v0.8.0.md`
  - `docs/sprints/2026-S21.md`
- 本次不纳入：
  - matcher/runtime contract 新语义
  - provider offer / compatibility decision
  - 新共享能力词汇
  - profile priority / fallback
  - `#294` parent closeout

## 当前停点

- `#301` 已合入主干，V2 declaration/profile carrier、registry validation 与 matcher `one-of` runtime path 已可用。
- 当前执行现场位于 `issue-302-fr-0027-adapter` worktree，基线为 `431c4b0f9182f3a14d3b642a315bd266986e5923`。
- 已新增 `baseline_multi_profile_resource_requirement_declaration()`，作为 reference adapter 与 runtime fixtures 的 V2 baseline helper。
- `XhsAdapter`、`DouyinAdapter` 与 `tests/runtime/resource_fixtures.py` 已迁移到 V2 multi-profile declaration。
- 已更新 registry / evidence / runtime / task record 测试中对 reference baseline 与 unmatched 条件的断言。

## 下一步动作

- 运行完整 runtime / docs / governance 门禁。
- 提交并创建 `#302` 受控 PR。
- 等待 reviewer / guardian / checks 收口后执行受控合并，并关闭 `#302`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 的 FR-0027 parent closeout 提供主干 reference adapter V2 declaration baseline。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0027` 的 reference adapter migration Work Item。
- 阻塞：
  - `#303` parent closeout 必须等待 reference adapters 不再绑定旧 V1 单声明 baseline。

## 已验证项

- `python3 -m unittest tests.runtime.test_registry tests.runtime.test_resource_capability_evidence tests.runtime.test_resource_capability_matcher`
  - 结果：通过，59 tests。
- `python3 -m unittest tests.runtime.test_runtime tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter`
  - 结果：通过，116 tests。
- `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_task_record tests.runtime.test_cli tests.runtime.test_http_api`
  - 结果：通过，122 tests。
- `python3 -m unittest tests.runtime.test_registry tests.runtime.test_resource_capability_evidence tests.runtime.test_resource_capability_matcher tests.runtime.test_runtime tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter tests.runtime.test_real_adapter_regression tests.runtime.test_task_record tests.runtime.test_cli tests.runtime.test_http_api`
  - 结果：通过，297 tests。
- `python3 -m py_compile syvert/registry.py syvert/adapters/xhs.py syvert/adapters/douyin.py`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-302-fr-0027-adapter`
  - 结果：通过。

## 未决风险

- V2 baseline 让 `account-only` 成为合法 shared profile，因此旧测试中“只有 account 则 unmatched”的假设已改为 `proxy-only` 才 unmatched。
- 本事项只迁移 reference adapter declaration，不改变 runtime resource slot request；当前共享路径仍请求 `account` 与 `proxy`。

## 回滚方式

- 使用独立 revert PR 撤销本事项对 adapters、fixtures、tests、registry helper、exec-plan 与 release-sprint 索引的增量修改。
- 若 reference adapter V2 baseline 需要重判，应回到 `#301` runtime contract 或 `#300` evidence truth，不在 adapter 私有代码中保留影子声明。

## 最近一次 checkpoint 对应的 head SHA

- `7a9c36d46927f10429e4cacb012472bc7a75692c`
- 说明：该 checkpoint 首次把 reference adapter V2 declaration baseline、fixtures、registry helper、受影响测试与 release / sprint 索引同步落盘；后续若只补 PR / guardian / merge gate 元数据，则作为 review-sync follow-up，不把版本化 exec-plan 退化为 live head 状态面。
