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
- 当前 checkpoint：已在 rebase 后 head `f2fd8aa52fa3b74cee189170d66004e5c7be1741` 新增 compatibility decision runtime、专属 fixtures 与 tests。runtime 复用既有 requirement / offer validator，合法后只比较 Adapter boundary、approved execution slice 与 resource profile canonical tuple；invalid requirement、invalid offer、compatibility mismatch、proof drift 与 decision-context provider leakage 均 fail-closed 为 `invalid_contract`，并提供无 provider identity 的 Core projection。当前分支已同步到 `origin/main=bf004b6c6877cdbee4a1c8e69dbdbf1ea764431c`。

## 下一步动作

- 运行全量 runtime tests、`py_compile` 与 spec/docs/workflow/governance/pr_scope implementation gate。
- 通过 gate 后提交中文 Conventional Commit，推送分支并用 `scripts/open_pr.py --class implementation` 创建 PR。
- 运行 guardian review，不设置超时；如有阻断，按同类阻断收敛后重跑相关验证。
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
