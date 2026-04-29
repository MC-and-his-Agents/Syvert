# GOV-0287 v0.7.0 phase and release closeout 执行计划

## 关联信息

- item_key：`GOV-0287-v0-7-0-phase-and-release-closeout`
- Issue：`#287`
- item_type：`GOV`
- release：`v0.7.0`
- sprint：`2026-S20`
- Parent Phase：`#264`
- 关联 spec：无（发布/治理收口事项）
- 关联 decision：`docs/decisions/ADR-GOV-0287-v0-7-0-phase-and-release-closeout.md`
- 阶段 A PR：`#288`
- 状态：`active`

## 目标

- 在不引入新 runtime、formal spec 或测试语义的前提下，通过合法 Work Item `#287` 完成 `v0.7.0` 的 phase / release 发布收口。
- 把 `docs/releases/v0.7.0.md`、`docs/sprints/2026-S20.md`、Git tag、GitHub Release、Phase `#264` 与 Work Item `#287` 状态收口到同一条版本 closeout 证据链。

## 范围

- 本次纳入：
  - `docs/exec-plans/GOV-0287-v0-7-0-phase-and-release-closeout.md`
  - `docs/decisions/ADR-GOV-0287-v0-7-0-phase-and-release-closeout.md`
  - `docs/releases/v0.7.0.md`
  - `docs/sprints/2026-S20.md`
- 本次不纳入：
  - 新 runtime / adapter / test 实现
  - `FR-0021` 或 `FR-0022` formal spec / requirement 语义改写
  - 外部 provider 接入、provider selector、fallback priority 或新增小红书/抖音业务能力
  - 阶段 A PR 内建立 tag / GitHub Release
  - 阶段 A PR 内关闭 GitHub Phase `#264`

## 当前停点

- `FR-0021` parent closeout 已由 PR `#286` 合入，merge commit `3fe59abb2b78b19d7d58e2e46469a4c348cfe35d`，FR Issue `#265` 与 closeout Work Item `#272` 均已关闭。
- `FR-0022` governance support phase / FR closeout 已由 PR `#281` 合入，merge commit `4fff4c8104332cafa3a36c3421372e9b7af6f882`，Phase `#273`、FR `#274` 与 closeout Work Item `#277` 均已关闭。
- Git tag `v0.7.0` 当前不存在。
- GitHub Release `v0.7.0` 当前不存在。
- Phase `#264` 与 Work Item `#287` 当前仍为 `open`，等待阶段 B published-truth follow-up 合入后完成 GitHub closeout。
- 当前 worktree：`/Users/mc/code/worktrees/syvert/issue-287-v0-7-0-phase-release`
- 当前承载分支：`issue-287-v0-7-0-phase-release`
- 当前主干基线：`3fe59abb2b78b19d7d58e2e46469a4c348cfe35d`

## 下一步动作

- 阶段 A：创建 docs PR，建立 release / sprint / decision / exec-plan carrier。
- 阶段 A 合入后 fast-forward main，并在阶段 A merge commit 上创建并推送 `v0.7.0` annotated tag。
- 创建 GitHub Release `v0.7.0`。
- 阶段 B：通过 metadata-only/docs follow-up 回写 published truth。
- 阶段 B PR 合入后关闭 `#264/#287`，并退役 worktree / branch。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.7.0` 完成从 `FR-0021` parent closeout 到正式发布的最后一段链路，使 release/sprint 索引、发布锚点与 GitHub closeout 进入一致完成态。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S20` 的 phase / release closeout Work Item，承接 `FR-0021` parent closeout 与 `FR-0022` governance support closeout 后的最终发布动作。
- 位置：本事项是 `v0.7.0` 收口链路的最后一个 Work Item；阶段 A 建立仓内 carrier，阶段 A 合入后的发布动作建立 tag / GitHub Release，阶段 B 回写 published truth，并在合入后完成 GitHub closeout。
- 阻塞：
  - 阶段 A PR 合入前不得创建 `v0.7.0` tag 或 GitHub Release。
  - 阶段 B PR 合入并完成 Phase / Work Item closeout 前，不得声明 `v0.7.0` 完成。

## 已验证项

### 发布前基线验证

- `gh api repos/MC-and-his-Agents/Syvert/issues/264`
  - 结果：`state=open`。
- `gh api repos/MC-and-his-Agents/Syvert/issues/265`
  - 结果：`state=closed`，`state_reason=completed`。
- `gh api repos/MC-and-his-Agents/Syvert/issues/272`
  - 结果：`state=closed`，`state_reason=completed`。
- `gh api repos/MC-and-his-Agents/Syvert/issues/273`
  - 结果：`state=closed`，`state_reason=completed`。
- `gh api repos/MC-and-his-Agents/Syvert/issues/274`
  - 结果：`state=closed`，`state_reason=completed`。
