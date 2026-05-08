# CHORE-0388 v1.2 resource governance spec 执行计划

## 关联信息

- item_key：`CHORE-0388-v1-2-resource-governance-spec`
- Issue：`#388`
- item_type：`CHORE`
- release：`v1.2.0`
- sprint：`2026-S24`
- Parent Phase：`#380`
- Parent FR：`#387`
- 关联 spec：`docs/specs/FR-0387-resource-governance-admission-and-health-contract/spec.md`
- 状态：`active`

## 目标

- 新增 `FR-0387` resource governance admission and health formal spec suite。
- 只冻结 `CredentialMaterial`、`SessionHealth`、`ResourceHealthEvidence`、resource lease / invalidation / admission 边界。
- 不交付 runtime carrier、consumer migration、fake/reference evidence 或 release closeout。

## 范围

- 本次纳入：
  - `docs/specs/FR-0387-resource-governance-admission-and-health-contract/spec.md`
  - `docs/specs/FR-0387-resource-governance-admission-and-health-contract/data-model.md`
  - `docs/specs/FR-0387-resource-governance-admission-and-health-contract/contracts/README.md`
  - `docs/specs/FR-0387-resource-governance-admission-and-health-contract/plan.md`
  - `docs/specs/FR-0387-resource-governance-admission-and-health-contract/risks.md`
  - `docs/exec-plans/CHORE-0388-v1-2-resource-governance-spec.md`
- 本次不纳入：
  - `syvert/**` runtime implementation
  - `tests/**` fake/reference/real evidence
  - AdapterRequirement / ProviderOffer / compatibility decision migration
  - SDK 文档、release index、tag 或 GitHub Release
  - 为 #380 或 #387 创建 worktree

## 当前停点

- Phase `#380`：open，active admission，只作为 Phase container。
- FR `#387`：open，canonical requirement container。
- Work Item `#388`：open，唯一进入 execution workspace 的事项。
- Workspace：`/Users/mc/code/worktrees/syvert/issue-388-chore-0388-v1-2-resource-governance-spec`
- Branch：`issue-388-chore-0388-v1-2-resource-governance-spec`
- 主仓 baseline：`30bf5c32947452791c29e183fad8377893b7965c`

## 验证计划

- `python3 scripts/spec_guard.py --mode ci --all`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-388-chore-0388-v1-2-resource-governance-spec`

## 已执行验证

- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-388-chore-0388-v1-2-resource-governance-spec`
  - 结果：通过。
- Initial GitHub checks on PR #389 at head `50dca1019eee92ff12a248770201344e73ac02a6`
  - `Validate Commit Messages`：通过。
  - `Validate Docs And Guard Scripts`：通过。
  - `Validate Governance Tooling`：通过。
  - `Validate Spec Review Boundaries`：通过。
- Guardian review on PR #389 at head `50dca1019eee92ff12a248770201344e73ac02a6`
  - 结果：`REQUEST_CHANGES`。
  - 处理：移除 `credential_session_stale` 作为直接 invalidation reason，并补齐本节验证证据入口。
- Guardian review on PR #389 at head `ce2fa92`
  - 结果：`REQUEST_CHANGES`。
  - 处理：补齐 pre-admission invalid evidence 不得绕过 active lease 的边界，并冻结 `observed_at / expires_at / freshness_policy_ref` freshness 判定规则。

## PR 计划

- PR class：`spec`
- closing：`fixes`
- integration_touchpoint：`none`
- shared_contract_changed：`no`
- integration_ref：`none`
- external_dependency：`none`
- merge_gate：`local_only`
- contract_surface：`none`
- joint_acceptance_needed：`no`

## 风险

- credential/session 私有字段泄漏到 public metadata。
- health status 被误解为 provider SLA、routing 或 marketplace 信号。
- `SessionHealth` 被实现成第二套 resource lifecycle status。
- spec 越界进入自动登录、刷新、修复或后台再验证机制。

## 回滚方式

- 使用独立 revert PR 撤销本 Work Item 新增的 spec suite 与 exec-plan。
- #380/#387 保持 active admission，由 FR 重新拆分下一步 Work Item。

## 最近一次 checkpoint 对应的 head SHA

- Initial branch checkpoint：`30bf5c32947452791c29e183fad8377893b7965c`
- Current live PR head is governed by PR `headRefOid` and guardian merge gate after PR creation.
