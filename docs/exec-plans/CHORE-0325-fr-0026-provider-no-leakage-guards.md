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
- 当前 checkpoint：已新增 `syvert.provider_no_leakage_guard` 与 focused runtime tests。guard 消费 `AdapterProviderCompatibilityDecision.evidence.adapter_bound_provider_evidence` 与 Core-facing surface payload，递归扫描 forbidden provider field token 与 adapter-bound provider identity value；合法 Core projection、registry discovery、TaskRecord payload 与 resource lifecycle payload均通过，注入 provider selector / identity / lifecycle 字段时 fail-closed。首轮 guardian 指出 forbidden token set 未覆盖 `provider_offer`、`compatibility_decision`、泛化 `selector` 与 `marketplace_listing`，当前已补齐并增加回归。第二轮 guardian 指出 provider identity 嵌入字符串、`provider_profile` 字段与真实 runtime path coverage 缺口，当前已补强 slug/subtoken 检测、补齐 token，并用 `execute_task_with_record` 覆盖真实 runtime envelope、TaskRecord 与 resource lifecycle snapshot。第三轮 guardian 指出 FR-0026 禁止语义还缺裸 `routing` 字段，当前已在 `2fb4ecb460835e3b458248bda71711709619be7a` 补齐并增加回归。第四轮 guardian 指出 camelCase/PascalCase Core payload 会绕过 forbidden field 检测，当前已在 `38c033be81dba190ee47104063f5a7a0a4583924` 新增统一 field-name 归一并补 `providerKey`、`offerId`、`selectedProvider`、`compatibilityDecision`、`resourceSupply` 回归。

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
