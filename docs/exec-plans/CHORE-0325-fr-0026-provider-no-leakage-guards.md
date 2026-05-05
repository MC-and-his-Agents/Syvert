# CHORE-0325-fr-0026-provider-no-leakage-guards 执行计划

## 关联信息

- item_key：`CHORE-0325-fr-0026-provider-no-leakage-guards`
- Issue：`#325`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 父 FR：`#298`
- 关联 spec：`docs/specs/FR-0026-adapter-provider-compatibility-decision/`
- active 收口事项：`CHORE-0325-fr-0026-provider-no-leakage-guards`
- 状态：`active`

## 目标

- 基于已合入的 `#324` compatibility decision runtime，增加 provider no-leakage guard / regression tests。
- 证明 Adapter-bound provider identity 只停留在 approved decision evidence，不进入 Core registry discovery、Core routing / projection、TaskRecord 或 resource lifecycle surface。

## 范围

- 本次纳入：
  - `syvert/provider_no_leakage_guard.py`
  - `tests/runtime/test_provider_no_leakage_guard.py`
  - `docs/exec-plans/CHORE-0325-fr-0026-provider-no-leakage-guards.md`
- 本次不纳入：
  - `docs/specs/FR-0026-adapter-provider-compatibility-decision/**`
  - `syvert/adapter_provider_compatibility_decision.py`
  - provider selector / router / fallback / priority
  - 真实 provider 样本或 provider 产品支持
  - 父 FR `#298` closeout

## 当前停点