- `gh api repos/MC-and-his-Agents/Syvert/issues/287`
  - 结果：`state=open`。
- `git tag --list 'v0.7.0'`
  - 结果：当前未找到 `v0.7.0`。
- `git ls-remote --tags origin 'v0.7.0*'`
  - 结果：当前未找到远端 `v0.7.0` tag。
- `gh release view v0.7.0 --repo MC-and-his-Agents/Syvert`
  - 结果：当前不存在 GitHub Release `v0.7.0`。
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
- `python3.11 scripts/open_pr.py --class docs --issue 287 --item-key GOV-0287-v0-7-0-phase-and-release-closeout --item-type GOV --release v0.7.0 --sprint 2026-S20 --title 'docs(release): 建立 v0.7.0 发布收口载体' --closing none --integration-touchpoint none --shared-contract-changed no --integration-ref none --external-dependency none --merge-gate local_only --contract-surface none --joint-acceptance-needed no --integration-status-checked-before-pr no --integration-status-checked-before-merge no`
  - 结果：已创建阶段 A PR `#288`。
- `python3.11 scripts/pr_guardian.py review 288 --post-review --json-output /tmp/syvert-pr-288-guardian.json`
  - 结果：`REQUEST_CHANGES`。guardian 指出 PR `#281` 的 merge commit SHA 写为不可解析的 `4fff4c85eec8dab6137c04e4eb205478b69b816a`。
  - 处理：已修正为当前仓库可解析的 `4fff4c8104332cafa3a36c3421372e9b7af6f882`。

## closeout 证据

- `FR-0021`：formal spec / runtime implementation / SDK compatibility / dual reference evidence / parent closeout 已完成，见：
  - `docs/specs/FR-0021-adapter-provider-port-boundary/`
  - `docs/exec-plans/CHORE-0268-fr-0021-formal-spec-closeout.md`
  - `docs/exec-plans/CHORE-0269-fr-0021-provider-port-native-provider-runtime.md`
  - `docs/exec-plans/CHORE-0270-fr-0021-sdk-capability-metadata.md`
  - `docs/exec-plans/CHORE-0271-fr-0021-dual-reference-evidence.md`
  - `docs/exec-plans/CHORE-0272-fr-0021-parent-closeout.md`
- `FR-0022`：governance script quota / fallback hardening formal spec、implementation 与 phase closeout 已完成，见：
  - `docs/specs/FR-0022-github-api-quota-fallback-hardening/`
  - `docs/exec-plans/CHORE-0275-fr-0022-github-api-quota-fallback-hardening.md`
  - `docs/exec-plans/CHORE-0276-fr-0022-github-api-quota-runtime.md`
  - `docs/exec-plans/CHORE-0277-fr-0022-parent-phase-closeout.md`

## 剩余 closeout 动作

- 合入阶段 A release carrier PR。
- 阶段 A PR 合入后创建并推送 `v0.7.0` annotated tag。
- 阶段 A PR 合入后创建 GitHub Release `v0.7.0`。
- 合入阶段 B published-truth follow-up PR。
- 阶段 B PR 合入后通过 closing keyword 或 REST 关闭 `#287`。
- 阶段 B PR 合入后通过 GitHub REST 关闭 Phase `#264`，并留言记录 `v0.7.0` tag / GitHub Release URL。
- 阶段 B PR 合入后 fast-forward main，并退役 active branch / worktree。

## 未决风险

- 若只建立 tag 而不回写 published truth 与 GitHub issue closeout metadata，`v0.7.0` 会出现“发布锚点已存在，但仓内/issue 真相仍停在前一跳”的分叉。
- 若 tag 指向未经过 review / guardian / merge gate 的提交，会破坏 release closeout 的可审计性。
- 若 release/sprint 索引误写外部 provider 或新增业务能力，会扩大 `FR-0021` 与 `v0.7.0` 的批准范围。

## 回滚方式

- 仓内回滚：使用独立 revert PR 撤销本事项对 release / sprint 索引、decision 与 exec-plan 的增量修改。
- 仓外回滚：若 tag / GitHub Release 已建立但主干事实有误，先修正主干与 GitHub truth，再按独立治理回合决定是否删除 / 重建发布锚点。

## 最近一次 checkpoint 对应的 head SHA

- `3fe59abb2b78b19d7d58e2e46469a4c348cfe35d`
- 说明：该 checkpoint 对应 `FR-0021` parent closeout 与 `FR-0022` governance support closeout 全部合入主干、`v0.7.0` 具备正式发布前主干基线。阶段 A carrier、tag / GitHub Release 与阶段 B metadata-only 回写属于该 checkpoint 之后的发布收口动作，不作为新的 runtime/spec checkpoint。
