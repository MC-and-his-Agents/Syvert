# CHORE-0324-fr-0026-compatibility-decision-runtime 执行计划

## 关联信息

- item_key：`CHORE-0324-fr-0026-compatibility-decision-runtime`
- Issue：`#324`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0026-adapter-provider-compatibility-decision/`
- 关联 decision：
- 关联 PR：`#339`
- active 收口事项：`CHORE-0324-fr-0026-compatibility-decision-runtime`
- 状态：`active`

## 目标

- 基于已批准的 `FR-0026` formal spec，实现 `AdapterCapabilityRequirement x ProviderCapabilityOffer -> AdapterProviderCompatibilityDecision` runtime decision。
- decision runtime 必须消费 `FR-0024` requirement validator、`FR-0025` offer validator 与 `FR-0027` resource profile proof truth，覆盖 `matched`、`unmatched`、`invalid_contract` 与 fail-closed/no provider routing leakage。

## 范围

- 本次纳入：
  - `syvert/adapter_provider_compatibility_decision.py`
  - `tests/runtime/adapter_provider_compatibility_decision_fixtures.py`
  - `tests/runtime/test_adapter_provider_compatibility_decision.py`
  - `docs/exec-plans/CHORE-0324-fr-0026-compatibility-decision-runtime.md`
- 本次不纳入：
  - `syvert/adapter_capability_requirement.py`
  - `syvert/provider_capability_offer.py`
  - `docs/specs/FR-0024-adapter-capability-requirement-contract/`
  - `docs/specs/FR-0025-provider-capability-offer-contract/`
  - `docs/specs/FR-0026-adapter-provider-compatibility-decision/`
  - provider selector、router、priority、score、fallback、marketplace 或真实 provider 产品支持
  - Core provider discovery / routing、TaskRecord provider field 或 resource lifecycle provider field
  - 父 FR `#298` closeout

## 当前停点

- worktree：`/Users/mc/code/worktrees/syvert/issue-324-fr-0026-compatibility-decision-runtime`
- 分支：`issue-324-fr-0026-compatibility-decision-runtime`
- worktree 创建基线：`4e90953447e20b1fffaee0f8104f989bd043202e`
- 已核对 `AGENTS.md`、`WORKFLOW.md`、`docs/AGENTS.md`、`code_review.md`、`#324` GitHub truth 与 `FR-0026` formal spec。
- 当前 checkpoint：已在 rebase 后 head `f2fd8aa52fa3b74cee189170d66004e5c7be1741` 新增 compatibility decision runtime、专属 fixtures 与 tests。runtime 复用既有 requirement / offer validator，合法后只比较 Adapter boundary、approved execution slice 与 resource profile canonical tuple；invalid requirement、invalid offer、compatibility mismatch、proof drift 与 decision-context provider leakage 均 fail-closed 为 `invalid_contract`，并提供无 provider identity 的 Core projection。当前分支已同步到 `origin/main=107a9fb3b93864ee01ef5ea21ad4d782761fc61e`。首轮到第十轮 guardian 已收敛 top-level drift、provider-derived `decision_id`、proof evidence 解析、context drift source attribution、coverage 证据、malformed context、hyphenated provider identity、context surface drift、error evidence no-leakage、上游 validator evidence 脱敏、proof surface drift、FR-0027 adapter/tuple coverage、fixture independence、非字符串 key surface drift、unknown required capability tuple drift、dataclass context field type 与动态 provider key equality 等阻断。第十一轮 guardian 针对 `fcb3883` 返回 `REQUEST_CHANGES`，指出 `decision_id=acme-decision-001` 仍可从 `provider_key=acme` prefix 派生并进入 Core projection，且 context drift evidence 仍复制 raw expected/actual context，可能泄漏动态 provider identity。当前已在 `582c31ab16688e1b2133a7dfd1bcee1ad783f225` 将动态 identity 检查扩展为 exact / prefix / suffix / subtoken slug 匹配，并把 frozen context drift observed values 改为只暴露 `surface` 与 mismatch count，不复制 raw context。

