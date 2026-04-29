# CHORE-0277 FR-0022 parent and phase closeout

## 关联信息

- item_key：`CHORE-0277-fr-0022-parent-phase-closeout`
- Issue：`#277`
- item_type：`CHORE`
- release：`v0.7.0`
- sprint：`2026-S20`
- Parent Phase：`#273`
- Parent FR：`#274`
- 关联 spec：`docs/specs/FR-0022-github-api-quota-fallback-hardening/`
- 状态：`active`

## 目标

- 在不引入新 runtime 或 formal spec 语义的前提下，收口 `FR-0022` 与 Phase `#273`。
- 将 formal spec、implementation、验证证据、GitHub issue 状态与当前主干事实对齐。

## 范围

- 本次纳入：
  - 新增本 closeout exec-plan。
  - 更新 `docs/releases/v0.7.0.md` 与 `docs/sprints/2026-S20.md` 中的 FR-0022 治理支撑事项证据。
  - 合入后回写并关闭 `#277`、`#274` 与 `#273`。
- 本次不纳入：
  - 不修改 `docs/specs/FR-0022-github-api-quota-fallback-hardening/`。
  - 不修改 `scripts/**`、`tests/**` 或 runtime 行为。
  - 不扩张 `v0.7.0` provider port 产品范围；FR-0022 只作为治理脚本 quota / fallback 支撑事项。

## 当前停点

- `#275` formal spec closeout 已由 PR `#278` squash merge，merge commit `c37e2ed595041dfe758965e9abefb450749af699`。
- `#276` runtime hardening 已由 PR `#280` squash merge，merge commit `dbba86122b79b5853549bc3f7819f4371207f98e`。
- `#275` 与 `#276` GitHub issue 均已关闭为 `completed`。
- `#274` FR、`#273` Phase 与 `#277` closeout Work Item 当前仍为 open，等待本 closeout PR 合入后关闭。
- 当前主干基线：`dbba86122b79b5853549bc3f7819f4371207f98e`。

## 下一步动作

- 通过 docs / governance gate、guardian 与 merge gate。
- 合入本 closeout PR。
- 使用 GitHub REST 在 `#277`、`#274`、`#273` 追加 closeout 评论并关闭为 `completed`。
- fast-forward main，退役 `issue-277-fr-0022-phase-273` 分支与 worktree。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.7.0 / 2026-S20` 完成 FR-0022 治理脚本 GitHub API quota / fallback hardening 收口，使后续治理脚本执行不再默认浪费 REST / GraphQL 额度，并保留 fail-closed merge gate。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0022` parent closeout Work Item 与 Phase `#273` closeout。
- 阻塞：`#274` FR 与 `#273` Phase 必须等待本事项合入并回写 GitHub 状态后才能关闭。

## closeout 证据

- formal spec 证据：
  - PR `#278`：新增 `docs/specs/FR-0022-github-api-quota-fallback-hardening/`，冻结 REST / GraphQL cost model、进程内缓存、非合并 fallback、merge gate hard-fail 与 review_poller 收敛边界。
  - 主干路径：`docs/specs/FR-0022-github-api-quota-fallback-hardening/`。
- implementation 证据：
  - PR `#280`：实现 integration live state process-local cache、uncached merge gate live recheck、spec mirror complete bulk index、rulesets read hard-fail、review_poller unchanged state reuse。
  - 主干路径：`scripts/integration_contract.py`、`scripts/pr_guardian.py`、`scripts/spec_issue_sync.py`、`scripts/sync_repo_settings.py`、`scripts/review_poller.py`。
- 测试证据：
  - `tests/governance/test_integration_contract.py`
  - `tests/governance/test_pr_guardian.py`
  - `tests/governance/test_spec_issue_sync.py`
  - `tests/governance/test_sync_repo_settings.py`
  - `tests/governance/test_review_poller.py`

## 已验证项

- `gh api repos/MC-and-his-Agents/Syvert/pulls/278`
  - 结果：`merged=true`，`merged_at=2026-04-29T03:56:55Z`，`merge_commit_sha=c37e2ed595041dfe758965e9abefb450749af699`。
- `gh api repos/MC-and-his-Agents/Syvert/pulls/280`
  - 结果：`merged=true`，`merged_at=2026-04-29T05:04:10Z`，`merge_commit_sha=dbba86122b79b5853549bc3f7819f4371207f98e`。
- `gh api repos/MC-and-his-Agents/Syvert/issues/275`
  - 结果：`state=closed`，`state_reason=completed`。
- `gh api repos/MC-and-his-Agents/Syvert/issues/276`
  - 结果：`state=closed`，`state_reason=completed`。
- `gh api repos/MC-and-his-Agents/Syvert/issues/274`
  - 结果：`state=open`，等待本 closeout PR 合入后关闭。
- `gh api repos/MC-and-his-Agents/Syvert/issues/273`
  - 结果：`state=open`，等待 `#274` 关闭后关闭。
- `python3.11 scripts/docs_guard.py --mode ci`
  - 结果：通过，`docs-guard 通过。`
- `python3.11 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref issue-277-fr-0022-phase-273`
  - 结果：通过，`governance-gate 通过。`

## 待完成

- 合入本 closeout PR。
- 合入后关闭 `#277`，说明 closeout 文档已进入主干。
- 关闭 `#274`，引用 `#275/#276/#277` 与 PR `#278/#280` 证据。
- 关闭 `#273`，说明唯一子 FR `#274` 已完成。

## 未决风险

- 若 closeout PR 合入前 `#274` 增加新的子 Work Item，必须重新核对后再关闭 Phase `#273`。
- 若 release / sprint 索引被误读为扩大 `v0.7.0` 产品范围，需保留 FR-0022 为治理支撑事项的说明。

## 回滚方式

- 仓内回滚：使用独立 revert PR 撤销本 closeout exec-plan 与 release / sprint evidence 更新。
- GitHub 侧回滚：若关闭后发现事实错误，使用 REST PATCH 重新打开 `#273`、`#274` 或 `#277`，追加纠正评论，并通过新的 closeout Work Item 修正仓内事实。

## 最近一次 checkpoint 对应的 head SHA

- 当前主干基线：`dbba86122b79b5853549bc3f7819f4371207f98e`。
- 本 exec-plan 是 `#277` 的首个版本化恢复工件；后续 review-sync 若只更新验证记录或 GitHub 状态，不推进新的 formal spec / runtime 语义。
