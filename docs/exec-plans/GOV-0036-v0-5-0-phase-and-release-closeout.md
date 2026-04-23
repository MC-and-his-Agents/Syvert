# GOV-0036-v0.5.0-phase-and-release-closeout 执行计划

## 关联信息

- item_key：`GOV-0036-v0-5-0-phase-and-release-closeout`
- Issue：`#215`
- item_type：`GOV`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 spec：无（发布/治理收口事项）
- 关联 decision：`docs/decisions/ADR-GOV-0036-v0-5-0-phase-and-release-closeout.md`
- 关联 PR：`#216`、阶段 B published-truth follow-up（当前分支待创建）
- 状态：`active`
- active 收口事项：`GOV-0036-v0-5-0-phase-and-release-closeout`

## 目标

- 在不引入新 runtime、formal spec 或测试语义的前提下，通过合法 Work Item `#215` 完成 `v0.5.0` 的 phase / release 发布收口。
- 把 `docs/releases/v0.5.0.md`、`docs/sprints/2026-S18.md`、Git tag、GitHub Release 与 GitHub issue 真相收口到同一条版本 closeout 证据链。

## 范围

- 本次纳入：
  - `docs/exec-plans/GOV-0036-v0-5-0-phase-and-release-closeout.md`
  - `docs/decisions/ADR-GOV-0036-v0-5-0-phase-and-release-closeout.md`
  - `docs/releases/v0.5.0.md`
  - `docs/sprints/2026-S18.md`
- 本次不纳入：
  - 任何新的 runtime / adapter / test 实现
  - `FR-0013` / `FR-0014` / `FR-0015` formal spec 语义改写
  - `v0.6.0` 规划或跨版本治理重构
  - 阶段 B 的 tag / GitHub Release 建立
  - GitHub `#188/#189/#190/#191/#215` 的最终 closeout 对账与关闭

## 当前停点

- `origin/main@f05556581cbba094c702c659e0ac994903fbd87d` 已包含 `v0.5.0` 所需的全部 formal spec、runtime、evidence rerun 与顶层定位治理：PR `#198/#199/#200/#207/#208/#212/#213/#214`。
- `#192/#193/#194/#195/#196/#205/#206/#211` 均已关闭，`v0.5.0` 的 formal spec、implementation 与 evidence 基线已经完成。
- 阶段 A docs carrier 已由 PR `#216` 合入主干，merge commit 为 `caef0abc3071d554e599fbae473b3348868a2bf0`。
- `v0.5.0` tag 与 GitHub Release `v0.5.0` 已建立。
- `#188/#189/#190/#191` 仍为 `OPEN`，当前仅剩 GitHub closeout 对账与关闭动作。
- `#215` 已建立为承接 `v0.5.0` phase / release closeout 的合法治理 Work Item。
- 当前执行现场为独立 worktree：`/Users/mc/code/worktrees/syvert/issue-215-v0-5-0`，当前分支为 `issue-215-v0-5-0-phase-b`。
- 当前执行现场已进入阶段 B published-truth follow-up：phase A carrier 已合入主干，`v0.5.0` tag 与 GitHub Release 已建立，当前分支只负责把仓内索引与 active exec-plan 回写到正式发布完成真相。

## 下一步动作

- 在当前分支把 release / sprint 索引与 active exec-plan 同步到正式发布完成真相。
- 通过受控 docs PR 合入阶段 B metadata-only/docs follow-up。
- 完成 `#188/#189/#190/#191/#215` 的 GitHub closeout 对账与关闭。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.5.0` 完成“从功能收口到正式发布”的最后一段链路，使 release/sprint 索引、发布锚点与 GitHub closeout 进入一致完成态。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`v0.5.0` 的 phase / release 发布 closeout Work Item。
- 阻塞：
- 阶段 B 需要把 `#216/caef0ab...` 与最终 published truth 严格区分，不能误写成仓内最终发布真相已经由阶段 A 单独完成。
- active `exec-plan` 需要把阶段 A 的历史基线与阶段 B 当前验证结果按 phase 隔离，避免 review 输入混写。

## 已验证项

### 阶段 A 基线验证

- `GH_TOKEN=\"$GH_TOKEN\" gh issue view 188 --json state`
  - 结果：`#188` 为 `OPEN`
- `GH_TOKEN=\"$GH_TOKEN\" gh issue view 189 --json state`
  - 结果：`#189` 为 `OPEN`
- `GH_TOKEN=\"$GH_TOKEN\" gh issue view 190 --json state`
  - 结果：`#190` 为 `OPEN`
- `GH_TOKEN=\"$GH_TOKEN\" gh issue view 191 --json state`
  - 结果：`#191` 为 `OPEN`