## 下一步动作

- 运行 spec/docs/workflow/governance/pr_scope implementation gate，确认最终 head 通过。
- 推送分支并运行 guardian review，不设置超时；如有阻断，按同类阻断收敛后重跑相关验证。
- guardian、GitHub checks 与 merge gate 通过后使用受控 `scripts/merge_pr.py` 合并，完成 #324 closeout、父 FR #298 comment、分支与 worktree 清理。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 把 `FR-0026` Adapter-bound Provider compatibility decision 从 formal spec 推进为可执行 runtime contract，供 no-leakage guard、docs / evidence 与父 FR closeout 消费。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0026` 的 runtime implementation Work Item。
- 阻塞：
  - `#325` no-provider-leakage guard 需要本 decision runtime 作为可审计对象。
  - `#326` docs / evidence 需要本 runtime 输出解释边界。
  - `#327` 父 FR closeout 需要 formal spec、runtime、guard、docs / evidence 与 GitHub 状态全部一致。

## 已验证项

- `python3 scripts/create_worktree.py --issue 324 --class implementation`
  - 结果：通过；创建 worktree `/Users/mc/code/worktrees/syvert/issue-324-fr-0026-compatibility-decision-runtime`，分支 `issue-324-fr-0026-compatibility-decision-runtime`，基线 `4e90953447e20b1fffaee0f8104f989bd043202e`。
- `gh api repos/:owner/:repo/issues/324 --jq '{number,title,state,body,labels:[.labels[].name],assignees:[.assignees[].login]}'`
  - 结果：通过；确认 `#324` open，item_key=`CHORE-0324-fr-0026-compatibility-decision-runtime`，item_type=`CHORE`，release=`v0.8.0`，sprint=`2026-S21`，integration fields 为 `none/no/local_only`。
- 已核对 `FR-0026` formal spec 与 data model，确认 runtime 只消费 `FR-0024` requirement、`FR-0025` offer 与 `FR-0027` profile proof truth，不修改 carrier 本体，不实现 selector / routing / fallback。
- 已核对 `syvert.adapter_capability_requirement` 与 `syvert.provider_capability_offer` validator API，decision runtime 复用其 validation 结果作为 `invalid_requirement_contract` / `invalid_provider_offer_contract` 入口。
- `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，10 tests。
- `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer`
  - 结果：通过，54 tests。
- `python3 -m py_compile syvert/adapter_provider_compatibility_decision.py tests/runtime/adapter_provider_compatibility_decision_fixtures.py tests/runtime/test_adapter_provider_compatibility_decision.py`
  - 结果：通过。
- `git diff --check`
  - 结果：通过。
- `python3 -m unittest discover tests/runtime`
  - 结果：通过，950 tests。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-324-fr-0026-compatibility-decision-runtime`
  - 结果：通过。
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：未通过；当前新增文件尚未纳入 Git 索引，guard 基于 `HEAD` 看不到变更。待提交后按真实 head 重新运行。
- rebase 到 `origin/main=bf004b6c6877cdbee4a1c8e69dbdbf1ea764431c` 后 `python3 -m unittest discover tests/runtime`
  - 结果：通过，950 tests。
- rebase 后 `python3 -m py_compile syvert/adapter_provider_compatibility_decision.py tests/runtime/adapter_provider_compatibility_decision_fixtures.py tests/runtime/test_adapter_provider_compatibility_decision.py`
  - 结果：通过。
- rebase 后 `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- rebase 后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- rebase 后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- rebase 后 `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-324-fr-0026-compatibility-decision-runtime`
  - 结果：通过。
- rebase 后 `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。
- `python3 scripts/pr_guardian.py review 339 --post-review --json-output /tmp/syvert-pr-339-guardian.json`
  - 结果：首轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - top-level decision input drift 可以被丢弃后返回 `matched`。
    - `decision_id` 可由 provider identity / offer id 直接派生并进入 Core projection。
    - invalid proof evidence 仅按 `fr-0027:profile:` 前缀视为 resolved，未填充 `unresolved_refs`。
    - `decision_context` violation 被错误归因到 `FR-0024`。
