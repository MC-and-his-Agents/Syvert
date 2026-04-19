# GOV-0033-v0.3.0-phase-and-release-closeout 执行计划

## 关联信息

- item_key：`GOV-0033-v0-3-0-phase-and-release-closeout`
- Issue：`#159`
- item_type：`GOV`
- release：`v0.3.0`
- sprint：`2026-S16`
- 关联 spec：无（发布/治理收口事项）
- 关联 decision：`docs/decisions/ADR-GOV-0033-v0-3-0-phase-and-release-closeout.md`
- 关联 PR：
- 状态：`active`
- active 收口事项：`GOV-0033-v0-3-0-phase-and-release-closeout`

## 目标

- 在不引入新 runtime、formal spec 或测试语义的前提下，通过合法 Work Item `#159` 完成 `v0.3.0` 的 phase / release 发布收口。
- 把 `#126` Phase、`docs/releases/v0.3.0.md`、`docs/sprints/2026-S16.md`、Git tag、GitHub Release 与 GitHub issue / project 真相收口到同一条版本 closeout 证据链。

## 范围

- 本次纳入：
  - `docs/exec-plans/GOV-0033-v0-3-0-phase-and-release-closeout.md`
  - `docs/releases/v0.3.0.md`
  - `docs/sprints/2026-S16.md`
  - GitHub `#126` / `#159` issue 正文、Project 状态与关闭语义对齐
  - Git tag `v0.3.0`
  - GitHub Release `v0.3.0`
- 本次不纳入：
  - 任何新的 runtime / adapter / test 实现
  - `FR-0008` / `FR-0009` formal spec 语义改写
  - `v0.4.0` 范围、资源系统或跨版本治理重构

## 当前停点

- `origin/main@eebeb9818e296736cadb43904ffa9072c27163ae` 已包含 `v0.3.0` 所需的全部功能与 closeout 前提：PR `#145/#147/#148/#149/#154/#156/#157/#158`。
- `#127/#128` 与其下属 Work Item 均已关闭，`v0.3.0` 的功能/contract 目标已经完成。
- 本事项按同一 Work Item 的两阶段模型推进：阶段 A 负责仓内 carrier 收口，阶段 B 负责 merge 后的发布锚点与 GitHub closeout。
- 当前分支 head 将 `docs/releases/v0.3.0.md` 与 `docs/sprints/2026-S16.md` 收口为完成态索引，去除了 `#144` 的旧 active closeout 入口。
- GitHub 侧仍残留 Phase `#126` 未关闭，正文仍写 `冲刺：待 project 排期`，Project 状态仍为 `Todo`。
- 仓外发布载体仍未建立：当前仓库没有 `v0.3.0` tag，也没有 GitHub Release `v0.3.0`。
- `#159` 当前执行现场为独立 worktree：`/Users/mc/code/worktrees/syvert/issue-159-chore-v0-3-0-phase`。
- 当前阶段 A 的仓内 closeout 工件已在当前分支落盘：`ADR-GOV-0033`、`GOV-0033` exec-plan 与 `v0.3.0` / `2026-S16` 完成态索引已同步补齐。

## 下一步动作

- 确认 `GOV-0033` exec-plan 与 release / sprint 索引已经收口为完成态，并以受控 docs PR 合入主干。
- 在当前 head 上完成受控 PR 创建、guardian 与 merge gate，合入主干。
- 合并后进入阶段 B：同步 `main`，创建 tag `v0.3.0`，发布 GitHub Release `v0.3.0`。
- 阶段 B 完成后回写并关闭 `#126` 与 `#159`，确认 Project 状态、tag / release 与仓内真相一致。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.3.0` 完成“从功能收口到正式发布”的最后一段链路，使阶段、索引、tag 与 GitHub Release 进入一致完成态。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`v0.3.0` 的 phase / release 发布 closeout Work Item。
- 阻塞：
  - `#126` 不能直接作为执行入口，必须由 `#159` 承接 docs / release 发布动作。
  - Git tag 与 GitHub Release 只能在 closeout PR 合入主干后创建，避免 tag 指向未合入 head。

## 已验证项

- `gh issue view 126 --json state,title,url,body,projectItems`
  - 结果：`#126` 为 `OPEN`，Project 状态为 `Todo`，正文仍停留在阶段进行前口径。
