# CHORE-0299-fr-0027-dual-reference-profile-evidence 执行计划

## 关联信息

- item_key：`CHORE-0299-fr-0027-dual-reference-profile-evidence`
- Issue：`#300`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0015-dual-reference-resource-capability-evidence/`
- 关联 decision：
- 关联 PR：`#305`
- active 收口事项：`CHORE-0299-fr-0027-dual-reference-profile-evidence`
- 状态：`active`

## 目标

- 基于已合入的 `FR-0027` formal spec，刷新 `FR-0015` 双参考 evidence truth，使其能定义 `FR-0027` 可直接消费的 profile-level shared approval proof，并显式保留 adapter_only / rejected profile 判定口径。

## 范围

- 本次纳入：
  - `docs/specs/FR-0015-dual-reference-resource-capability-evidence/`
  - `docs/exec-plans/CHORE-0299-fr-0027-dual-reference-profile-evidence.md`
  - `docs/releases/v0.8.0.md`
  - `docs/sprints/2026-S21.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - machine-readable evidence carrier implementation
  - matcher runtime 实现
  - reference adapter declaration migration
  - provider compatibility / priority / fallback
  - `#294` parent closeout

## 当前停点

- `#299` 已通过 PR `#304` 合入主干，`FR-0027` formal spec 已成为 `v0.8.0` 当前双参考 slice 的 governing artifact。
- 当前执行现场位于 `issue-300-fr-0027-profile` worktree，基线为 `9feb47387c655e1d0b50474249fed577637654c8`。
- 已把 `FR-0015` formal evidence truth 扩展到 profile 级：
  - `account+proxy` -> `shared + approve_profile_for_v0_8_0`
  - `account-only` -> `shared + approve_profile_for_v0_8_0`
  - `douyin account private material` -> `adapter_only + keep_adapter_local`
  - `proxy-only` -> `rejected + reject_profile_for_v0_8_0`
  - `none` -> `rejected + reject_profile_for_v0_8_0`
- 已在 FR-0015 spec / data-model / contract / research 中新增 `ResourceRequirementProfileEvidenceRecord` 与 `ApprovedSharedResourceRequirementProfileEvidenceEntry` 的 formal shape，供 `#301/#302` 实现消费。
- 由于 formal spec 与实现必须分 PR，`syvert/resource_capability_evidence.py` 的 machine-readable carrier 落地已移出本 Work Item，改由 `#301` matcher/runtime contract 实现回合承接。

## 下一步动作

- 运行 docs / spec / scope 门禁。
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

- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-300-fr-0027-profile`
  - 结果：通过。
- `python3 scripts/open_pr.py --class spec --issue 300 --item-key CHORE-0299-fr-0027-dual-reference-profile-evidence --item-type CHORE --release v0.8.0 --sprint 2026-S21 --title "docs(spec): 收口 FR-0027 双参考 profile evidence" --closing fixes --integration-touchpoint none --shared-contract-changed no --integration-ref none --external-dependency none --merge-gate local_only --contract-surface none --joint-acceptance-needed no --integration-status-checked-before-pr no --integration-status-checked-before-merge no`
  - 结果：已创建当前受审 spec PR `#305 https://github.com/MC-and-his-Agents/Syvert/pull/305`。

## 未决风险

- `account-only` 被批准为 shared profile 的边界只适用于当前 `content_detail_by_url + target_type=url + collection_mode=hybrid` 双参考 slice，不得外推到其它 execution path。
- `adapter_only` profile truth 只能作为 evidence 事实保留，不得被后续 declaration migration 偷渡进 shared declaration。

## 回滚方式

- 使用独立 revert PR 撤销本事项对 `FR-0015` 文档、当前 exec-plan 与 release / sprint 索引的增量修改。
- 若需要重判 profile 合法性，先回到 evidence carrier，不在 matcher 或 adapter migration PR 中隐式改写 profile approval truth。

## 最近一次 checkpoint 对应的 head SHA

- `bb602f710279c9df38a66c134f3018a48808935a`
- 说明：当前 checkpoint 把 `#300` 收窄为 formal evidence truth / docs PR，并把 machine-readable carrier implementation 移交给 `#301`；后续若只补 PR / guardian / merge gate 元数据，则作为 review-sync follow-up，不把版本化 exec-plan 退化为 live head 状态面。