- 已处理首轮 guardian 阻断：
  - `AdapterProviderCompatibilityDecisionInput` mapping 顶层缺字段、额外字段与 provider routing / priority / fallback drift 均 fail-closed。
  - `decision_context.decision_id` 限定为 opaque lowercase/digit/hyphen id，拒绝冒号、下划线、路径或 provider-derived offer id 形态。
  - invalid profile proof evidence 只把 approved `FR-0027` proof refs 记为 resolved；unknown / duplicate refs 进入 `invalid_contract_evidence.unresolved_refs`。
  - `decision_context` drift 统一归因 `FR-0026`。
- guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，15 tests。
- guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer`
  - 结果：通过，59 tests。
- guardian 修复后 `python3 -m unittest discover tests/runtime`
  - 结果：通过，955 tests。
- guardian 修复后 `python3 -m py_compile syvert/adapter_provider_compatibility_decision.py tests/runtime/adapter_provider_compatibility_decision_fixtures.py tests/runtime/test_adapter_provider_compatibility_decision.py`
  - 结果：通过。
- guardian 修复后 `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- guardian 修复后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- guardian 修复后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- guardian 修复后 `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-324-fr-0026-compatibility-decision-runtime`
  - 结果：通过。
- guardian 修复后 `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。
- `python3 scripts/pr_guardian.py review 339 --post-review --json-output /tmp/syvert-pr-339-guardian-rerun.json`
  - 结果：第二轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项不是新 runtime 行为失败，而是验证证据不足：
    - capability / operation / target_type / collection_mode、version / error carrier fail-closed 分支缺少覆盖。
    - `matched` / `unmatched` 测试未强断言 canonical tuple、required capabilities 与 profile proof binding。
    - profile proof coverage 用例断言过宽，未证明 FR-0027 proof coverage 失败口径。
- 已处理第二轮 guardian 阻断：
  - 新增 requirement-side capability / operation / target_type / collection_mode drift fail-closed 回归。
  - 新增 offer-side capability / operation / target_type / collection_mode、version、error_carrier drift fail-closed 回归。
  - `matched` 测试断言 `resource_dependency_mode + normalized_required_capabilities`、requirement / offer proof refs、decision evidence 与 observability proof refs。
  - 新增同名 `profile_key` 但 canonical tuple 不同的 `unmatched` 回归，防止退化为 profile_key 匹配。
  - proof coverage 测试分别断言 requirement / offer source contract、observed details、resolved / unresolved proof evidence。
- 第二轮 guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，19 tests。
- 第二轮 guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer`
  - 结果：通过，63 tests。
- 第二轮 guardian 修复后 `python3 -m unittest discover tests/runtime`
  - 结果：通过，959 tests。
- 第二轮 guardian 修复后 `python3 -m py_compile syvert/adapter_provider_compatibility_decision.py tests/runtime/adapter_provider_compatibility_decision_fixtures.py tests/runtime/test_adapter_provider_compatibility_decision.py`
  - 结果：通过。
- 第二轮 guardian 修复后 `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- 第二轮 guardian 修复后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- 第二轮 guardian 修复后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- 第二轮 guardian 修复后 `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-324-fr-0026-compatibility-decision-runtime`
  - 结果：通过。
- 第二轮 guardian 修复后 `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。
- `python3 scripts/pr_guardian.py review 339 --post-review`
  - 结果：第三轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - malformed / non-canonical `decision_context` 可被 synthetic baseline 归一后返回 `matched`。
    - requirement / offer 两侧正常共享的 approved FR-0027 proof refs 在 unrelated invalid decision 中被误判为 duplicate unresolved。
    - 小写连字符 provider identity（如 `native-xhs-detail`）可作为 opaque `decision_id` 泄漏到 Core projection。
