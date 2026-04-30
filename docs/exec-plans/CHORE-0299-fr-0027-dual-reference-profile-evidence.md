# CHORE-0299-fr-0027-dual-reference-profile-evidence 执行计划

## 关联信息

- item_key：`CHORE-0299-fr-0027-dual-reference-profile-evidence`
- Issue：`#300`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0027-multi-profile-resource-requirement-contract/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0299-fr-0027-dual-reference-profile-evidence`
- 状态：`active`

## 目标

- 基于已合入的 `FR-0027` formal spec，刷新 `FR-0015` 双参考 evidence carrier，使其能产出 `FR-0027` 可直接消费的 profile-level shared approval proof，并显式保留 adapter_only / rejected profile truth。

## 范围

- 本次纳入：
  - `syvert/resource_capability_evidence.py`
  - `tests/runtime/test_resource_capability_evidence.py`
  - `docs/specs/FR-0015-dual-reference-resource-capability-evidence/`
  - `docs/exec-plans/CHORE-0299-fr-0027-dual-reference-profile-evidence.md`
  - `docs/releases/v0.8.0.md`
  - `docs/sprints/2026-S21.md`
- 本次不纳入：
  - matcher runtime 实现
  - reference adapter declaration migration
  - provider compatibility / priority / fallback
  - `#294` parent closeout

## 当前停点

- `#299` 已通过 PR `#304` 合入主干，`FR-0027` formal spec 已成为 `v0.8.0` 当前双参考 slice 的 governing artifact。
- 当前执行现场位于 `issue-300-fr-0027-profile` worktree，基线为 `9feb47387c655e1d0b50474249fed577637654c8`。
- 已把 `FR-0015` evidence carrier 扩展到 profile 级：
  - `account+proxy` -> `shared + approve_profile_for_v0_8_0`
  - `account-only` -> `shared + approve_profile_for_v0_8_0`
  - `douyin account private material` -> `adapter_only + keep_adapter_local`
  - `proxy-only` -> `rejected + reject_profile_for_v0_8_0`
  - `none` -> `rejected + reject_profile_for_v0_8_0`
- 已新增 `ApprovedSharedResourceRequirementProfileEvidenceEntry` 投影入口，供 `#301/#302` 消费。

## 下一步动作

- 运行实现与治理门禁。
- 提交并创建 `#300` 受控 PR。
- 等待 reviewer / guardian / checks 收口后执行受控合并，并关闭 `#300`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 的 FR-0027 multi-profile runtime 与 reference adapter migration 提供可复验 profile evidence input。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0027` 的 profile evidence Work Item。
- 阻塞：
  - `#301` matcher/runtime contract 需要读取本事项批准的 shared profile proof。
  - `#302` reference adapter declaration migration 需要绑定本事项产出的 profile `evidence_refs`。

## 已验证项

- `python3 -m unittest tests.runtime.test_resource_capability_evidence`
  - 结果：通过，30 tests。

## 未决风险

- `account-only` 被批准为 shared profile 的边界只适用于当前 `content_detail_by_url + target_type=url + collection_mode=hybrid` 双参考 slice，不得外推到其它 execution path。
- `adapter_only` profile truth 只能作为 evidence 事实保留，不得被后续 declaration migration 偷渡进 shared declaration。

## 回滚方式

- 使用独立 revert PR 撤销本事项对 `syvert/resource_capability_evidence.py`、相关测试、`FR-0015` 文档与 release / sprint 索引的增量修改。
- 若需要重判 profile 合法性，先回到 evidence carrier，不在 matcher 或 adapter migration PR 中隐式改写 profile approval truth。

## 最近一次 checkpoint 对应的 head SHA

- `c39eff1459c652c3b103b328aacf4a8cdec5e3eb`
- 说明：该 checkpoint 首次把 `FR-0027` profile evidence carrier、formal research truth、测试、release / sprint 索引与当前 active exec-plan 同步落盘；后续若只补 PR / guardian / merge gate 元数据，则作为 review-sync follow-up，不把版本化 exec-plan 退化为 live head 状态面。
