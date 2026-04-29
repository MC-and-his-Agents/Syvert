# CHORE-0272 FR-0021 parent closeout

## 关联信息

- item_key：`CHORE-0272-fr-0021-parent-closeout`
- Issue：`#272`
- item_type：`CHORE`
- release：`v0.7.0`
- sprint：`2026-S20`
- Parent Phase：`#264`
- Parent FR：`#265`
- 关联 spec：`docs/specs/FR-0021-adapter-provider-port-boundary/`
- 关联 PR：`#286`
- 状态：`active`

## 目标

- 在不引入新 runtime 或 formal spec 语义的前提下，收口 `FR-0021` 父事项。
- 将 formal spec、provider port / native provider implementation、SDK compatibility / capability metadata、双参考 evidence、GitHub issue 状态与当前主干事实对齐。
- 明确 `#264` Phase 与 `v0.7.0` tag / GitHub Release 仍留给后续独立 phase / release closeout Work Item。

## 范围

- 本次纳入：
  - 新增本 closeout exec-plan。
  - 更新 `docs/releases/v0.7.0.md` 与 `docs/sprints/2026-S20.md` 中的 `FR-0021` parent closeout 索引。
  - 合入后回写并关闭 `#272` 与 `#265`。
- 本次不纳入：
  - 不修改 `docs/specs/FR-0021-adapter-provider-port-boundary/`。
  - 不修改 `syvert/**`、`tests/**` 或 runtime 行为。
  - 不新增外部 provider、provider selector、fallback priority 或小红书/抖音业务能力。
  - 不关闭 Phase `#264`，不创建 `v0.7.0` tag，不发布 GitHub Release。

## 当前停点

- `#266` planning truth 已完成并关闭。
- `#268` formal spec closeout 已由 PR `#282` squash merge，merge commit `7a4cbaa72ccd41263ce8d94dbcb7ed8c894dd882`。
- `#269` provider port / native provider runtime implementation 已由 PR `#283` squash merge，merge commit `de2e3aaf3e83554a9241e1ae28fac14599359fbc`。
- `#270` SDK compatibility / capability metadata 已由 PR `#284` squash merge，merge commit `c707fa8d7468fb4fce398234e4448253b83a8c5a`。
- `#271` dual reference evidence 已由 PR `#285` squash merge，merge commit `4b6e0035972b6412213e8b99011130f854f74438`。
- `#266/#268/#269/#270/#271` GitHub issue 均已关闭为 `completed`。
- `#265` FR 与 `#272` closeout Work Item 当前仍为 open，等待本 closeout PR 合入后关闭。
- 当前主干基线：`4b6e0035972b6412213e8b99011130f854f74438`。

## 下一步动作

- 通过 docs / governance gate、guardian 与 merge gate。
- 合入本 closeout PR。
- 使用 GitHub REST 在 `#272` 与 `#265` 追加 closeout 评论并关闭为 `completed`。
- 确认 `#264` Phase 仍为 open，等待最终 phase / release closeout Work Item。
- fast-forward main，退役 `issue-272-fr-0021` 分支与 worktree。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.7.0 / 2026-S20` 完成 `FR-0021` parent closeout，使最终 phase / release closeout 可以直接引用 `FR-0021` spec、implementation、SDK compatibility 与 evidence 主干事实。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0021` parent closeout Work Item。
- 阻塞：最终 `#264` phase / release closeout 前必须完成 `#265` FR 状态同步。

## closeout 证据

- planning truth：
  - Issue `#266`：建立 `v0.7.0` adapter provider port 规划真相，已关闭为 `completed`。
  - 主干路径：`docs/exec-plans/CHORE-0266-v0-7-adapter-provider-port-planning.md`、`docs/decisions/ADR-CHORE-0266-v0-7-adapter-provider-port-planning.md`。
- formal spec 证据：
  - PR `#282`：新增 `docs/specs/FR-0021-adapter-provider-port-boundary/`，冻结 adapter-owned provider port、native provider、Core 不感知 provider、非外部 provider SDK 与 non-approval boundary。
  - 主干路径：`docs/specs/FR-0021-adapter-provider-port-boundary/`。
- implementation 证据：
  - PR `#283`：新增 `syvert/adapters/xhs_provider.py` 与 `syvert/adapters/douyin_provider.py`，并让 `XhsAdapter` / `DouyinAdapter` 委托 native provider，同时保持 Adapter public runtime surface、constructor transport hooks 与 registry provider field exclusion。
  - 主干路径：`syvert/adapters/xhs.py`、`syvert/adapters/xhs_provider.py`、`syvert/adapters/douyin.py`、`syvert/adapters/douyin_provider.py`、`syvert/registry.py`。
- SDK / metadata 证据：
  - PR `#284`：更新 `adapter-sdk.md`、`docs/releases/v0.7.0.md` 与 `docs/sprints/2026-S20.md`，明确 `syvert-adapter-sdk/v0.7` compatibility declaration、approved capability baseline 与第三方 adapter migration boundary。