- 已处理第三轮 guardian 阻断：
  - 非 mapping / 非 dataclass `decision_context` 归一为不可通过 frozen context 校验的 invalid carrier，按 `FR-0026` `invalid_compatibility_contract` fail-closed。
  - proof evidence duplicate 判定改为 requirement / offer 各自集合内部判定，不把两侧正常共享的 approved proof refs 视为 unresolved。
  - `decision_id` opacity 检查复用 provider leakage token，拒绝 hyphenated provider identity。
- 第三轮 guardian 修复后 targeted probe：
  - `decision_context=None` -> `invalid_contract / invalid_compatibility_contract / FR-0026`。
  - `decision_id=native-xhs-detail` -> `invalid_contract / provider_leakage_detected / FR-0026`。
  - unrelated adapter mismatch 保留 approved proof refs 为 resolved，`unresolved_refs=()`。
- 第三轮 guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，20 tests。
- `python3 scripts/pr_guardian.py review 339 --post-review`
  - 结果：第四轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - `decision_context` 额外字段会被 synthetic dataclass 归一后静默丢弃，可能返回 `matched`。
    - `rank` 与 `preferred_profile` 未纳入 FR-0026 forbidden decision tokens。
    - `invalid_contract_evidence.observed_values` 复制 forbidden field names / values，违反 FR-0026 error evidence no-leakage 语义。
- 已处理第四轮 guardian 阻断：
  - 新增 `_validate_context_surface`，对非 canonical `decision_context` mapping 的缺字段、额外字段、provider leakage 先 fail-closed，不允许 normalization 丢弃 drift。
  - 扩展 `FORBIDDEN_DECISION_TOKENS`，覆盖 `rank`、`preferred_profile`、`preferred_profiles`。
  - 将 top-level / context surface drift 与 provider leakage 的 `observed_values` 改为结构化摘要，只暴露 `surface`、缺失字段数、额外字段数与 forbidden semantics count，不复制 forbidden field name 或 raw provider / routing / priority / fallback value。
  - 补充 context extra non-forbidden field、`rank`、`preferred_profile` 与 sanitized observed values 回归。
- 第四轮 guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，21 tests。
- 第四轮 guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer`
  - 结果：通过，65 tests。
- 第四轮 guardian 修复后 `python3 -m py_compile syvert/adapter_provider_compatibility_decision.py tests/runtime/adapter_provider_compatibility_decision_fixtures.py tests/runtime/test_adapter_provider_compatibility_decision.py`
  - 结果：通过。
- 第四轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- 第四轮 guardian 修复后 `python3 -m unittest discover tests/runtime`
  - 结果：通过，961 tests。
- `python3 scripts/pr_guardian.py review 339 --post-review --json-output /tmp/syvert-pr-339-guardian-fourth-followup.json`
  - 结果：第五轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - invalid requirement / offer 分支把上游 validator `details` 原样放入 `invalid_contract_evidence.observed_values`，可泄漏 provider selector、routing、priority、fallback 或 provider identity。
- 已处理第五轮 guardian 阻断：
  - invalid requirement / offer 分支不再复制上游 validator `message` 或 `details`，避免把 FR-0024 / FR-0025 的 raw failure evidence 当作 FR-0026 decision evidence。
  - 新增 `_upstream_validation_observed_values`，只暴露 `surface`、`validation_error_code`、`detail_count` 与 `forbidden_semantics_count`。
  - 补充 requirement / offer 内嵌 `provider_selector` / `fallback_order` 的 targeted 回归，证明 fail-closed 且 observed values 不包含 forbidden field name / raw provider value。
- 第五轮 guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer`
  - 结果：通过，67 tests。