- `gh issue view 159 --json state,title,url,body`
  - 结果：`#159` 为 `OPEN`，已建立为承接 `v0.3.0` phase / release closeout 的合法治理 Work Item。
- `python3 scripts/create_worktree.py --issue 159 --class docs`
  - 结果：已创建独立 worktree `/Users/mc/code/worktrees/syvert/issue-159-chore-v0-3-0-phase`
- `gh issue view 127 --json state`
  - 结果：`#127` 为 `CLOSED`。
- `gh issue view 128 --json state`
  - 结果：`#128` 为 `CLOSED`。
- `gh release list`
  - 结果：当前仅有 `v0.1.0`、`v0.2.0`，尚无 `v0.3.0`。
- `git tag --list`
  - 结果：当前仅有 `v0.1.0`、`v0.2.0`，尚无 `v0.3.0`。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/governance_gate.py --mode ci --base-sha $(git merge-base origin/main HEAD) --head-sha $(git rev-parse HEAD) --head-ref issue-159-chore-v0-3-0-phase`
  - 结果：通过

## closeout 证据

- 功能完成证据：
  - `FR-0008` formal spec / implementation / parent closeout 已由 PR `#145/#147/#148/#149` 合入主干
  - `FR-0009` formal spec / implementation / parent closeout 已由 PR `#154/#156/#157/#158` 合入主干
- release / sprint 证据：
  - `docs/releases/v0.3.0.md` 与 `docs/sprints/2026-S16.md` 已在当前 head 收口为完成态索引，不再保留 active closeout 入口
- 阶段 A 仓内工件证据：
  - `docs/decisions/ADR-GOV-0033-v0-3-0-phase-and-release-closeout.md`
  - `docs/exec-plans/GOV-0033-v0-3-0-phase-and-release-closeout.md`

## 阶段 B 待执行发布动作

- 创建 tag：`v0.3.0`
- 创建 GitHub Release：`v0.3.0`
- 回写并关闭 `#126`
- 回写并关闭 `#159`
- 对齐相关 Project 状态

## GitHub closeout 工件

- `#159` 正文修正目标：
  - 执行状态改为 `已完成（PR #... 已 MERGED）`
  - 回填 merge commit
  - 明确本事项负责 phase / release closeout、tag 与 GitHub Release 发布
- `#159` Project 状态目标：
  - 执行期间如进入 Project，则保持 `In Progress`
  - 完成后切到 `Done`
- `#126` 正文修正目标：
  - 明确 `#127/#128` 及其子 Work Item 已全部完成
  - 明确 `v0.3.0` release / sprint / exec-plan / tag / GitHub Release 真相一致
  - 冲刺字段不再保留 `待 project 排期`
- `#126` Project 状态目标：
  - 在 closeout 完成前保持当前状态
  - `#159` 合入、tag / release 发布完成后切到 `Done`

## 未决风险

- 若 tag / GitHub Release 早于 closeout PR 合入，会造成发布锚点指向非主干事实。
- 若 release / sprint 索引仍保留 active closeout 入口，会把已完成版本错误表述为仍在收口。
- 若只创建 tag 而不更新 `#126` Phase，GitHub 上位阶段真相仍会滞后于已发布状态。

## 回滚方式

- 仓内回滚：如需回滚，使用独立 revert PR 撤销本事项对 `docs/exec-plans/GOV-0033-v0-3-0-phase-and-release-closeout.md`、`docs/releases/v0.3.0.md` 与 `docs/sprints/2026-S16.md` 的增量修改。
- 仓外回滚：
  - 若 closeout PR 未合入，恢复 `#126/#159` 正文并停止发布动作
  - 若 tag / GitHub Release 已创建但发现主干事实有误，先修正主干与 GitHub 事实，再按独立回合决定是否删除 / 重建发布锚点

## 最近一次 checkpoint 对应的 head SHA

- `201ddef800eff91d57dff4c338237434da2b2045`
- 说明：该 checkpoint 首次把 `ADR-GOV-0033`、两阶段 Work Item 决策、`v0.3.0` / `2026-S16` 完成态索引与阶段 A/阶段 B 分界收口到同一条仓内真相。当前 PR head 上的后续变更只用于 review / merge gate / GitHub carrier 同步，属于 `metadata-only closeout follow-up`。