- worktree：`/Users/mc/code/worktrees/syvert/issue-325-fr-0026-provider-no-leakage-guards`
- 分支：`issue-325-fr-0026-provider-no-leakage-guards`
- worktree 创建基线：`b3850cd588d557d2a97ce7d1526863eccbb1ac4e`
- 已确认 `#324` / PR `#339` 合入主干并关闭，父 FR `#298` 仍 open。
- 当前 checkpoint：已新增 `syvert.provider_no_leakage_guard` 与 focused runtime tests。guard 消费 `AdapterProviderCompatibilityDecision.evidence.adapter_bound_provider_evidence` 与 Core-facing surface payload，递归扫描 forbidden provider field token 与 adapter-bound provider identity value；合法 Core projection、registry discovery、TaskRecord payload 与 resource lifecycle payload均通过，注入 provider selector / identity / lifecycle 字段时 fail-closed。首轮 guardian 指出 forbidden token set 未覆盖 `provider_offer`、`compatibility_decision`、泛化 `selector` 与 `marketplace_listing`，当前已补齐并增加回归。第二轮 guardian 指出 provider identity 嵌入字符串、`provider_profile` 字段与真实 runtime path coverage 缺口，当前已补强 slug/subtoken 检测、补齐 token，并用 `execute_task_with_record` 覆盖真实 runtime envelope、TaskRecord 与 resource lifecycle snapshot。第三轮 guardian 指出 FR-0026 禁止语义还缺裸 `routing` 字段，当前已在 `2fb4ecb460835e3b458248bda71711709619be7a` 补齐并增加回归。第四轮 guardian 指出 camelCase/PascalCase Core payload 会绕过 forbidden field 检测，当前已在 `38c033be81dba190ee47104063f5a7a0a4583924` 新增统一 field-name 归一并补 `providerKey`、`offerId`、`selectedProvider`、`compatibilityDecision`、`resourceSupply` 回归。第五轮 guardian 指出 provider identity 若出现在 JSON mapping key 中会绕过 guard，当前已在 `7886c623e87915c8c14517ecb73456a701eff680` 把字符串 key 也纳入 provider identity value 检测并补回归。第六轮 guardian 指出 registry/discovery 相关字段与 provider-specific failure semantics 仍有缺口，当前已在 `707fcfbe652ae510c0751702ccd2e1874c1ec6d8` 补齐 `provider_capability`、`provider_registry_entry`、`core_provider_registry`、`core_provider_discovery` 等字段，以及 `provider_unavailable`、`provider_contract_violation`、`invalid_provider_offer` 这类 Core-facing failed-envelope value。第七轮 guardian 指出裸 `provider` / `providerId` 公共字段和 provider failure category/value 仍可漏检，当前已在 `0a5520397fd0f68140a33c5cd5a89747c669a649` 补齐。第八轮 guardian 指出 value scanning 仍会放过 Core-facing string value 中的 forbidden semantics，并且 acronym casing 如 `offerID` 会绕过；当前已在 `1de824ca31d808189322ff47f8783d1477a1ded8` 将 value 语义检测改为归一后精确匹配 forbidden semantics，并修复 acronym 归一。第九轮 guardian 暴露出该规则会误伤合法 task id / error message；当前已在 `dd135377062cf8bab098ce73e44e19a0ad036127` 拆分“provider identity / provider failure / forbidden semantics”三类 value 规则，并把 failure_category=provider 变成 path-aware 校验。第十轮 guardian 指出 `route:provider_selector` / `policy/routing_policy` 这类标点分隔的嵌入式 forbidden semantics 仍可绕过，当前已在 `4154ab427dff07ea9475d9210f81402b40b521d3` 统一把非字母数字都视作 value token 分隔符。第十一轮 guardian 指出 provider identity value 的 camelCase/PascalCase 形式，以及 provider lifecycle/pool 相关禁止语义作为 string value 仍有缺口，当前已在 `778471d5d7f95ca5e8b94f5545694c24fedf00ad` 补齐。第十二轮 guardian 指出 FR-0021 / FR-0023 已禁止的 provider metadata carrier 同义字段仍可绕过，当前已把 `provider_capabilities`、`external_provider_ref`、`native_provider`、`browser_provider`、`resource_provider` 纳入字段名与字符串值禁止语义，并补充 snake_case / camelCase 回归。第十三轮 guardian 指出 provider failure category 的 camelCase / PascalCase path 未复用字段名归一，当前已把 failure category value 判断切换到归一后的 path field name，并补充 `failureCategory` / `FailureCategory` / `failure-category` 回归。第十四轮 guardian 指出真实 runtime envelope 使用 `error.category` 且 FR-0026 禁止 runtime 技术字段，当前已让 `category=provider/provider_failure` fail-closed，并把 `playwright`、`cdp`、`chromium`、`browser_profile`、`network_tier`、`transport` 纳入字段名与字符串值禁止语义。第十五轮 guardian 指出 provider identity 字段名作为字符串值、以及 broader runtime technical `browser` / `network` 仍可漏检，当前已补齐 `provider_key`、`provider_id`、`offer_id`、`browser`、`network` 的 value / field token 回归。第十六轮 guardian 指出 `offer`、`decision_detail(s)` carrier 未禁止，且真实路径正向证据缺 Core routing surface；当前已补齐这些 carrier，并把 `project_compatibility_decision_for_core(decision)` 作为 `core_routing_projection` 纳入 real runtime no-leakage evidence。

## 下一步动作

- 新增 guard 模块与 runtime tests。
- 运行相关 runtime tests、全量 runtime discover、`py_compile`、`git diff --check` 与 spec/docs/workflow/governance/pr_scope implementation gates。
- 提交中文 Conventional Commit，使用 `scripts/open_pr.py` 开 PR。
- guardian review 通过且 checks 全绿后使用受控 merge，完成 #325 closeout 并更新父 FR #298 comment。

## 已验证项

- `python3 scripts/create_worktree.py --issue 325 --class implementation`
  - 结果：通过；创建 worktree `/Users/mc/code/worktrees/syvert/issue-325-fr-0026-provider-no-leakage-guards`，分支 `issue-325-fr-0026-provider-no-leakage-guards`，基线 `b3850cd588d557d2a97ce7d1526863eccbb1ac4e`。
- `#324` / PR `#339`
  - 结果：已合入主干并关闭，主干 `b3850cd` 包含 FR-0026 decision runtime。
- `python3 -m unittest tests.runtime.test_provider_no_leakage_guard`
  - 结果：通过，7 tests。