- 第五轮 guardian 修复后 `python3 -m py_compile syvert/adapter_provider_compatibility_decision.py tests/runtime/adapter_provider_compatibility_decision_fixtures.py tests/runtime/test_adapter_provider_compatibility_decision.py`
  - 结果：通过。
- 第五轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- 第五轮 guardian 修复后 `python3 -m unittest discover tests/runtime`
  - 结果：通过，963 tests。
- `python3 scripts/pr_guardian.py review 339 --post-review --json-output /tmp/syvert-pr-339-guardian-fifth-followup.json`
  - 结果：第六轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - invalid proof evidence 只从顶层 `evidence.resource_profile_evidence_refs` 推导 resolved / unresolved；profile-level proof ref 漂移但顶层 evidence 保持旧合法值时，旧顶层 ref 被误报为 resolved，真正漂移的 profile ref 没进入 `unresolved_refs`。
- 已处理第六轮 guardian 阻断：
  - 新增 profile evidence report，按 source contract 选择 requirement / offer / compatibility carrier surface。
  - 同时消费 profile-level `evidence_refs`、顶层 `evidence.resource_profile_evidence_refs` 与 `observability.proof_refs`；只有 approved、非重复且三层 surface 对齐的 ref 进入 resolved。
  - unknown、duplicate、non-unique 或 surface mismatch 的原始 refs 进入 `invalid_contract_evidence.unresolved_refs`。
  - 补充 requirement / offer profile-level only drift 回归，顶层 evidence 仍保留旧合法值时，unknown ref 与 stale ref 均 unresolved 且不进入 resolved evidence refs。
- 第六轮 guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，25 tests。
- 第六轮 guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer`
  - 结果：通过，69 tests。
- 第六轮 guardian 修复后 `python3 -m py_compile syvert/adapter_provider_compatibility_decision.py tests/runtime/adapter_provider_compatibility_decision_fixtures.py tests/runtime/test_adapter_provider_compatibility_decision.py`
  - 结果：通过。
- 第六轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- 第六轮 guardian 修复后 `python3 -m unittest discover tests/runtime`
  - 结果：通过，965 tests。
- `python3 scripts/pr_guardian.py review 339 --post-review --json-output /tmp/syvert-pr-339-guardian-sixth-followup.json`
  - 结果：第七轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - resolved proof refs 只校验 approved / surface aligned / non-duplicate，未校验 FR-0027 `reference_adapters`、capability / execution slice 与 canonical tuple。
    - `valid_compatibility_decision_input` 通过 SUT `baseline_compatibility_decision_context()` 生成 positive fixture，削弱 frozen context 回归。
- 已处理第七轮 guardian 阻断：
  - 新增 `ProfileEvidenceCarrierRef` 与 `_profile_ref_satisfies_fr0027`，resolved proof 必须满足当前 adapter coverage、capability、operation、target_type、collection_mode、resource_dependency_mode 与 normalized required capabilities。
  - 更新未覆盖 adapter 的 requirement / offer proof tests，断言 approved ref 仍因 adapter coverage 不满足而进入 `unresolved_refs`，不再进入 `resource_profile_evidence_refs` / `resolved_profile_evidence_refs`。
  - 将 compatibility decision fixture 的 `decision_context` 改为显式 frozen contract literal，不再从 SUT baseline helper 派生。
- 第七轮 guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，25 tests。
- 第七轮 guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer`
  - 结果：通过，69 tests。
- 第七轮 guardian 修复后 `python3 -m py_compile syvert/adapter_provider_compatibility_decision.py tests/runtime/adapter_provider_compatibility_decision_fixtures.py tests/runtime/test_adapter_provider_compatibility_decision.py`
  - 结果：通过。
- 第七轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- 第七轮 guardian 修复后 `python3 -m unittest discover tests/runtime`
  - 结果：通过，965 tests。
