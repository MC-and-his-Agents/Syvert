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

## 下一步动作

- 运行新增测试、相关 runtime harness / registry 回归与必需门禁。
- 修正门禁发现的问题。
- 提交中文 Conventional Commit。
- 使用 `scripts/open_pr.py` 受控开 PR，等待 guardian review、checks 与 merge gate。
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
  - 结果：通过，10 tests。
- `python3 -m unittest tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation tests.runtime.test_adapter_resource_requirement_declaration tests.runtime.test_registry`
  - 结果：通过，50 tests。
- `python3 -m unittest tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation tests.runtime.test_adapter_resource_requirement_declaration tests.runtime.test_registry`
  - 结果：通过，60 tests。
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

## 未决风险

- 本事项只实现 Adapter-only contract test entry，不代表 Provider offer 或 compatibility decision 已定义；相关字段继续 fail-closed。
- 当前第三方样例为了复用 `FR-0027` 已批准 resource profile proof，绑定到既有 `xhs` approved slice；不得据此推断新第三方 adapter key 已被 resource proof 批准。
- 若后续 `#314/#319` 并行修改相邻 validator 或 docs，本事项只消费主干合并后的事实，不覆盖其 ownership 文件。

## 回滚方式

- 使用独立 revert PR 撤销本事项新增的 contract harness entry、fixture、测试和 exec-plan 增量。
- 若发现 FR-0023 规约不足，回到 formal spec Work Item 处理，不在 implementation PR 中隐式改写 formal spec。

## 最近一次 checkpoint 对应的 head SHA

- worktree 创建基线：`589ea1e73ebce464ac16d292c180e08cee302ce5`
- implementation checkpoint：`7f82cbc71a72ea159d85b03dfdefe0e7286e6e28`
- docs_guard follow-up checkpoint：待提交后补充。