- `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，42 tests。
- `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- `git diff --check`
  - 结果：通过。
- `python3 -m unittest discover tests/runtime`
  - 结果：通过，982 tests。
- 提交后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，42 tests。
- 提交后 `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- 提交后 `git diff --check HEAD~2..HEAD`
  - 结果：通过。
- 提交后 `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。
- 提交后 `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- 提交后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- 提交后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- 提交后 `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-325-fr-0026-provider-no-leakage-guards`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 340 --post-review --json-output /tmp/syvert-pr-340-guardian.json`
  - 结果：首轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - no-leakage guard 漏掉 FR-0026 明确禁止的 provider / decision synonyms：`provider_offer`、`compatibility_decision`、泛化 `selector`、`marketplace_listing`。
- guardian 修复后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，43 tests。
- guardian 修复后 `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- guardian 修复后 `git diff --check`
  - 结果：通过。
- guardian 修复后 `python3 -m unittest discover tests/runtime`
  - 结果：通过，983 tests。
- `python3 scripts/pr_guardian.py review 340 --post-review --json-output /tmp/syvert-pr-340-guardian-followup.json`
  - 结果：第二轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - provider identity 嵌入组合字符串时会漏检，例如 `route:native_xhs_detail`、`offer:native-xhs-detail-001`。
    - forbidden token set 未覆盖 FR-0026 场景 7 明确禁止的 `provider_profile`。
    - 正向测试主要是手工干净 payload，未证明真实 Core routing / TaskRecord / resource lifecycle 生成路径 no-leakage。
- 第二轮 guardian 修复后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard`
  - 结果：通过，10 tests。
