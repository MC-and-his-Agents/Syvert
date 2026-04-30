# CHORE-0310-fr-0023-contract-test-entry 执行计划

## 关联信息

- item_key：`CHORE-0310-fr-0023-contract-test-entry`
- Issue：`#310`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0023-third-party-adapter-entry-path/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0310-fr-0023-contract-test-entry`
- 状态：`active`

## 目标

- 基于已合入的 `FR-0023` formal spec，交付第三方 Adapter contract test 入口，按 manifest shape、required public metadata、`FR-0027` resource declaration、fixture refs / coverage、Adapter `execute()` 行为的顺序执行 fail-closed 准入。

## 范围

- 本次纳入：
  - `tests/runtime/contract_harness/third_party_entry.py`
  - `tests/runtime/contract_harness/third_party_fixtures.py`
  - `tests/runtime/test_third_party_adapter_contract_entry.py`
  - `tests/runtime/contract_harness/__init__.py` 的最小导出更新
  - 本执行计划
- 本次不纳入：
  - `docs/specs/FR-0023-third-party-adapter-entry-path/**` formal spec 变更
  - FR-0024、FR-0025、FR-0027 formal spec 套件
  - `adapter-sdk.md`
  - Provider offer、compatibility decision、provider registry / selector / marketplace / fallback / priority / score
  - `#314` 的 AdapterCapabilityRequirement validator
  - Core runtime、TaskRecord、resource lifecycle 或 registry 的 provider-facing 字段
  - 无关 `compatibility` 未跟踪目录

## 当前停点

- 已在独立 worktree `/Users/mc/code/worktrees/syvert/issue-310-fr-0023-adapter-contract-test` 执行。
- 已核对 `AGENTS.md`、`WORKFLOW.md`、`#310` GitHub issue、`FR-0023` formal spec 与现有 contract harness / registry resource declaration 校验。
- 已新增第三方 Adapter manifest / fixture contract entry，并复用 `AdapterRegistry.from_mapping()` 消费现有 `AdapterResourceRequirementDeclarationV2` / FR-0027 校验。
- 已确认当前 FR-0027 approved profile proof 只覆盖 `xhs` / `douyin` reference slice；本事项不扩张 resource proof，不创建第二套第三方 resource declaration truth。
- guardian review 初次返回 `REQUEST_CHANGES`，阻断项为 `adapter_key` 语义边界与 adapter public metadata provider-facing 字段未显式 fail-closed；已补充对应校验与回归测试。
- guardian review 第二次返回 `REQUEST_CHANGES`，阻断项为第三方入口仍被 `xhs/douyin` reference adapter proof 绑定；已改为 harness 内第三方 profile-proof 校验，保留 FR-0027 profile tuple / evidence proof 对齐，但不要求非参考第三方 `adapter_key` 冒充 reference adapter。
- guardian review 第三次返回 `REQUEST_CHANGES`，阻断项为执行阶段硬编码 capability / target / mode 且未注入 required resource profile；已将 fixture input 扩展为 operation / capability / target / collection mode / resource profile 驱动，并在执行时构造与 FR-0027 profile 对齐的 resource bundle。
- guardian review 第四次返回 `REQUEST_CHANGES`，阻断项为 `adapter_key` 语义边界使用任意子串导致误杀，以及 error_mapping fixture 未绑定 manifest 声明；已改为 token / segment 级 key 校验，并要求 error_mapping fixture 通过 `source_error` 与 manifest `error_mapping` 对齐。
- guardian review 第五次返回 `REQUEST_CHANGES`，阻断项为纯 provider product name 仍可作为 `adapter_key`，以及 manifest 可声明未批准 capability；已显式阻断 `xhs` / `douyin` provider product key，并限制 supported_capabilities 只能使用当前 `content_detail` approved slice 且必须有 resource declaration 覆盖。
- guardian review 第六次返回 `REQUEST_CHANGES`，阻断项为非 mapping success payload 会触发未处理异常，以及 sequence 字段会误收 dict keys；已改为结构化 contract violation，并让 sequence helper 拒绝 mapping。
- guardian review 第七次返回 `REQUEST_CHANGES`，阻断项为 `resource_dependency_mode=none` 且 `required_capabilities=()` 的 FR-0027 合法 profile 会被第三方入口误拒绝；已允许 none profile 空能力集合，并补充第三方 manifest / fixture / execute 准入回归。
- guardian review 第八次返回 `REQUEST_CHANGES`，阻断项为执行结果和 resource bundle 使用 operation 而不是 adapter capability family，以及 unexpected adapter exception 会中断 contract run；已统一为 fixture capability，并把 unexpected exception 归一为结构化 runtime_contract observation。
- guardian review 第九次返回 `REQUEST_CHANGES`，阻断项为 adapter-vs-manifest metadata 对齐对 `fixture_refs` 与 resource requirement profile 顺序敏感；已改为顺序无关的语义集合比较，并补充回归。
- guardian review 第十次返回 `REQUEST_CHANGES`，阻断项为 adapter success payload 可覆盖 harness runtime context；已将 `task_id`、`adapter_key`、`capability`、`status`、`error` 设为保留字段，payload 携带这些字段时归一为 runtime_contract contract violation。
- guardian review 第十一次返回 `REQUEST_CHANGES`，阻断项为 rejected FR-0027 `none` profile 被误纳入 approved proof、`PlatformAdapterError.details` 非 mapping 会中断 contract run、`result_contract` / `error_mapping` 嵌套 carrier 可走私 provider / compatibility 字段；已移除 rejected `none` profile proof，新增平台错误 details fail-closed 归一化，并让嵌套 carrier 使用固定字段集。
- guardian review 第十二次返回 `REQUEST_CHANGES`，阻断项为 error_mapping observation 只比较 category / code，未验证 adapter reported `details.source_error` 与 fixture / manifest 绑定一致；已补充 source_error observation 校验与回归。
- guardian review 第十三次返回 `REQUEST_CHANGES`，阻断项为 manifest 可额外声明 fixtures 未覆盖的 target / collection mode、fixture input / expected nested carrier 可夹带 provider 字段、`sdk_contract_id` provider / compatibility 阻断大小写敏感；已补充 fixture coverage 反向校验、fixture nested fixed field set，并将 sdk contract 语义阻断改为大小写无关。
- guardian review 第十四次返回 `REQUEST_CHANGES`，阻断项为 provider-facing forbidden 字段集合未覆盖 registry 已禁止变体、adapter `fixture_refs` 非字符串序列会触发未处理异常、fixture 顶层非字符串 key 会触发未处理排序异常；已扩展 forbidden 字段集合，adapter fixture refs 比对前先做字符串序列校验，fixture 顶层 key 先做字符串校验。

## 下一步动作

- 提交第十四次 guardian 修复并推送 PR `#330` 新 head，重新运行 guardian review、GitHub checks 与 merge gate。
- 使用 `scripts/merge_pr.py` 受控合并后执行 issue closeout、父 FR `#295` comment、worktree 清理与分支退役。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 的第三方 Adapter 稳定接入路径提供可执行 contract test entry，使 SDK docs / migration 可以引用已落地的 manifest、fixture 与 Adapter-only 测试入口。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0023` contract test entry 实现 Work Item。
- 阻塞：
  - `#311` SDK docs / migration 需要引用该入口。
  - `#312` parent closeout 需要核对该入口已合入主干。

## 已验证项

- `gh api user --jq .login`
  - 结果：通过，当前认证用户为 `mcontheway`。
- `gh api repos/:owner/:repo/issues/310 --jq '{title:.title,state:.state,body:.body,labels:[.labels[].name],milestone:.milestone.title,assignees:[.assignees[].login]}'`
  - 结果：通过，确认 `#310` 上下文为 `CHORE-0310-fr-0023-contract-test-entry`，release=`v0.8.0`，sprint=`2026-S21`，父 FR=`#295`。
- `python3 -m pytest tests/runtime/test_third_party_adapter_contract_entry.py -q`
  - 结果：未执行通过；当前环境 `python3` 无 `pytest` 模块，改用 `unittest` 执行同等测试。
- `python3 -m unittest tests.runtime.test_third_party_adapter_contract_entry`
  - 结果：通过，19 tests。
- `python3 -m unittest tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation tests.runtime.test_adapter_resource_requirement_declaration tests.runtime.test_registry`
  - 结果：通过，50 tests。
- `python3 -m unittest tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation tests.runtime.test_adapter_resource_requirement_declaration tests.runtime.test_registry`
  - 结果：通过，69 tests。
- `python3 -m py_compile tests/runtime/contract_harness/third_party_entry.py tests/runtime/contract_harness/third_party_fixtures.py tests/runtime/test_third_party_adapter_contract_entry.py`
  - 结果：通过。
- `git diff --check`
  - 结果：通过。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过，提交 `7f82cbc` 后复跑通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 初次结果：失败，原因是本 exec-plan 的禁止范围中出现通配路径表述，被识别为缺失路径引用。
  - 修正后结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过，提交 `7f82cbc` 后复跑通过。
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-310-fr-0023-adapter-contract-test`
  - 结果：通过。
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class 为 `implementation`，变更类别为 `docs, implementation`。
- `python3 scripts/pr_guardian.py review 330 --post-review`
  - 初次结果：`REQUEST_CHANGES`，`safe_to_merge=false`。
  - 阻断项：`adapter_key` 只校验非空；adapter public metadata 可暴露 provider-facing 字段。
  - 修正：新增 `adapter_key` provider / account / environment / routing strategy 语义片段阻断；新增 adapter 对象 provider / compatibility 字段暴露阻断；新增回归测试。
  - 第二次结果：`REQUEST_CHANGES`，`safe_to_merge=false`。
  - 阻断项：第三方 manifest resource declaration 校验仍通过 reference adapter proof 绑定 `xhs/douyin`，非参考第三方 key 无法通过。
  - 修正：将 contract entry 的 resource declaration 校验改为第三方 profile-proof 校验，仍校验 FR-0027 evidence ref、capability、resource dependency mode 与 required capabilities；最小样例改为非参考 key `community_content`。
  - 第三次结果：`REQUEST_CHANGES`，`safe_to_merge=false`。
  - 阻断项：执行阶段硬编码 `content_detail` / `url` / `hybrid`；required resource profiles 未通过 fixture 输入和 resource bundle 证明。
  - 修正：fixture input 必须声明 operation、capability、target_type、target_value、collection_mode、resource_profile_key；entry 校验这些输入与 manifest metadata 及 FR-0027 profile proof execution path 一致，并向 adapter execute 注入对应 resource bundle。
  - 第四次结果：`REQUEST_CHANGES`，`safe_to_merge=false`。
  - 阻断项：`adapter_key` 禁词使用子串匹配导致合法 key 误杀；error_mapping fixture 未绑定 manifest `error_mapping` 声明。
  - 修正：`adapter_key` 改为分隔符 token 级语义阻断；error_mapping fixture 必须声明 `source_error`，且 expected category/code 必须与 manifest mapping 一致后才进入执行观测比对。
  - 第五次结果：`REQUEST_CHANGES`，`safe_to_merge=false`。
  - 阻断项：纯 provider product name 如 `xhs` / `douyin` 仍可作为 `adapter_key`；manifest 可声明当前 approved slice 之外的 capability。
  - 修正：将 `xhs` / `douyin` 纳入 token 级 adapter_key 边界阻断；manifest supported_capabilities 限制为当前 approved slice `content_detail`，并要求每个 supported capability 有 resource declaration 覆盖。
  - 第六次结果：`REQUEST_CHANGES`，`safe_to_merge=false`。
  - 阻断项：非 mapping success payload 会让 harness 抛未处理异常；sequence 字段会误收 mapping keys。
  - 修正：非 mapping success payload 生成可由 validator 归类的 contract violation envelope；sequence helper 显式拒绝 `Mapping` 输入。
- rebase 到 `origin/main` 后 `python3 -m unittest tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_registry tests.runtime.test_adapter_resource_requirement_declaration`
  - 结果：通过，69 tests。
- rebase 到 `origin/main` 后 `python3 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- rebase 到 `origin/main` 后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- rebase 到 `origin/main` 后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- rebase 到 `origin/main` 后 `python3 scripts/governance_gate.py --mode ci ...`
  - 结果：通过。
- rebase 到 `origin/main` 后 `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。
- `python3 scripts/pr_guardian.py review 330 --post-review`
  - 第七次结果：`REQUEST_CHANGES`，`safe_to_merge=false`。
  - 阻断项：第三方入口错误拒绝 FR-0027 `none` profile。
  - 修正：`required_capabilities` 在 `resource_dependency_mode=none` 时允许空 tuple，proof index 消费 FR-0027 frozen truth 中的 none profile，并补充第三方 contract entry 回归。
- 第七轮 guardian 修复后 `python3 -m unittest tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation tests.runtime.test_registry tests.runtime.test_adapter_resource_requirement_declaration`
  - 结果：通过，70 tests。
- 第七轮 guardian 修复后 `python3 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- 第七轮 guardian 修复后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- 第七轮 guardian 修复后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- 第七轮 guardian 修复后 `python3 scripts/governance_gate.py --mode ci ...`
  - 结果：通过。
- 第七轮 guardian 修复后 `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。
- `python3 scripts/pr_guardian.py review 330 --post-review`
  - 第八次结果：`REQUEST_CHANGES`，`safe_to_merge=false`。
  - 阻断项：
    - runtime envelope 与 resource bundle 使用 operation `content_detail_by_url`，而不是 adapter capability family `content_detail`。
    - unexpected adapter exception 会直接中断 contract run，而不是形成结构化 contract violation observation。
    - FR-0023 registry discovery 约束与 reference adapter baseline 约束需要在工件中明确落地位置或后续 ownership。
  - 修正：
    - resource bundle、success envelope、failed envelope 统一使用 fixture capability family。
    - unexpected exception 归一为 `runtime_contract + adapter_execution_exception` failed envelope，由 sample validator 归类为 contract violation。
    - 本工件明确：registry discovery 的既有约束由 `syvert/registry.py` 与 `tests/runtime/test_registry.py` 继续承担；本 PR 只新增第三方 contract entry 的 adapter public metadata fail-closed 校验。
    - 本工件明确：reference adapter baseline 不在 `#310` ownership 内，后续由 `#311` SDK docs / migration 与 `#312` parent closeout 消费，本 PR 不修改 reference adapters。
- 第八轮 guardian 修复后 `python3 -m unittest tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation tests.runtime.test_registry tests.runtime.test_adapter_resource_requirement_declaration`
  - 结果：通过，71 tests。
- 第八轮 guardian 修复后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- 第八轮 guardian 修复后 `python3 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- 第八轮 guardian 修复后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- 第八轮 guardian 修复后 `python3 scripts/governance_gate.py --mode ci ...`
  - 结果：通过。
- 第八轮 guardian 修复后 `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。
- `git rebase origin/main`
  - 结果：通过；同步到包含 `#314` merge commit `e456547dd4bc8145e7a1c77be1e89164a7d33fc8` 的主干。
- rebase 后 `python3 -m unittest tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation tests.runtime.test_registry tests.runtime.test_adapter_resource_requirement_declaration`
  - 结果：通过，71 tests。
- rebase 后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- rebase 后 `python3 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- rebase 后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- rebase 后 `python3 scripts/governance_gate.py --mode ci ...`
  - 结果：通过。
- rebase 后 `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。
- `python3 scripts/pr_guardian.py review 330 --post-review`
  - 第九次结果：`REQUEST_CHANGES`，`safe_to_merge=false`。
  - 阻断项：manifest 与 adapter 暴露相同 fixture refs / resource declarations / profiles 集合但顺序不同会被误判为 metadata mismatch。
  - 修正：`fixture_refs` 对齐改为排序后比较；`resource_requirement_declarations` 及 profile 对齐改为 canonical signature 排序后比较。
- 第九轮 guardian 修复后 `python3 -m unittest tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation tests.runtime.test_registry tests.runtime.test_adapter_resource_requirement_declaration`
  - 结果：通过，72 tests。
- 第九轮 guardian 修复后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- 第九轮 guardian 修复后 `python3 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- 第九轮 guardian 修复后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- 第九轮 guardian 修复后 `python3 scripts/governance_gate.py --mode ci ...`
  - 结果：通过。
- 第九轮 guardian 修复后 `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。
- `python3 scripts/pr_guardian.py review 330 --post-review`
  - 第十次结果：`REQUEST_CHANGES`，`safe_to_merge=false`。
  - 阻断项：adapter success payload 可以通过 `{**envelope, **payload}` 覆盖 harness 控制的 runtime context 字段，并仍被误判为 pass。
  - 修正：success payload 若携带 `task_id`、`adapter_key`、`capability`、`status` 或 `error`，入口返回 `runtime_contract + adapter_payload_reserved_runtime_fields` failed envelope，由 sample validator 归类为 contract violation。
- 第十轮 guardian 修复后 `python3 -m unittest tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation tests.runtime.test_registry tests.runtime.test_adapter_resource_requirement_declaration`
  - 结果：通过，73 tests。
- 第十轮 guardian 修复后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- 第十轮 guardian 修复后 `python3 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- 第十轮 guardian 修复后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- 第十轮 guardian 修复后 `python3 scripts/governance_gate.py --mode ci ...`
  - 结果：通过。
- 第十轮 guardian 修复后 `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。
- `python3 scripts/pr_guardian.py review 330 --post-review`
  - 第十一次结果：`REQUEST_CHANGES`，`safe_to_merge=false`。
  - 阻断项：
    - `fr-0027:profile:content-detail-by-url-hybrid:none` 当前 FR-0027 truth 为 rejected，但入口通过 frozen truth 误放行。
    - `PlatformAdapterError.details` 为 `None` 或非 mapping 时，`dict(error.details)` 会中断 contract run。
    - `result_contract` 与 `error_mapping` nested carrier 未固定字段集，可夹带 provider / selector / fallback 等字段。
  - 修正：
    - approved profile proof index 只消费 approved shared FR-0027 proof，不再消费 rejected frozen `none` profile。
    - `PlatformAdapterError.details` 非 mapping 时归一为 `runtime_contract + adapter_platform_error_details_invalid` failed envelope。
    - `result_contract` 与每个 `error_mapping` mapping 均校验固定字段集并拒绝 provider / compatibility 字段。
- 第十一次 guardian 修复后 `python3 -m unittest tests.runtime.test_third_party_adapter_contract_entry`
  - 结果：通过，27 tests。
- 第十一次 guardian 修复后 `python3 -m unittest tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation tests.runtime.test_registry tests.runtime.test_adapter_resource_requirement_declaration`
  - 结果：通过，77 tests。
- 第十一次 guardian 修复后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- 第十一次 guardian 修复后 `python3 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- 第十一次 guardian 修复后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- 第十一次 guardian 修复后 `python3 scripts/governance_gate.py --mode ci ...`
  - 结果：通过。
- 第十一次 guardian 修复后 `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。
- 第十一次 guardian 修复后 `git diff --check`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 330 --post-review`
  - 第十二次结果：`REQUEST_CHANGES`，`safe_to_merge=false`。
  - 阻断项：error_mapping fixture 已绑定 `expected.error.source_error` 与 manifest `error_mapping`，但 execution observation 只比较 observed category / code；adapter 可返回相同 category / code 但不同 `details.source_error` 并误通过。
  - 修正：error_mapping observation 现在要求 observed failed envelope 的 `error.details.source_error` 与 fixture expected source_error 完全一致，否则返回 `error_mapping_source_error_mismatch` contract violation。
- 第十二次 guardian 修复后 `python3 -m unittest tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation tests.runtime.test_registry tests.runtime.test_adapter_resource_requirement_declaration`
  - 结果：通过，78 tests。
- 第十二次 guardian 修复后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- 第十二次 guardian 修复后 `python3 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- 第十二次 guardian 修复后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- 第十二次 guardian 修复后 `python3 scripts/governance_gate.py --mode ci ...`
  - 结果：通过。
- 第十二次 guardian 修复后 `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。
- 第十二次 guardian 修复后 `git diff --check`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 330 --post-review`
  - 第十三次结果：`REQUEST_CHANGES`，`safe_to_merge=false`。
  - 阻断项：
    - manifest / adapter 可声明 fixtures 未覆盖的 `supported_targets` / `supported_collection_modes`。
    - fixture `input` / `expected` / `expected.error` 可夹带 provider / selector / offer 字段。
    - `sdk_contract_id` 的 provider / compatibility 语义阻断大小写敏感。
  - 修正：
    - fixtures 必须反向覆盖 manifest 声明的每个 supported target 与 collection mode，否则返回 `invalid_fixture_metadata_coverage`。
    - fixture `input`、success `expected`、error_mapping `expected` 与 `expected.error` 均使用固定字段集并拒绝 provider / compatibility 字段。
    - `sdk_contract_id` provider / compatibility 检查改为大小写无关。
- 第十三次 guardian 修复后 `python3 -m unittest tests.runtime.test_third_party_adapter_contract_entry`
  - 初次结果：失败，既有缺失 `resource_profile_key` 用例现在先命中 `fixture.input` 固定字段集；已更新断言。
- 第十三次 guardian 修复后 `python3 -m unittest tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation tests.runtime.test_registry tests.runtime.test_adapter_resource_requirement_declaration`
  - 结果：通过，83 tests。
- 第十三次 guardian 修复后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- 第十三次 guardian 修复后 `python3 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- 第十三次 guardian 修复后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- 第十三次 guardian 修复后 `python3 scripts/governance_gate.py --mode ci ...`
  - 结果：通过。
- 第十三次 guardian 修复后 `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。
- 第十三次 guardian 修复后 `git diff --check`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 330 --post-review`
  - 第十四次结果：`REQUEST_CHANGES`，`safe_to_merge=false`。
  - 阻断项：
    - adapter public metadata forbidden 字段集合缺少 `provider_selection`、`provider_capabilities`、`external_provider_ref`、`native_provider`、`browser_provider` 等 registry 已禁止变体。
    - adapter 暴露非法 `fixture_refs` 时，排序混合类型会触发未处理异常。
    - fixture 顶层非字符串字段名会触发未处理排序异常。
  - 修正：
    - `_FORBIDDEN_MANIFEST_FIELDS` 扩展到 registry provider / resource-provider forbidden 变体，并补 manifest、adapter public metadata、resource declaration、fixture carrier 回归。
    - adapter `fixture_refs` 比对前复用字符串序列校验，非法值归入 `adapter_manifest_metadata_mismatch`。
    - fixture 顶层 shape 校验先拒绝非字符串字段名。
- 第十四次 guardian 修复后 `python3 -m unittest tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation tests.runtime.test_registry tests.runtime.test_adapter_resource_requirement_declaration`
  - 结果：通过，87 tests。
- 第十四次 guardian 修复后 `python3 -m py_compile tests/runtime/contract_harness/third_party_entry.py tests/runtime/test_third_party_adapter_contract_entry.py`
  - 结果：通过。
- 第十四次 guardian 修复后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- 第十四次 guardian 修复后 `python3 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- 第十四次 guardian 修复后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- 第十四次 guardian 修复后 `python3 scripts/governance_gate.py --mode ci ...`
  - 结果：通过。
- 第十四次 guardian 修复后 `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。
- 第十四次 guardian 修复后 `git diff --check`
  - 结果：通过。

## 未决风险

- 本事项只实现 Adapter-only contract test entry，不代表 Provider offer 或 compatibility decision 已定义；相关字段继续 fail-closed。
- 当前第三方样例只消费 `FR-0027` profile tuple / proof truth，不定义第三方 adapter key 的 provider 兼容性或真实外部资源支持。
- Registry discovery 的 public metadata 输出面继续由既有 `syvert/registry.py` / `tests/runtime/test_registry.py` 覆盖；本事项只验证第三方 contract entry 不接受 provider-facing metadata。
- Reference adapter baseline 不在本事项 ownership 内；`#311` 负责 SDK docs / migration 说明，`#312` 负责父 FR closeout 时核对 reference baseline、contract entry 与 GitHub 状态。
- 若后续 `#314/#319` 并行修改相邻 validator 或 docs，本事项只消费主干合并后的事实，不覆盖其 ownership 文件。

## 回滚方式

- 使用独立 revert PR 撤销本事项新增的 contract harness entry、fixture、测试和 exec-plan 增量。
- 若发现 FR-0023 规约不足，回到 formal spec Work Item 处理，不在 implementation PR 中隐式改写 formal spec。

## 最近一次 checkpoint 对应的 head SHA

- worktree 创建基线：`589ea1e73ebce464ac16d292c180e08cee302ce5`
- implementation checkpoint：`7f82cbc71a72ea159d85b03dfdefe0e7286e6e28`
- docs_guard follow-up checkpoint：`7f2f8e6d7f15fc2fa9abcf9e0fa3eefa814a3c13`
