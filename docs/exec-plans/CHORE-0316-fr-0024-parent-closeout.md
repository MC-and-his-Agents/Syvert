# CHORE-0316-fr-0024-parent-closeout 执行计划

## 关联信息

- item_key：`CHORE-0316-fr-0024-parent-closeout`
- Issue：`#316`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- Parent Phase：`#293`
- Parent FR：`#296`
- 关联 spec：`docs/specs/FR-0024-adapter-capability-requirement-contract/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0316-fr-0024-parent-closeout`
- 状态：`active`

## 目标

- 汇总 `FR-0024` formal spec、manifest fixture validator、reference adapter requirement migration 与 GitHub 状态的主干事实，完成父 FR `#296` closeout。
- 明确 `FR-0024` 已成为 `#298 / FR-0026` compatibility decision 可消费的 Adapter requirement truth。
- 保持本 closeout 为 docs / metadata 收口，不修改 `FR-0024` formal spec 正文、runtime、tests、`FR-0025` 或 `FR-0026` formal spec。

## 范围

- 本次纳入：
  - `docs/exec-plans/CHORE-0316-fr-0024-parent-closeout.md`
  - `docs/releases/v0.8.0.md`
  - `docs/sprints/2026-S21.md`
  - GitHub `#296` closeout comment / status
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `docs/specs/FR-0024-adapter-capability-requirement-contract/**` 正文修改
  - `docs/specs/FR-0025-provider-capability-offer-contract/**`
  - `docs/specs/FR-0026-adapter-provider-compatibility-decision/**`
  - Provider offer、compatibility decision、selector、priority、fallback 或新共享能力词汇
  - 关闭 Phase `#293`

## 当前停点

- `#313` / PR `#317` 已合入：`FR-0024` formal spec closeout，merge commit `589ea1e73ebce464ac16d292c180e08cee302ce5`，GitHub issue `#313` 已关闭。
- `#314` / PR `#329` 已合入：`AdapterCapabilityRequirement` manifest fixture validator，merge commit `e456547dd4bc8145e7a1c77be1e89164a7d33fc8`，GitHub issue `#314` 已关闭。
- `#315` / PR `#332` 已合入：xhs / douyin reference adapter requirement baseline migration，merge commit `3ce34ee3a5e54945b6bb9a3128d4fc61ae346e4e`，GitHub issue `#315` 已关闭。
- 当前主干基线：`4e90953447e20b1fffaee0f8104f989bd043202e`，已包含 PR `#317/#329/#332` 后续主干提交。
- 父 FR `#296` 当前 open，等待本 closeout PR 合入后写入 closeout comment 并关闭。

## 下一步动作

- 运行 docs class 的 scope / governance 门禁。
- 提交并通过受控入口创建 docs PR。
- 等待 GitHub checks，运行 guardian review；guardian 不设置超时限制。
- guardian `APPROVE` 且 `safe_to_merge=true` 后，使用受控 merge 入口合入。
- 合入后使用 GitHub REST 在 `#296` 写入 closeout comment 并关闭为 `completed`；确认 `#316` 自动关闭，必要时使用 REST 补关闭。
- 退役本分支与 worktree。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 固定 Adapter-side requirement carrier 的父 FR closeout truth，使后续 `FR-0026` 只消费 `FR-0024` 的已批准 requirement input，不反向改写 requirement carrier。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0024` 的 parent closeout Work Item。
- 阻塞：
  - `#298 / FR-0026` compatibility decision 需要 `FR-0024` 作为 Adapter requirement input。
  - `FR-0025` offer truth 与 `FR-0026` decision truth 不得重新定义 Adapter requirement carrier。

## closeout 证据

- formal spec 证据：
  - PR `#317`：新增并收口 `docs/specs/FR-0024-adapter-capability-requirement-contract/`，冻结 `AdapterCapabilityRequirement` canonical carrier、固定字段、`FR-0027` resource profile / proof consumption、fail-closed 与禁止 Provider offer / compatibility decision 边界。
  - 主干路径：`docs/specs/FR-0024-adapter-capability-requirement-contract/`、`docs/exec-plans/CHORE-0313-fr-0024-formal-spec-closeout.md`。
- manifest / validator 证据：
  - PR `#329`：新增 `syvert/adapter_capability_requirement.py`、fixture 与 runtime tests，使合法 requirement、`unmatched` 前提和非法 carrier 能稳定区分；provider / priority / fallback / decision 等越界字段 fail-closed。
  - 主干路径：`syvert/adapter_capability_requirement.py`、`tests/runtime/adapter_capability_requirement_fixtures.py`、`tests/runtime/test_adapter_capability_requirement.py`、`docs/exec-plans/CHORE-0314-fr-0024-manifest-fixture-validator.md`。
