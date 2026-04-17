# CHORE-0125-fr-0008-parent-closeout 执行计划

## 关联信息

- item_key：`CHORE-0125-fr-0008-parent-closeout`
- Issue：`#140`
- item_type：`CHORE`
- release：`v0.3.0`
- sprint：`2026-S16`
- 关联 spec：`docs/specs/FR-0008-task-record-persistence/`
- 关联 PR：
- 状态：`active`
- active 收口事项：`CHORE-0125-fr-0008-parent-closeout`

## 目标

- 在不引入新运行时代码或新 formal spec 语义的前提下，通过合法 Work Item `#140` 完成父 FR `#127` 的最终 closeout。
- 把 `FR-0008` 的 formal spec、`#138/#139` 实现、release / sprint 索引与 GitHub issue 真相映射回同一条父事项证据链。

## 范围

- 本次纳入：
  - `docs/exec-plans/FR-0008-task-record-persistence.md`
  - `docs/exec-plans/CHORE-0125-fr-0008-parent-closeout.md`
  - `docs/exec-plans/CHORE-0122-fr-0008-formal-spec-closeout.md`
  - `docs/exec-plans/CHORE-0123-fr-0008-task-record-model.md`
  - `docs/exec-plans/CHORE-0124-fr-0008-local-persistence-and-serialization.md`
  - `docs/releases/v0.3.0.md`
  - `docs/sprints/2026-S16.md`
  - GitHub `#140` / `#127` / `#137` / `#138` / `#139` issue 正文、closeout 评论与 Project 状态对齐
- 本次不纳入：
  - 任何新的 runtime / adapter / test 实现
  - `FR-0008` formal spec 语义改写
  - `FR-0009` 或 `#126` 的事项状态调整

## 当前停点

- `origin/main@b6ebf00dce8cb0182b81b077fb1255270f1ee803` 已包含 `FR-0008` closeout 所需的关键前提：PR `#145`、`#147`、`#148`。
- `#137` 已由 PR `#145` 合入并关闭；`#138` 已由 PR `#147` 合入并关闭；`#139` 已由 PR `#148` 合入并关闭。
- 当前 `FR-0008` GitHub closeout 仍包含 Work Item `#140` 与父 FR `#127`；二者正文仍未回写 formal spec / implementation / closeout 的完整主干真相。
- `#140` 当前执行现场为独立 worktree：`/Users/mc/code/worktrees/syvert/issue-140-chore-fr-0008`。
- 当前实质 closeout checkpoint 为 `3840abaef51b6706a6167192c2a725bef8a1ce2a`，已首次落盘 requirement container、parent closeout exec-plan、release/sprint 对齐与 `#145/#147/#148` 主干回链。
- 当前受审 PR：`#149`

## 下一步动作

- 把 `FR-0008` requirement container、`#137/#138/#139` 历史执行记录、release / sprint 索引与 `#140` 对齐到“唯一 active closeout 入口”后的主干真相。
- 当前 head 完成 docs 类门禁与受控 PR 创建后，进入 guardian / merge gate。
- 合并后先把 `#140` 的 Project 状态从 `In Progress` 切到 `Done`，修正 `#140` 正文并关闭当前 Work Item。
- 随后修正 GitHub `#127` 正文、发布 `#127` closeout 评论、把 `#127` 的 Project 状态从 `Todo` 切到 `Done`，再关闭 `#127`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.3.0` 完成 `FR-0008` 父事项收口，使任务记录与持久化 contract 已被 formal spec、主干实现、验证证据与 GitHub 关闭语义完整消费。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0008` 父事项 closeout Work Item。
- 阻塞：
  - 必须先保证 `#137/#138/#139` 全部关闭，且 release / sprint / exec-plan 不再把这些子事项误表述为当前 active 入口。
  - 必须在关闭前修正 `#127` 正文，使其反映 formal spec、共享模型实现、本地持久化实现与当前 parent closeout 入口的主干真相。

## 已验证项

