# CHORE-0320-fr-0025-offer-manifest-validator 执行计划

## 关联信息

- item_key：`CHORE-0320-fr-0025-offer-manifest-validator`
- Issue：`#320`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0025-provider-capability-offer-contract/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0320-fr-0025-offer-manifest-validator`
- 状态：`active`

## 目标

- 基于已合入的 `FR-0025` formal spec，实现 `ProviderCapabilityOffer` canonical carrier validator 与 manifest fixture 测试入口。
- validator 必须消费 `FR-0027` approved shared profile proof truth，验证 provider key、adapter binding、capability offer、resource support、error carrier、version、evidence、lifecycle、observability 与 fail-closed 边界。
- validator 输出稳定区分合法 offer declared 与非法 carrier invalid；非法 carrier 统一映射为 `runtime_contract + invalid_provider_offer`。

## 范围

- 本次纳入：
  - `syvert/provider_capability_offer.py`
  - `tests/runtime/provider_capability_offer_fixtures.py`
  - `tests/runtime/test_provider_capability_offer.py`
  - `docs/exec-plans/CHORE-0320-fr-0025-offer-manifest-validator.md`
- 本次不纳入：
  - `docs/specs/FR-0025-provider-capability-offer-contract/**`
  - Core registry、TaskRecord、resource lifecycle、runtime routing
  - `AdapterCapabilityRequirement x ProviderCapabilityOffer` compatibility decision
  - provider selector、priority、fallback、marketplace、真实 provider 产品支持
  - SDK docs / evidence 与父 FR `#297` closeout

## 当前停点

- worktree：`/Users/mc/code/worktrees/syvert/issue-320-fr-0025-provider-offer-manifest-validator`
- 分支：`issue-320-fr-0025-provider-offer-manifest-validator`
- 原始 worktree 创建基线：`e456547dd4bc8145e7a1c77be1e89164a7d33fc8`
- 已核对 `AGENTS.md`、`WORKFLOW.md`、`#320` GitHub truth 与 `FR-0025` formal spec。
- 当前 checkpoint：已新增 Provider capability offer validator、fixtures 与 runtime tests；已 rebase 到最新主干 `3ce34ee3a5e54945b6bb9a3128d4fc61ae346e4e`。首轮 guardian 指出 `provider_port_ref` 未强制归属当前 `adapter_binding.adapter_key`，已收紧为必须使用当前 `adapter_key:` 前缀并拒绝 core/global/marketplace/registry/routing 端口语义，focused 回归已通过。

## 下一步动作

- 推送分支并通过 `scripts/open_pr.py --class implementation` 创建 PR。
- 运行 guardian review；若 guardian 或 checks 返回阻断，按同类阻断收敛后重跑门禁。
- guardian 与 checks 通过后使用 `scripts/merge_pr.py` 受控合并，并执行 issue closeout / branch retirement / worktree retirement。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 把 `FR-0025` Provider capability offer 从 formal carrier 推进为可执行 validator / fixture truth，供 SDK docs / evidence、后续 compatibility decision 与父 FR closeout 消费。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0025` 的 manifest fixture validator implementation Work Item。
- 阻塞：
  - `#321` SDK docs / evidence 需要本 validator 作为可执行 offer truth。
  - `#322` 父 FR closeout 需要本 validator 与 SDK evidence 主干事实。
  - 后续 `FR-0026` compatibility decision 需要稳定 Provider offer input，但不得由本事项提前实现 decision。

## 已验证项

- `python3 scripts/create_worktree.py --issue 320 --class implementation`
  - 结果：通过；创建 worktree `/Users/mc/code/worktrees/syvert/issue-320-fr-0025-provider-offer-manifest-validator`，分支 `issue-320-fr-0025-provider-offer-manifest-validator`，基线 `e456547dd4bc8145e7a1c77be1e89164a7d33fc8`。
- `gh api user --jq .login`
  - 结果：通过；确认本机 `gh` keyring 可用，未全局导出 `GH_TOKEN` / `GITHUB_TOKEN`。
- `gh api repos/:owner/:repo/issues/320 --jq '{number,title,state,body,labels:[.labels[].name],assignees:[.assignees[].login]}'`
  - 结果：通过；确认 `#320` open，item_key=`CHORE-0320-fr-0025-offer-manifest-validator`，item_type=`CHORE`，release=`v0.8.0`，sprint=`2026-S21`，integration fields 为 `none/no/local_only`。
- 已核对 `FR-0025` formal spec、data model 与 contracts，确认 required fields、forbidden fields、proof adapter coverage、declared-only 与 `invalid_provider_offer` fail-closed 语义。
- 已核对 `FR-0024` validator 风格，复用 dataclass、raw mapping normalization、string array fail-closed、forbidden field scan 与 declared-only 输出模式。
- 已核对 `FR-0027` approved shared profile proof truth，Provider offer validator 只消费 `approved_shared_resource_requirement_profile_evidence_entries()`，不复制 registry / matcher execution path。
- `python3 -m unittest tests.runtime.test_provider_capability_offer`
  - 结果：通过，18 tests。
- `python3 -m unittest tests.runtime.test_adapter_capability_requirement tests.runtime.test_adapter_resource_requirement_declaration tests.runtime.test_resource_capability_matcher tests.runtime.test_registry`
  - 结果：通过，65 tests。
- `python3 -m py_compile syvert/provider_capability_offer.py tests/runtime/provider_capability_offer_fixtures.py tests/runtime/test_provider_capability_offer.py`
  - 结果：通过。
- `python3 -m unittest discover tests/runtime`
  - 结果：通过，887 tests。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- 补充 error carrier / version / lifecycle / duplicate profile 边界回归后 `python3 -m unittest tests.runtime.test_provider_capability_offer`
  - 结果：通过，20 tests。
- 补充边界回归后 `python3 -m unittest tests.runtime.test_adapter_capability_requirement tests.runtime.test_adapter_resource_requirement_declaration tests.runtime.test_resource_capability_matcher tests.runtime.test_registry`
  - 结果：通过，65 tests。
- rebase 到 `origin/main=3ce34ee3a5e54945b6bb9a3128d4fc61ae346e4e` 后，提交 `54b72473f77d8254365954b15c32321ced2d8715` 上 `python3 -m unittest discover tests/runtime`
  - 结果：通过，893 tests。
- rebase 后提交 `54b72473f77d8254365954b15c32321ced2d8715` 上 `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- rebase 后提交 `54b72473f77d8254365954b15c32321ced2d8715` 上 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- rebase 后提交 `54b72473f77d8254365954b15c32321ced2d8715` 上 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- rebase 后提交 `54b72473f77d8254365954b15c32321ced2d8715` 上 `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-320-fr-0025-provider-offer-manifest-validator`
  - 结果：通过。
- rebase 后提交 `54b72473f77d8254365954b15c32321ced2d8715` 上 `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`implementation`，变更类别=`docs, implementation`。
- `python3 scripts/open_pr.py --class implementation --issue 320 ...`
  - 结果：通过，创建 PR `#335`。
- `python3 scripts/pr_guardian.py review 335 --post-review`
  - 结果：`REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：`adapter_binding.provider_port_ref` 只拒绝 `core` / 连续 `global_provider` token，未强制归属 `adapter_binding.adapter_key`，因此 `xhs` offer 可借用 `douyin:adapter-owned-provider-port` 或 global-looking port ref。
- 已处理首轮 guardian 阻断：
  - `adapter_binding.provider_port_ref` 必须以当前 `adapter_binding.adapter_key + ":"` 为前缀，cross-adapter / global ref fail-closed。
  - `provider_port_ref` 拒绝 core / global / public SDK / marketplace / registry / routing 端口语义。
  - 新增 cross-adapter、global、core、marketplace、registry port ref focused 回归。
- guardian 修复后 `python3 -m unittest tests.runtime.test_provider_capability_offer`
  - 结果：通过，21 tests。
- guardian 修复后 `python3 -m py_compile syvert/provider_capability_offer.py tests/runtime/test_provider_capability_offer.py`
  - 结果：通过。

## 待验证项

- guardian 修复后的相关 runtime 回归、全量 runtime discover、required gates、PR push、guardian review、GitHub checks、受控 merge 与 closeout reconciliation。

## 未决风险

- 若 validator 后续复制 `FR-0027` matcher 或 registry 逻辑，会形成 resource profile proof second truth。
- 若合法 offer 输出被解释为 compatibility approved，会提前越过 `FR-0026` compatibility decision 边界。
- 若 provider key、adapter binding、observability 或 lifecycle 接受 Core routing、selector、fallback、marketplace 或技术链路字段，会污染 Core / Adapter / Provider 边界。

## 回滚方式

- 使用独立 revert PR 撤销本次新增 validator、fixture、测试与 exec-plan。
- 若发现 `FR-0025` carrier 本身不足，必须回到 formal spec Work Item 更新规约，不在 implementation PR 中隐式改写。

## 最近一次 checkpoint 对应的 head SHA

- 初始 implementation checkpoint：`e456547dd4bc8145e7a1c77be1e89164a7d33fc8`
- implementation checkpoint：`2fa77286f2c5bb15da07a172e914e02369b362f7`
- main-sync validation checkpoint：`54b72473f77d8254365954b15c32321ced2d8715`