- 第二轮 guardian 修复后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，45 tests。
- 第二轮 guardian 修复后 `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- 第二轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- 第二轮 guardian 修复后 `python3 -m unittest discover tests/runtime`
  - 结果：通过，985 tests。
- `python3 scripts/pr_guardian.py review 340 --post-review --json-output /tmp/syvert-pr-340-guardian-followup-2.json`
  - 结果：第三轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - no-leakage guard 漏检 FR-0026 禁止语义中的裸 `routing` 字段。
- 第三轮 guardian 修复后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，45 tests。
- 第三轮 guardian 修复后 `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- 第三轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 340 --post-review --json-output /tmp/syvert-pr-340-guardian-followup-3.json`
  - 结果：第四轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - no-leakage field detection 漏掉 camelCase/PascalCase provider fields，例如 `providerKey`、`offerId`、`selectedProvider`、`compatibilityDecision`、`resourceSupply`。
- 第四轮 guardian 修复后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，46 tests。
- 第四轮 guardian 修复后 `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- 第四轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 340 --post-review --json-output /tmp/syvert-pr-340-guardian-followup-4.json`
  - 结果：第五轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - provider identity 出现在 mapping key 时会绕过 no-leakage guard，例如 `{\"routes\": {\"native_xhs_detail\": \"enabled\"}}`。
- 第五轮 guardian 修复后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，47 tests。
- 第五轮 guardian 修复后 `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- 第五轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 340 --post-review --json-output /tmp/syvert-pr-340-guardian-followup-5.json`
  - 结果：第六轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - guard 漏掉 Core registry/discovery 词汇：`provider_capability`、`provider_registry_entry`、`core_provider_registry`、`core_provider_discovery` 等。
    - guard 未阻断 Core-facing provider-specific failure value：`provider_unavailable`、`provider_contract_violation`、`invalid_provider_offer`。
- 第六轮 guardian 修复后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，48 tests。
- 第六轮 guardian 修复后 `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- 第六轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 340 --post-review --json-output /tmp/syvert-pr-340-guardian-followup-6.json`
  - 结果：第七轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - no-leakage guard 漏掉裸 `provider` / `providerId` 这类 provider-specific Core public field。
    - provider failure category/value 仍可进入 Core-facing envelope，例如 `provider`、`provider_failure`。
- 第七轮 guardian 修复后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，48 tests。
- 第七轮 guardian 修复后 `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- 第七轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 340 --post-review --json-output /tmp/syvert-pr-340-guardian-followup-7.json`
  - 结果：第八轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - Core-facing string value 中出现 forbidden semantics 时会漏检，例如 `provider_selector`、`selected_provider`、`routing_policy`。
    - acronym casing 如 `offerID` / `OfferID` 仍可绕过 forbidden field 检测。
- 第八轮 guardian 修复后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，49 tests。
- 第八轮 guardian 修复后 `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- 第八轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 340 --post-review --json-output /tmp/syvert-pr-340-guardian-followup-8.json`
  - 结果：第九轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - 收紧后的 value scanning 会误伤合法 Core payload，例如 `task-no-provider`、`compatibility decision unmatched`。
- 第九轮 guardian 修复后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，49 tests。
- 第九轮 guardian 修复后 `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- 第九轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 340 --post-review --json-output /tmp/syvert-pr-340-guardian-followup-9.json`
  - 结果：第十轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - 标点分隔的嵌入式 forbidden semantics 仍可绕过，例如 `route:provider_selector`、`mode:selected_provider`、`policy/routing_policy`。
- 第十轮 guardian 修复后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，49 tests。
- 第十轮 guardian 修复后 `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- 第十轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 340 --post-review --json-output /tmp/syvert-pr-340-guardian-followup-10.json`
  - 结果：第十一轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - provider identity value 的 camelCase/PascalCase 形式如 `nativeXhsDetail`、`NativeXhsDetail` 仍可绕过。
    - `provider_lifecycle`、`provider_lease`、`resource_pool`、`account_pool`、`proxy_pool` 作为 string value 仍可泄漏。
- 第十一轮 guardian 修复后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，49 tests。
- 第十一轮 guardian 修复后 `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- 第十一轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 340 --post-review --json-output /tmp/syvert-pr-340-guardian-followup-ef00682.json`
  - 结果：第十二轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - no-leakage guard 漏掉既有 provider-facing metadata alias：`provider_capabilities`、`external_provider_ref`、`native_provider`、`browser_provider`、`resource_provider`。
- 第十二轮 guardian 修复后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，49 tests。
- 第十二轮 guardian 修复后 `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- 第十二轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 340 --post-review --json-output /tmp/syvert-pr-340-guardian-followup-bec50ae.json`
  - 结果：第十三轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - provider failure category value 的 `failureCategory` / PascalCase 等字段形态绕过 no-leakage guard。
- 第十三轮 guardian 修复后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，49 tests。
- 第十三轮 guardian 修复后最小复现命令验证 `failure_category`、`failureCategory`、`FailureCategory`、`failure-category`
  - 结果：全部返回 `failed`，并记录 forbidden value path。
- 第十三轮 guardian 修复后 `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- 第十三轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 340 --post-review --json-output /tmp/syvert-pr-340-guardian-followup-eaf10c2.json`
  - 结果：第十四轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - 真实 runtime failed envelope 使用 `error.category`，`category=provider` / `provider_failure` 仍可泄漏。
    - FR-0026 禁止的 Playwright / CDP / Chromium / browser profile / network tier / transport runtime 技术字段未纳入 guard。
- 第十四轮 guardian 修复后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，49 tests。
- 第十四轮 guardian 修复后 `python3 -m unittest discover tests/runtime`
  - 结果：通过，989 tests。
- 第十四轮 guardian 修复后最小复现命令验证 `error.category`、`runtime_contract` 与 runtime 技术字段
  - 结果：`category=provider/provider_failure` 与 runtime 技术字段返回 `failed`；合法 `category=runtime_contract` 返回 `passed`。
- 第十四轮 guardian 修复后 `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- 第十四轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 340 --post-review --json-output /tmp/syvert-pr-340-guardian-followup-40e3a30.json`
  - 结果：第十五轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - `provider_key`、`offer_id`、`provider_id` 作为 string value carrier 时绕过 guard。
    - runtime technical broader terms `browser`、`network` 未与 compatibility decision forbidden semantics 对齐。
- 第十五轮 guardian 修复后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，49 tests。
- 第十五轮 guardian 修复后 `python3 -m unittest discover tests/runtime`
  - 结果：通过，989 tests。
- 第十五轮 guardian 修复后最小复现命令验证 `provider_key`、`offer_id`、`provider_id`、`browser`、`network`
  - 结果：全部返回 `failed`。
- 第十五轮 guardian 修复后 `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- 第十五轮 guardian 修复后 `git diff --check`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 340 --post-review --json-output /tmp/syvert-pr-340-guardian-followup-635c659.json`
  - 结果：第十六轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - `offer`、`decision_detail`、`decision_details` Core-facing carrier 未被 guard 禁止。
    - real runtime positive evidence 未显式纳入 Core routing/projection surface。
- 第十六轮 guardian 修复后 `python3 -m unittest tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，49 tests。
- 第十六轮 guardian 修复后 `python3 -m unittest discover tests/runtime`
  - 结果：通过，989 tests。
- 第十六轮 guardian 修复后最小复现命令验证 `offer`、`decision_detail`、`decision_details`
  - 结果：全部返回 `failed`。
- 第十六轮 guardian 修复后 `python3 -m py_compile syvert/provider_no_leakage_guard.py tests/runtime/test_provider_no_leakage_guard.py`
  - 结果：通过。
- 第十六轮 guardian 修复后 `git diff --check`
  - 结果：通过。

## 待验证项

- PR guardian、GitHub checks、受控 merge 与 closeout reconciliation。

## 风险

- guard 只能证明本仓 Core-facing surface 的 provider no-leakage，不定义真实 provider 产品支持。
- 若后续新增 Core-facing surface，必须显式纳入本 guard 或新增 follow-up。

## 回滚方式

- 使用独立 revert PR 撤销 no-leakage guard 模块、测试与 exec-plan。
- 若发现 no-leakage 边界需要改变，回到 `FR-0026` formal spec Work Item，不在 implementation PR 中改写规约。

## 最近一次 checkpoint 对应的 head SHA

- worktree 创建基线：`b3850cd588d557d2a97ce7d1526863eccbb1ac4e`
- implementation checkpoint：`bbc19ea1b5d9a48cf80def857e14d5b440dc277b`
- guardian follow-up checkpoint：`35c73cd4ac1fe7eddd8dc4c96ed8abcf18ec452b`
- second guardian follow-up checkpoint：`ee73d8fb45432cf34dcc5a8e71cce008f03c7dde`
- third guardian follow-up checkpoint：`2fb4ecb460835e3b458248bda71711709619be7a`
- fourth guardian follow-up checkpoint：`38c033be81dba190ee47104063f5a7a0a4583924`
- fifth guardian follow-up checkpoint：`7886c623e87915c8c14517ecb73456a701eff680`
- sixth guardian follow-up checkpoint：`707fcfbe652ae510c0751702ccd2e1874c1ec6d8`
- seventh guardian follow-up checkpoint：`0a5520397fd0f68140a33c5cd5a89747c669a649`
- eighth guardian follow-up checkpoint：`1de824ca31d808189322ff47f8783d1477a1ded8`
- ninth guardian follow-up checkpoint：`dd135377062cf8bab098ce73e44e19a0ad036127`
- tenth guardian follow-up checkpoint：`4154ab427dff07ea9475d9210f81402b40b521d3`
- eleventh guardian follow-up checkpoint：`778471d5d7f95ca5e8b94f5545694c24fedf00ad`
- twelfth guardian follow-up checkpoint：`a1404921df1f7cfb302660870555975be6f7f0d4`
- thirteenth guardian follow-up checkpoint：`c8cc62e7e4805043a303a04a9bd0526972858dcf`
- fourteenth guardian follow-up checkpoint：`1ad66bf194bdc9566f7524be3cf723b27c1864cc`
- fifteenth guardian follow-up checkpoint：`c94e921376d8fce9c3b786e2c7d8f321666a997f`