- `python3 scripts/pr_guardian.py review 339 --post-review --json-output /tmp/syvert-pr-339-guardian-seventh-followup.json`
  - 结果：第八轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - 非字符串 extra key 被 `_require_string_keys()` 过滤，顶层 input / `decision_context` 可能绕过 canonical surface drift 校验并返回 `matched`。
    - invalid proof evidence 中 `_normalize_required_capabilities()` 会丢弃 unknown capability，导致 tuple mismatch 的 proof 被误判 resolved。
- 已处理第八轮 guardian 阻断：
  - surface drift 校验新增非字符串 key 计数，顶层 input 与 decision_context 只要存在非字符串 extra key 即 fail-closed，并通过 sanitized observed values 只暴露计数。
  - proof evidence best-effort required capabilities 改为“可完整 canonicalize 才归一”；若存在 unknown / duplicate / 不可覆盖值，则保留原始 tuple，使 FR-0027 tuple comparison 失败并进入 unresolved。
  - 补充顶层 input / decision_context 非字符串 extra key 回归，以及 requirement / offer unknown required capability 绑定 approved proof ref 的 unresolved 回归。
- 第八轮 guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，29 tests。
- 第八轮 guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer`
  - 结果：通过，73 tests。
- 第八轮 guardian 修复后 `python3 -m py_compile syvert/adapter_provider_compatibility_decision.py tests/runtime/adapter_provider_compatibility_decision_fixtures.py tests/runtime/test_adapter_provider_compatibility_decision.py`
  - 结果：通过。
- 第八轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- 第八轮 guardian 修复后 `python3 -m unittest discover tests/runtime`
  - 结果：通过，969 tests。
- `python3 scripts/pr_guardian.py review 339 --post-review --json-output /tmp/syvert-pr-339-guardian-eighth-followup.json`
  - 结果：第九轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - 非法 `CompatibilityDecisionContext` dataclass 输入会被 `_normalize_context` 原样返回，非字符串 `decision_id` 进入 `_is_opaque_decision_id` 后抛 `TypeError`，未返回 fail-closed invalid_contract carrier。
- 已处理第九轮 guardian 阻断：
  - dataclass context 路径与 mapping context 路径一样执行 non-empty string / bool 归一，非法字段收敛为空值或 `False`，由 `_validate_context` 返回 `invalid_compatibility_contract`。
  - 补充 `AdapterProviderCompatibilityDecisionInput` + `CompatibilityDecisionContext(decision_id=123, ...)` 回归，证明不抛异常、返回 FR-0026 invalid_contract。
- 第九轮 guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer`
  - 结果：通过，74 tests。
- 第九轮 guardian 修复后 `python3 -m py_compile syvert/adapter_provider_compatibility_decision.py tests/runtime/adapter_provider_compatibility_decision_fixtures.py tests/runtime/test_adapter_provider_compatibility_decision.py`
  - 结果：通过。
- 第九轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- 第九轮 guardian 修复后 `python3 -m unittest discover tests/runtime`
  - 结果：通过，970 tests。
- `python3 scripts/pr_guardian.py review 339 --post-review --json-output /tmp/syvert-pr-339-guardian-ninth-followup.json`
  - 结果：第十轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - 静态 forbidden token 只覆盖已知 provider 命名，合法 offer 使用任意 `provider_key=acme` 且 `decision_id=acme` 时会返回 matched，并把 provider-derived decision_id 暴露到 Core projection。
- 已处理第十轮 guardian 阻断：
  - 新增 `_validate_context_provider_identity`，在 context frozen 校验后、requirement / offer validator 前，基于当前 raw offer 的 `provider_key` 与 `observability.offer_id` 做动态 identity slug 校验。
  - 若 decision_id 等于或可逆 slug 派生自当前 provider identity，则 fail-closed 为 `provider_leakage_detected`，observed values 只暴露布尔摘要。
  - 补充 `provider_key=acme` / `decision_id=acme` 回归，断言返回 FR-0026 provider leakage 且 Core projection fail-closed。
