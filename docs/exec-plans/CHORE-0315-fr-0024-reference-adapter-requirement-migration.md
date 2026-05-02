# CHORE-0315-fr-0024-reference-adapter-requirement-migration 执行计划

## 关联信息

- item_key：`CHORE-0315-fr-0024-reference-adapter-requirement-migration`
- Issue：`#315`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0024-adapter-capability-requirement-contract/`
- 关联 decision：
- 关联 PR：`#332`
- active 收口事项：`CHORE-0315-fr-0024-reference-adapter-requirement-migration`
- 状态：`active`

## 目标

- 将小红书与抖音 reference adapter 的 `content_detail_by_url + url + hybrid` requirement baseline 迁移到 `FR-0024` `AdapterCapabilityRequirement` carrier。
- baseline 必须复用现有 `FR-0027` `AdapterResourceRequirementDeclarationV2` / profile proof truth，不维护第二套 resource profile 声明。
- validator 回归必须覆盖 reference baseline 的 declared、unmatched 与 fail-closed 行为。

## 范围

- 本次纳入：
  - `syvert/adapter_capability_requirement.py`
  - `syvert/adapters/xhs.py`
  - `syvert/adapters/douyin.py`
  - `tests/runtime/test_reference_adapter_capability_requirement_baseline.py`
  - `docs/exec-plans/CHORE-0315-fr-0024-reference-adapter-requirement-migration.md`
- 本次不纳入：
  - `tests/runtime/contract_harness/**`
  - Provider offer、compatibility decision、selector、priority、fallback
  - 新共享能力词汇、resource profile truth 或 matcher 语义
  - 父 FR `#296` closeout

## 当前停点

- worktree：`/Users/mc/code/worktrees/syvert/issue-315-fr-0024-adapter-requirement`
- 分支：`issue-315-fr-0024-adapter-requirement`
- 原始 worktree 创建基线：`e456547dd4bc8145e7a1c77be1e89164a7d33fc8`
- 已核对 `AGENTS.md`、`WORKFLOW.md`、`#315` GitHub truth、`FR-0024` formal spec 与现有 `#314` validator 实现。
- 当前 checkpoint：已实现 xhs / douyin reference adapter requirement baseline，复用同一 `FR-0027` resource declaration truth，并通过专用 baseline、validator、registry/resource、完整 runtime regression 与本地治理门禁；PR `#332` 已创建，等待 guardian review、GitHub checks 与受控 merge。

## 下一步动作

- guardian review、GitHub checks 与受控 merge 通过后，完成 issue closeout/comment 并退役分支/worktree。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 把 `FR-0024` Adapter capability requirement 从 validator truth 推进为双 reference adapter 主干 baseline，使后续 `FR-0026` decision input 与父 FR closeout 可引用同一 requirement truth。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0024` 的 reference adapter requirement migration Work Item。
- 阻塞：
  - `#316` 父 FR closeout 需要 reference adapter migration 主干事实。
  - 后续 `#298` / `FR-0026` 需要可直接引用的 Adapter requirement baseline。

## 已验证项

- `python3 scripts/create_worktree.py --issue 315 --class implementation`
  - 结果：通过；创建 worktree `/Users/mc/code/worktrees/syvert/issue-315-fr-0024-adapter-requirement`，分支 `issue-315-fr-0024-adapter-requirement`，基线 `e456547dd4bc8145e7a1c77be1e89164a7d33fc8`。
- `gh api user --jq .login`
  - 结果：通过；确认本机 `gh` keyring 可用，未全局导出 `GH_TOKEN` / `GITHUB_TOKEN`。
- `gh api repos/:owner/:repo/issues/315 --jq '{number,title,state,body,labels:[.labels[].name],assignees:[.assignees[].login]}'`
  - 结果：通过；确认 `#315` open，item_key=`CHORE-0315-fr-0024-reference-adapter-requirement-migration`，item_type=`CHORE`，release=`v0.8.0`，sprint=`2026-S21`，integration fields 为 `none/no/local_only`。
- 已核对 `FR-0024` formal spec 与 data model，确认 reference adapter migration 必须消费 `AdapterCapabilityRequirement`，且不得新增 Provider offer / compatibility decision / fallback / priority。
- 已核对 `syvert/adapter_capability_requirement.py`、`tests/runtime/adapter_capability_requirement_fixtures.py`、`tests/runtime/test_adapter_capability_requirement.py` 与 `FR-0027` resource declaration baseline。
- `python3 -m unittest tests.runtime.test_reference_adapter_capability_requirement_baseline`
  - 结果：通过，4 tests。
- `python3 -m unittest tests.runtime.test_adapter_capability_requirement`
  - 结果：通过，23 tests。
- `python3 -m unittest tests.runtime.test_registry tests.runtime.test_resource_capability_evidence`
  - 结果：通过，42 tests。
- `python3 -m unittest discover tests/runtime`
  - 结果：通过，873 tests。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- 提交 `932775ef206346319b0c7907006b854fbbdd213d`
  - 结果：已生成实现 checkpoint，提交信息 `feat(runtime): 迁移 FR-0024 参考适配器需求基线`。
- 提交态 `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- 提交态 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- 提交态 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- 提交态 `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-315-fr-0024-adapter-requirement`
  - 结果：通过。
- 提交态 `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。
- `git push -u origin issue-315-fr-0024-adapter-requirement`
  - 结果：通过，远端分支已创建并跟踪。
- `python3 scripts/open_pr.py --class implementation --issue 315 ...`
  - 结果：通过，创建 PR `#332`。

## 待验证项

- PR guardian、GitHub checks、受控 merge、issue closeout 与 worktree retirement。

## 未决风险

- 若 reference adapter requirement baseline 复制 resource profile / proof truth，会和 `FR-0027` 形成第二套 resource requirement truth。
- 若 requirement carrier 被误读为 Provider compatible，会提前越过 Provider offer 与 compatibility decision 边界。
- 若后续在本 PR 中触碰 `tests/runtime/contract_harness/**`，会与 `#310` 的 ownership 冲突。

## 回滚方式

- 通过独立 revert PR 撤销 reference adapter requirement migration；不得保留影子声明与 formal contract 并行。

## 最近一次 checkpoint 对应的 head SHA

- implementation checkpoint：`932775ef206346319b0c7907006b854fbbdd213d`