- dual reference evidence：
  - PR `#285`：新增 `docs/exec-plans/artifacts/CHORE-0271-fr-0021-dual-reference-evidence.md`。
  - evidence 覆盖 `xhs` / `douyin`、public operation `content_detail_by_url`、adapter-facing capability `content_detail`、target `url`、mode `hybrid`、managed resources `account` + `proxy`、raw + normalized compatibility，以及 registry / Core 不暴露 provider 字段。

## 已验证项

- `gh api repos/MC-and-his-Agents/Syvert/issues/266`
  - 结果：`state=closed`，`state_reason=completed`。
- `gh api repos/MC-and-his-Agents/Syvert/issues/268`
  - 结果：`state=closed`，`state_reason=completed`。
- `gh api repos/MC-and-his-Agents/Syvert/issues/269`
  - 结果：`state=closed`，`state_reason=completed`。
- `gh api repos/MC-and-his-Agents/Syvert/issues/270`
  - 结果：`state=closed`，`state_reason=completed`。
- `gh api repos/MC-and-his-Agents/Syvert/issues/271`
  - 结果：`state=closed`，`state_reason=completed`。
- `gh api repos/MC-and-his-Agents/Syvert/issues/265`
  - 结果：`state=open`，等待本 closeout PR 合入后关闭。
- `gh api repos/MC-and-his-Agents/Syvert/issues/264`
  - 结果：`state=open`，等待后续 phase / release closeout Work Item。
- `gh api repos/MC-and-his-Agents/Syvert/pulls/282`
  - 结果：`merged=true`，`merged_at=2026-04-29T06:48:36Z`，`merge_commit_sha=7a4cbaa72ccd41263ce8d94dbcb7ed8c894dd882`。
- `gh api repos/MC-and-his-Agents/Syvert/pulls/283`
  - 结果：`merged=true`，`merged_at=2026-04-29T08:22:19Z`，`merge_commit_sha=de2e3aaf3e83554a9241e1ae28fac14599359fbc`。
- `gh api repos/MC-and-his-Agents/Syvert/pulls/284`
  - 结果：`merged=true`，`merged_at=2026-04-29T09:39:32Z`，`merge_commit_sha=c707fa8d7468fb4fce398234e4448253b83a8c5a`。
- `gh api repos/MC-and-his-Agents/Syvert/pulls/285`
  - 结果：`merged=true`，`merged_at=2026-04-29T10:19:36Z`，`merge_commit_sha=4b6e0035972b6412213e8b99011130f854f74438`。
- `python3.11 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `python3.11 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3.11 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3.11 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `python3.11 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，`PR class=docs`。
- `python3.11 scripts/open_pr.py --class docs --issue 272 --item-key CHORE-0272-fr-0021-parent-closeout --item-type CHORE --release v0.7.0 --sprint 2026-S20 --title 'docs(closeout): 收口 FR-0021 父事项' --closing fixes --integration-touchpoint none --shared-contract-changed no --integration-ref none --external-dependency none --merge-gate local_only --contract-surface none --joint-acceptance-needed no --integration-status-checked-before-pr no --integration-status-checked-before-merge no`
  - 结果：已创建 PR `#286`。
- `python3.11 scripts/pr_guardian.py review 286 --post-review --json-output /tmp/syvert-pr-286-guardian.json`
  - 结果：`REQUEST_CHANGES`。guardian 要求 release / sprint closeout 索引补齐 PR `#286`，并调整 sprint 状态，避免在 PR 合入与 `#265/#272` GitHub closeout 执行前提前声明 parent closeout 已完成。
  - 处理：已补齐 `#272` / PR `#286` 映射，并把 sprint 状态改为 parent closeout 由 `#272` / PR `#286` 执行、合入后关闭 `#265`。

## 待完成

- 合入本 closeout PR。
- 合入后关闭 `#272`，说明 closeout 文档已进入主干。
- 关闭 `#265`，引用 `#266/#268/#269/#270/#271/#272` 与 PR `#282/#283/#284/#285` 证据。
- 保持 `#264` open，等待最终 phase / release closeout Work Item。

## 未决风险

- 若 `#265` 关闭前又新增子 Work Item，必须重新核对后再关闭父 FR。
- 若本 closeout 被误用于发布 `v0.7.0`，会绕过最终 phase / release closeout 的 tag / GitHub Release 策略。
- 若 release / sprint 索引把 `FR-0021` 误写成批准外部 provider 或新增业务能力，会扩大 `v0.7.0` 范围。

## 回滚方式

- 仓内回滚：使用独立 revert PR 撤销本 closeout exec-plan 与 release / sprint closeout 索引。
- GitHub 侧回滚：若关闭后发现事实错误，使用 REST PATCH 重新打开 `#265` 或 `#272`，追加纠正评论，并通过新的 closeout Work Item 修正仓内事实。

## 最近一次 checkpoint 对应的 head SHA

- 当前主干基线：`4b6e0035972b6412213e8b99011130f854f74438`。
- 本 exec-plan 是 `#272` 的首个版本化恢复工件；后续 review-sync 若只更新验证记录或 GitHub 状态，不推进新的 formal spec / runtime 语义。