- `gh issue view 127 --json state,title,url,body,projectItems`
  - 结果：`#127` 为 `OPEN`，当前仍是 `FR-0008` 的 canonical requirement 容器，但正文仍保留 `formal spec（planned）` 等过期事实。
- `gh issue view 137 --json state,title,url,body`
  - 结果：`#137` 为 `CLOSED`；对应 PR `#145` / merge commit `093141b5dfbde9d5912963fe72497081334bc6bd`。
- `gh issue view 138 --json state,title,url,body`
  - 结果：`#138` 为 `CLOSED`；对应 PR `#147` / merge commit `b912c369d745b0579e4e6d38bcf35c08845bc006`。
- `gh issue view 139 --json state,title,url,body,projectItems`
  - 结果：`#139` 为 `CLOSED`，Project 状态为 `Done`；对应 PR `#148` / merge commit `b6ebf00dce8cb0182b81b077fb1255270f1ee803`，但正文仍停留在 `进行中（PR #148）`。
- `gh issue view 140 --json state,title,url,body,projectItems`
  - 结果：`#140` 为 `OPEN`，Project 状态为 `In Progress`。
- `gh issue view 127 --json state,title,url,body,projectItems`
  - 结果：`#127` 为 `OPEN`，Project 状态为 `Todo`；父事项 closeout 完成后需切到 `Done`。
- `gh pr view 145 --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`，`mergeCommit=093141b5dfbde9d5912963fe72497081334bc6bd`
- `gh pr view 147 --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`，`mergeCommit=b912c369d745b0579e4e6d38bcf35c08845bc006`
- `gh pr view 148 --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`，`mergeCommit=b6ebf00dce8cb0182b81b077fb1255270f1ee803`
- `python3 scripts/create_worktree.py --issue 140 --class docs`
  - 结果：已创建独立 worktree `/Users/mc/code/worktrees/syvert/issue-140-chore-fr-0008`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：在实质 closeout checkpoint `3840abaef51b6706a6167192c2a725bef8a1ce2a` 上通过
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：在实质 closeout checkpoint `3840abaef51b6706a6167192c2a725bef8a1ce2a` 上通过
- `python3 scripts/governance_gate.py --mode ci --base-sha $(git merge-base origin/main HEAD) --head-sha $(git rev-parse HEAD) --head-ref issue-140-chore-fr-0008`
  - 结果：在实质 closeout checkpoint `3840abaef51b6706a6167192c2a725bef8a1ce2a` 上通过
- `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：在实质 closeout checkpoint `3840abaef51b6706a6167192c2a725bef8a1ce2a` 上通过，`PR class=docs`
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
  - 结果：在实质 closeout checkpoint `3840abaef51b6706a6167192c2a725bef8a1ce2a` 上通过
- `python3 scripts/open_pr.py --class docs --issue 140 --item-key CHORE-0125-fr-0008-parent-closeout --item-type CHORE --release v0.3.0 --sprint 2026-S16 --title 'docs(closeout): 收口 FR-0008 父事项' --closing fixes --dry-run`
  - 结果：通过；当前受审 PR 为 `#149 https://github.com/MC-and-his-Agents/Syvert/pull/149`

## closeout 证据

- formal spec 证据：PR `#145` 已把 `FR-0008` formal spec 合入主干，对应 `docs/specs/FR-0008-task-record-persistence/`
- implementation 证据：
  - PR `#147` / `#138`：落地 `TaskRecord` / `TaskRequestSnapshot` / `TaskTerminalResult` / `TaskLogEntry` 共享模型、JSON-safe 序列化与 runtime 生命周期接线
  - PR `#148` / `#139`：落地 `LocalTaskRecordStore`、accepted/running/completion 三段 durable 写入、fail-closed invalidation 与 accepted/running/terminal 幂等回放
- release / sprint 证据：`docs/releases/v0.3.0.md` 与 `docs/sprints/2026-S16.md` 在本回合回链 `#127/#137/#138/#139/#140` 与 PR `#145/#147/#148`
- GitHub closeout 证据：当前剩余 GitHub closeout issue 为 active Work Item `#140` 与父 FR `#127`；本回合合入后应先把 `#140` 从 `In Progress` 切到 `Done` 并关闭，再把 `#127` 从 `Todo` 切到 `Done` 并关闭