- 第十轮 guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer`
  - 结果：通过，75 tests。
- 第十轮 guardian 修复后 `python3 -m py_compile syvert/adapter_provider_compatibility_decision.py tests/runtime/adapter_provider_compatibility_decision_fixtures.py tests/runtime/test_adapter_provider_compatibility_decision.py`
  - 结果：通过。
- 第十轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- 第十轮 guardian 修复后 `python3 -m unittest discover tests/runtime`
  - 结果：通过，971 tests。
- `python3 scripts/pr_guardian.py review 339 --post-review --json-output /tmp/syvert-pr-339-guardian-tenth-followup.json`
  - 结果：第十一轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - `decision_id` 只拒绝 exact provider identity，`provider_key=acme` / `decision_id=acme-decision-001` 仍可 matched 并进入 Core projection。
    - context drift evidence 复制 raw `expected_context` / `actual_context`，动态 provider identity 出现在 drifted context 字段时会泄漏到 `observed_values`。
- 已处理第十一轮 guardian 阻断：
  - 动态 provider identity 校验扩展为 exact、prefix、suffix 与 subtoken slug 匹配。
  - frozen context drift observed values 改为 sanitized summary，只暴露 `surface=decision_context` 与 `mismatched_field_count`。
  - 补充 `provider_key=acme` / `decision_id=acme-decision-001` 回归，以及 `contract_version=acme` context drift 不复制 raw provider identity 的回归。
- 第十一轮 guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer`
  - 结果：通过，77 tests。
- 第十一轮 guardian 修复后 `python3 -m py_compile syvert/adapter_provider_compatibility_decision.py tests/runtime/adapter_provider_compatibility_decision_fixtures.py tests/runtime/test_adapter_provider_compatibility_decision.py`
  - 结果：通过。
- 第十一轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- 第十一轮 guardian 修复后 `python3 -m unittest discover tests/runtime`
  - 结果：通过，973 tests。

## 待验证项

- PR guardian、GitHub checks、受控 merge 与 closeout reconciliation。

## 未决风险

- `syvert.adapter_provider_compatibility_decision` 复用 requirement / offer 模块的 private normalizer 以避免复制 carrier normalization truth；若后续这些 normalizer 改名，需要同步更新 decision runtime 或公开专门的 normalization API。
- 若后续调用方把 `matched` 解释为 provider selection、priority、fallback 或 Core routing，会越过 `FR-0026` 边界；本事项通过 Core projection 与 no-leakage assertion 限制 runtime 输出，但 no-leakage guard 仍由后续 `#325` 完成。

## 回滚方式

- 使用独立 revert PR 撤销本次新增 decision runtime、fixture、测试与 exec-plan。
- 若发现 `FR-0026` decision carrier 本身不足，必须回到 formal spec Work Item 更新规约，不在 implementation PR 中隐式改写。

## 最近一次 checkpoint 对应的 head SHA

- worktree 创建基线：`4e90953447e20b1fffaee0f8104f989bd043202e`
- implementation checkpoint：`f2fd8aa52fa3b74cee189170d66004e5c7be1741`
- latest synced main：`bf004b6c6877cdbee4a1c8e69dbdbf1ea764431c`
- fourth guardian checkpoint：`c80ee5c24f637ae55e9d02ebe436611125428334`
- fifth guardian checkpoint：`2fa8e26494453a2ff40cb3095b898426d75c576c`
- sixth guardian checkpoint：`681b7906026440d2c3bc02b1f872296de1abef88`
- seventh guardian checkpoint：`a4da8087fa8c6ac6f39bd21368a2b82f1dc70282`
- eighth guardian checkpoint：`a03d8cc9b66f2f4440329233b83729622e0bfc0e`
- ninth guardian checkpoint：`206523985a096e97404395bde9a7c7834db1c155`
- tenth guardian checkpoint：`63d4472f3fed4dd9cd51eebe740087e59af3da0a`
- eleventh guardian checkpoint：`582c31ab16688e1b2133a7dfd1bcee1ad783f225`
