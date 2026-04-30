# CHORE-0314-fr-0024-manifest-fixture-validator 执行计划

## 关联信息

- item_key：`CHORE-0314-fr-0024-manifest-fixture-validator`
- Issue：`#314`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0024-adapter-capability-requirement-contract/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0314-fr-0024-manifest-fixture-validator`
- 状态：`active`

## 目标

- 基于已合入的 `FR-0024` formal spec，实现 `AdapterCapabilityRequirement` canonical carrier validator 与 manifest fixture 测试入口。
- validator 必须消费 `FR-0027` 的 `AdapterResourceRequirementDeclarationV2` / approved shared profile proof truth，不复制 resource profile matcher 逻辑。
- validator 输出稳定区分合法 requirement declared、合法但当前前提未满足的 unmatched、非法 carrier 的 `invalid_contract` / `invalid_resource_requirement`。

## 范围

- 本次纳入：
  - `syvert/adapter_capability_requirement.py`
  - `tests/runtime/adapter_capability_requirement_fixtures.py`
  - `tests/runtime/test_adapter_capability_requirement.py`
  - `docs/exec-plans/CHORE-0314-fr-0024-manifest-fixture-validator.md`
- 本次不纳入：
  - `docs/specs/FR-0024-adapter-capability-requirement-contract/**`
  - Provider capability offer formal spec 或实现
  - `tests/runtime/contract_harness/**`
  - `syvert/runtime.py` / `syvert/registry.py` 大范围改动
  - Provider offer、compatibility decision、selector、priority、fallback carrier
  - reference adapter requirement migration
  - 关闭父 FR `#296`

## 当前停点

- worktree：`/Users/mc/code/worktrees/syvert/issue-314-fr-0024-adapter-requirement-manifest-validator`
- 分支：`issue-314-fr-0024-adapter-requirement-manifest-validator`
- 原始 worktree 创建基线：`589ea1e73ebce464ac16d292c180e08cee302ce5`
- 已核对 `AGENTS.md`、`WORKFLOW.md`、`#314` GitHub truth 与 `FR-0024` formal spec。
- 当前 checkpoint：PR `#329` 首次 guardian review 返回 `REQUEST_CHANGES`，已修复两个阻断项并补充复现测试；修复提交 `01c0bf982bfcfb45af4aa4d603e51c719556af7f` 的目标测试与门禁已通过，下一步推送并重新运行 guardian。

## 下一步动作

- 推送 PR `#329` 新 head，重新运行 guardian。
- guardian 与 checks 通过后受控合并。
- 合并后确认 `#314` closeout、更新父 FR `#296` comment、清理 worktree 并退役分支。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 把 `FR-0024` Adapter capability requirement 从 formal carrier 推进为可执行 validator / fixture truth，供后续 reference adapter migration 与父 FR closeout 消费。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0024` 的 manifest fixture validator implementation Work Item。
- 阻塞：
  - `#315` reference adapter requirement migration 需要本 validator 作为迁移前的 manifest truth。
  - `#316` 父 FR closeout 需要本 validator 与 migration 主干事实。
  - 后续 Provider offer / compatibility decision 需要稳定 requirement input，不得反向改写本 carrier。

## 已验证项

- `python3 scripts/create_worktree.py --issue 314 --class implementation`
  - 结果：通过；创建 worktree `/Users/mc/code/worktrees/syvert/issue-314-fr-0024-adapter-requirement-manifest-validator`，分支 `issue-314-fr-0024-adapter-requirement-manifest-validator`，基线 `589ea1e73ebce464ac16d292c180e08cee302ce5`。
- `gh api user --jq .login`
  - 结果：通过；确认本机 `gh` keyring 可用，未全局导出 `GH_TOKEN` / `GITHUB_TOKEN`。
- `gh api repos/:owner/:repo/issues/314 --jq '{number,title,state,body,labels:[.labels[].name],assignees:[.assignees[].login],milestone:(.milestone.title // null)}'`
  - 结果：通过；确认 `#314` open，item_key=`CHORE-0314-fr-0024-manifest-fixture-validator`，item_type=`CHORE`，release=`v0.8.0`，sprint=`2026-S21`，integration fields 为 `none/no/local_only`。
- 已核对 `FR-0024` formal spec 与 data model，确认字段、禁止字段、declared / unmatched / invalid 语义。
- 已核对 `syvert/registry.py` 与 `syvert/runtime.py` 的 `FR-0027` truth，确认 resource requirement validation 通过 `AdapterRegistry.from_mapping` 与 `match_resource_capabilities` 消费。
- `python -m unittest tests.runtime.test_adapter_capability_requirement`
  - 结果：未运行；本机没有 `python` 命令。
- `python3 -m unittest tests.runtime.test_adapter_capability_requirement`
  - 结果：通过，13 tests。
- `python3 -m unittest tests.runtime.test_adapter_resource_requirement_declaration`
  - 结果：通过，10 tests。
- `python3 -m unittest tests.runtime.test_resource_capability_matcher`
  - 结果：通过，17 tests。
- `python3 -m unittest tests.runtime.test_registry`
  - 结果：通过，15 tests。
- `python3 -m unittest discover tests/runtime`
  - 结果：通过，859 tests。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- 提交 `17c8f3d` 后重跑 `python3 scripts/docs_guard.py --mode ci`
  - 结果：首次未通过；原因是 exec-plan 的禁止范围表述引用了尚不存在的 `FR-0025` spec 路径。处理：改为非路径文本表述 `Provider capability offer formal spec 或实现`，避免把未来路径伪装为当前仓内真相。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：提交态重跑通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：提交态重跑通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：提交态重跑通过。
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-314-fr-0024-adapter-requirement-manifest-validator`
  - 结果：通过。
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。
- `python3 scripts/open_pr.py --class implementation --issue 314 ...`
  - 结果：首次未通过；原因是受控脚本不负责推送，本地分支尚无同名远端 head。处理：执行 `git push -u origin issue-314-fr-0024-adapter-requirement-manifest-validator` 后重试。
- `git push -u origin issue-314-fr-0024-adapter-requirement-manifest-validator`
  - 结果：通过，远端分支创建。
- `python3 scripts/open_pr.py --class implementation --issue 314 ...`
  - 结果：通过，创建 PR `#329`。
- `python3 scripts/pr_guardian.py review 329 --post-review`
  - 结果：`REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - canonical dataclass 输入中的 raw `resource_requirement` 未归一化，可能抛出 `AttributeError` 而非稳定返回 `invalid_resource_requirement`。
    - `capability_requirement_evidence_refs` 只校验非空/去重，任意字符串可冒充 requirement 级 evidence。
- 已处理 guardian 阻断：
  - `AdapterCapabilityRequirement` dataclass 输入现在会重新归一化 nested execution/evidence/lifecycle/observability 与 `resource_requirement`，非法资源声明稳定返回 `invalid_resource_requirement`。
  - `capability_requirement_evidence_refs` 现在限制为 `FR-0024` formal spec / manifest fixture / migration / closeout evidence 前缀。
  - 新增对应复现测试。
- guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_capability_requirement`
  - 结果：通过，15 tests。
- guardian 修复后 `python3 -m unittest tests.runtime.test_adapter_resource_requirement_declaration`
  - 结果：通过，10 tests。
- guardian 修复后 `python3 -m unittest tests.runtime.test_resource_capability_matcher`
  - 结果：通过，17 tests。
- guardian 修复后 `python3 -m unittest tests.runtime.test_registry`
  - 结果：通过，15 tests。
- guardian 修复后 `python3 -m unittest discover tests/runtime`
  - 结果：通过，861 tests。
- guardian 修复提交 `01c0bf982bfcfb45af4aa4d603e51c719556af7f` 后 `python3 -m unittest tests.runtime.test_adapter_capability_requirement`
  - 结果：通过，15 tests。
- guardian 修复提交 `01c0bf982bfcfb45af4aa4d603e51c719556af7f` 后 `python3 -m unittest tests.runtime.test_adapter_resource_requirement_declaration`
  - 结果：通过，10 tests。
- guardian 修复提交 `01c0bf982bfcfb45af4aa4d603e51c719556af7f` 后 `python3 -m unittest tests.runtime.test_resource_capability_matcher`
  - 结果：通过，17 tests。
- guardian 修复提交 `01c0bf982bfcfb45af4aa4d603e51c719556af7f` 后 `python3 -m unittest tests.runtime.test_registry`
  - 结果：通过，15 tests。
- guardian 修复提交 `01c0bf982bfcfb45af4aa4d603e51c719556af7f` 后 `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- guardian 修复提交 `01c0bf982bfcfb45af4aa4d603e51c719556af7f` 后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- guardian 修复提交 `01c0bf982bfcfb45af4aa4d603e51c719556af7f` 后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- guardian 修复提交 `01c0bf982bfcfb45af4aa4d603e51c719556af7f` 后 `python3 scripts/governance_gate.py --mode ci ...`
  - 结果：通过。
- guardian 修复提交 `01c0bf982bfcfb45af4aa4d603e51c719556af7f` 后 `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。

## 待验证项

- PR push、guardian review、GitHub checks、受控 merge、closeout reconciliation。

## 未决风险

- 若 validator 后续复制 `FR-0027` matcher 规则，会形成 resource requirement second truth。
- 若合法 requirement 输出被解释为 Provider compatible，会提前越过 Provider offer / compatibility decision 边界。
- 若 observability / lifecycle 接受 provider、selector、fallback 或浏览器技术字段，会污染 Adapter capability requirement canonical surface。

## 回滚方式

- 使用独立 revert PR 撤销本次新增 validator、fixture、测试与 exec-plan。
- 若发现 `FR-0024` carrier 本身不足，必须回到 formal spec Work Item 更新规约，不在 implementation PR 中隐式改写。

## 最近一次 checkpoint 对应的 head SHA

- 初始 implementation checkpoint：`589ea1e73ebce464ac16d292c180e08cee302ce5`
- implementation checkpoint：`17c8f3d`
- validation follow-up checkpoint：`295f560bb1b21975b30701080b7aa4eb1a2c7774`
- guardian fix checkpoint：`01c0bf982bfcfb45af4aa4d603e51c719556af7f`