## GitHub closeout 工件

- `#140` 正文修正目标：
  - 执行状态改为 `已完成（PR #... 已 MERGED）`
  - 回填 merge commit；当前受审 docs head 与 docs 门禁记录已在本轮 closeout exec-plan 中落盘
  - 明确本事项只负责 docs / GitHub closeout 收口，不引入新 runtime 或 formal spec 语义
- `#140` Project 状态目标：
  - PR `#149` 审查与合并期间保持 `In Progress`
  - 合并并回写正文后切到 `Done`
- `#127` 正文修正目标：
  - 明确 formal spec 已由 PR `#145` 合入主干
  - 明确共享模型实现已由 `#138` / PR `#147` 落地
  - 明确本地持久化与共享序列化管线已由 `#139` / PR `#148` 落地
  - 将父事项 closeout 入口补为 `#140`
  - 子 Work Item 保持：`#137`、`#138`、`#139`、`#140`
- `#127` Project 状态目标：
  - 在 `#140` 合入前保持 `Todo`
  - `#140` 合入且 `#127` 正文 / closeout comment 对齐后切到 `Done`
- `#127` closeout 评论草案：
  - `FR-0008` formal spec 已由 PR `#145` 合入主干，spec 真相位于 `docs/specs/FR-0008-task-record-persistence/`
  - `#138` / PR `#147` 已完成任务状态/结果/日志共享模型
  - `#139` / PR `#148` 已完成本地持久化与共享序列化管线
  - 当前父事项 closeout 已由 `#140` 承接，`docs/releases/v0.3.0.md`、`docs/sprints/2026-S16.md` 与 active exec-plan 已与 GitHub 真相一致
- Project 状态验证入口：
  - `gh issue view 140 --json projectItems`：验证 `#140` 已从 `In Progress` 切到 `Done`
  - `gh issue view 127 --json projectItems`：验证 `#127` 已从 `Todo` 切到 `Done`

## 未决风险

- 若 `#127` 关闭前仍把 `#137/#138/#139` 或 release / sprint 索引标记为 active，会留下双 active 执行语义。
- 若 `#127` 关闭前不修正 GitHub 正文与 closeout 评论，后续回溯 `FR-0008` 的 formal spec / implementation / closeout 证据仍需手工拼接。

## 回滚方式

- 仓内回滚：如需回滚，使用独立 revert PR 撤销本事项对 `docs/exec-plans/FR-0008-task-record-persistence.md`、`docs/exec-plans/CHORE-0125-fr-0008-parent-closeout.md`、`docs/releases/v0.3.0.md` 与 `docs/sprints/2026-S16.md` 的增量修改。
- GitHub 侧回滚：
  - 若已编辑 `#127` / `#140` 正文但 PR 未合入，恢复它们到 closeout 前正文，并保留 `#127/#140` 为 `OPEN`
  - 若已发布 closeout 评论但发现仓内工件仍不一致，在对应 issue 追加纠正评论并停止关闭动作
  - 若 `#127` 或 `#140` 已关闭后发现 closeout 事实错误，先重新打开对应 issue，再通过独立 revert PR 与新的 closeout 回合修复仓内 / GitHub 状态

## 最近一次 checkpoint 对应的 head SHA

- 前置完成基线：`b6ebf00dce8cb0182b81b077fb1255270f1ee803`
- 实质 closeout checkpoint：`3840abaef51b6706a6167192c2a725bef8a1ce2a`
- 说明：`b6ebf00...` 是 formal spec / `#138` / `#139` 已完成后的主干基线；`3840aba...` 首次落盘本轮 requirement container、parent closeout exec-plan、release/sprint 对齐与 closeout 证据。其后的 metadata-only review sync 只回写受审 head / docs 验证 / GitHub 追账，不改写 `FR-0008` closeout 语义。