- reference adapter migration 证据：
  - PR `#332`：小红书与抖音 reference adapter 已暴露 `FR-0024` `AdapterCapabilityRequirement` baseline，并复用 `FR-0027` resource declaration / proof truth。
  - 主干路径：`syvert/adapters/xhs.py`、`syvert/adapters/douyin.py`、`tests/runtime/test_reference_adapter_capability_requirement_baseline.py`、`docs/exec-plans/CHORE-0315-fr-0024-reference-adapter-requirement-migration.md`。
- GitHub 状态证据：
  - `#313/#314/#315` 均已关闭；`#296` 保持 open，等待本 closeout PR 合入后关闭。
  - `#298 / FR-0026` formal spec 已在主干声明只消费 `FR-0024`、`FR-0025` 与 `FR-0027`，不得定义 requirement / offer / resource profile carrier 本体。

## 已验证项

- `gh api user --jq .login`
  - 结果：通过；确认本机 `gh` keyring 可用，未全局导出 `GH_TOKEN` / `GITHUB_TOKEN`。
- `python3 scripts/create_worktree.py --issue 316 --class docs`
  - 结果：通过；创建 worktree `/Users/mc/code/worktrees/syvert/issue-316-fr-0024`，分支 `issue-316-fr-0024`，基线 `4e90953447e20b1fffaee0f8104f989bd043202e`。
- `gh api repos/:owner/:repo/issues/313 --jq ...`
  - 结果：通过；确认 `#313` closed，closed_at=`2026-04-30T10:15:58Z`。
- `gh api repos/:owner/:repo/issues/314 --jq ...`
  - 结果：通过；确认 `#314` closed，closed_at=`2026-04-30T13:37:20Z`。
- `gh api repos/:owner/:repo/issues/315 --jq ...`
  - 结果：通过；确认 `#315` closed，closed_at=`2026-05-02T06:04:05Z`。
- `gh api repos/:owner/:repo/issues/296 --jq ...`
  - 结果：通过；确认父 FR `#296` open，关闭条件为 formal spec、requirement docs / SDK / reference adapter upgrade 约束与父事项 closeout truth。
- `gh api repos/:owner/:repo/pulls/317 --jq ...`
  - 结果：通过；`merged=true`，`merged_at=2026-04-30T10:15:56Z`，`merge_commit_sha=589ea1e73ebce464ac16d292c180e08cee302ce5`。
- `gh api repos/:owner/:repo/pulls/329 --jq ...`
  - 结果：通过；`merged=true`，`merged_at=2026-04-30T13:37:18Z`，`merge_commit_sha=e456547dd4bc8145e7a1c77be1e89164a7d33fc8`。
- `gh api repos/:owner/:repo/pulls/332 --jq ...`
  - 结果：通过；`merged=true`，`merged_at=2026-05-02T06:04:04Z`，`merge_commit_sha=3ce34ee3a5e54945b6bb9a3128d4fc61ae346e4e`。

## 待验证项

- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-316-fr-0024`
- `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
- 受控 `open_pr`、GitHub checks、guardian review、受控 merge、GitHub closeout reconciliation。

## 未决风险

- 本 PR 合入前不得关闭 `#296`；否则 GitHub 状态会早于仓内 closeout truth。
- 若 `#298 / FR-0026` 后续反向改写 `AdapterCapabilityRequirement`，会破坏 `FR-0024` 作为 requirement truth 的父项关闭结论。
- 若 release / sprint 索引把 `FR-0024` 误写成 Provider offer 或 compatibility decision 完成，会扩大本 FR 范围。

## 回滚方式

- 仓内回滚：使用独立 revert PR 撤销本 closeout exec-plan 与 release / sprint closeout 索引。
- GitHub 侧回滚：若关闭后发现事实不一致，使用 REST PATCH 重新打开 `#296` 或 `#316`，追加纠正评论，并通过新的 closeout Work Item 修正仓内事实。

## 最近一次 checkpoint 对应的 head SHA

- 当前主干基线：`4e90953447e20b1fffaee0f8104f989bd043202e`。
- 本 exec-plan 是 `#316` 的首个版本化恢复工件；后续 review-sync 若只更新验证记录或 GitHub 状态，不推进新的 formal spec / runtime 语义。