- `GH_TOKEN=\"$GH_TOKEN\" gh release view v0.5.0`
  - 结果：当前不存在 `v0.5.0` GitHub Release
- `git tag --list 'v0.5.0'`
  - 结果：当前未找到 `v0.5.0`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/governance_gate.py --mode ci --base-sha \"$(git merge-base origin/main HEAD)\" --head-sha \"$(git rev-parse HEAD)\" --head-ref issue-215-v0-5-0`
  - 结果：通过
- `GH_TOKEN=\"$GH_TOKEN\" python3 scripts/open_pr.py --class docs --issue 215 --item-key GOV-0036-v0-5-0-phase-and-release-closeout --item-type GOV --release v0.5.0 --sprint 2026-S18 --title 'docs(release): 建立 v0.5.0 发布收口 carrier' --base main --closing fixes --dry-run`
  - 结果：通过
- `GH_TOKEN=\"$GH_TOKEN\" python3 scripts/open_pr.py --class docs --issue 215 --item-key GOV-0036-v0-5-0-phase-and-release-closeout --item-type GOV --release v0.5.0 --sprint 2026-S18 --title 'docs(release): 建立 v0.5.0 发布收口 carrier' --base main --closing fixes`
  - 结果：已创建 PR `#216`
- guardian review（绑定 PR `#216` 最新受审 head）
  - 结果：`APPROVE`
- `GH_TOKEN=\"$GH_TOKEN\" gh pr view 216 --json state,mergedAt`
  - 结果：PR `#216` 已 `MERGED`，merge commit 为 `caef0abc3071d554e599fbae473b3348868a2bf0`

### 阶段 B 当前验证

- `git -C /Users/mc/dev/syvert pull --ff-only origin main`
  - 结果：本地主仓库 `main` 已 fast-forward 到 `caef0abc3071d554e599fbae473b3348868a2bf0`
- `git -C /Users/mc/dev/syvert tag -a v0.5.0 -m 'v0.5.0' caef0abc3071d554e599fbae473b3348868a2bf0`
  - 结果：已在阶段 A merge commit 上创建 annotated tag `v0.5.0`
- `git -C /Users/mc/dev/syvert push origin v0.5.0`
  - 结果：已推送 tag `v0.5.0`
- `GH_TOKEN=\"$GH_TOKEN\" gh release create v0.5.0 --repo MC-and-his-Agents/Syvert --title 'v0.5.0' --notes-file /tmp/v0.5.0-release.md`
  - 结果：已创建 GitHub Release `v0.5.0`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：当前阶段 B 变更已通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：当前阶段 B 变更已通过

## closeout 证据

- 功能完成证据：
  - `FR-0015` formal spec / follow-up / implementation 已由 PR `#198/#208/#212` 合入主干
  - `FR-0013` formal spec / runtime 已由 PR `#200/#213` 合入主干
  - `FR-0014` formal spec / runtime 已由 PR `#199/#214` 合入主干
  - `GOV-0035` 顶层定位治理已由 PR `#207` 合入主干
- 当前发布前基线：
  - `origin/main@f05556581cbba094c702c659e0ac994903fbd87d`
- 发布锚点证据：
  - `v0.5.0` tag 已创建并推送
  - GitHub Release `v0.5.0` 已创建

## 剩余 closeout 动作

- 合入阶段 B metadata-only/docs PR
- 回写并关闭 `#188/#189/#190/#191/#215`

## 未决风险

- 若阶段 A 合入后没有立即建立 tag / GitHub Release，仓内 release/sprint 索引仍会滞后于正式发布态。
- 若只建立 tag 而不回写 published truth 与 GitHub issue closeout metadata，`v0.5.0` 会再次出现“发布锚点已存在，但仓内/issue 真相仍停在前一跳”的分叉。

## 回滚方式

- 仓内回滚：如需回滚，使用独立 revert PR 撤销本事项对 release / sprint 索引、decision 与 exec-plan 的增量修改。
- 仓外回滚：
  - 若阶段 A PR 未合入，恢复 `#215` 正文并停止发布动作
  - 若 tag / GitHub Release 已建立但主干事实有误，先修正主干与 GitHub truth，再按独立治理回合决定是否删除 / 重建发布锚点

## 最近一次 checkpoint 对应的 head SHA

- `caef0abc3071d554e599fbae473b3348868a2bf0`
- 说明：该 checkpoint 对应阶段 A release carrier 已合入主干，且 `v0.5.0` tag / GitHub Release 已建立；当前阶段 B 仅回写仓内最终发布真相与 GitHub closeout metadata。
