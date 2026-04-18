# CHORE-0129-fr-0009-parent-closeout 执行计划

## 关联信息

- item_key：`CHORE-0129-fr-0009-parent-closeout`
- Issue：`#144`
- item_type：`CHORE`
- release：`v0.3.0`
- sprint：`2026-S16`
- 关联 spec：`docs/specs/FR-0009-cli-task-query-and-core-path/`
- 状态：`active`
- active 收口事项：`CHORE-0129-fr-0009-parent-closeout`

## 目标

- 在不引入新运行时代码或新 formal spec 语义的前提下，通过合法 Work Item `#144` 完成父 FR `#128` 的最终 closeout。
- 把 `FR-0009` 的 formal spec、`#142/#143` 实现、release / sprint 索引与 GitHub issue 真相收口到同一条父事项证据链。

## 范围

- 本次纳入：
  - `docs/exec-plans/FR-0009-cli-task-query-and-core-path.md`
  - `docs/exec-plans/CHORE-0129-fr-0009-parent-closeout.md`
  - `docs/exec-plans/CHORE-0126-fr-0009-formal-spec-closeout.md`
  - `docs/exec-plans/CHORE-0127-fr-0009-cli-task-query.md`
  - `docs/exec-plans/CHORE-0128-fr-0009-cli-core-path-persistence-closeout.md`
  - `docs/releases/v0.3.0.md`
  - `docs/sprints/2026-S16.md`
  - GitHub `#141` / `#143` / `#144` / `#128` issue 正文、`#128` closeout 评论与 Issue 状态对齐
- 本次不纳入：
  - 任何新的 runtime / adapter / test 实现
  - `FR-0009` formal spec 语义改写
  - `FR-0010` 或 `#126` 之外事项的状态调整

## 当前停点

- `origin/main@2f4aea6322d93feefa66b63227a3c9ff5299b44c` 已包含 `FR-0009` closeout 所需的关键前提：PR `#154`、`#156`、`#157`。
- `#141` 已由 PR `#154` 合入并关闭；`#142` 已由 PR `#156` 合入并关闭；`#143` 已由 PR `#157` 合入并关闭。
- `FR-0009` requirement container、release / sprint 索引仍未回写 `#142/#143` 已合入与 `#144` 成为唯一 active closeout 入口的主干真相。
- GitHub 侧仍有 closeout 追账：`#141` 正文停留在 `待开始`，`#143` 正文停留在 `进行中（PR #157 审查中）`，`#144` 仍为 `待开始`，父 FR `#128` 仍保留初始骨架正文。
- `#144` 当前执行现场为独立 worktree：`/Users/mc/code/worktrees/syvert/issue-144-chore-fr-0009`。

## 下一步动作

- 落盘 `FR-0009` requirement container、`#141/#142/#143` 历史执行记录、release / sprint 索引与 `#144` 的 parent closeout 真相。
- 在当前 head 上完成 docs 类门禁与受控 PR 创建，进入 guardian / merge gate。
- 合并后先修正 `#144` 正文为 `已完成（PR #... 已 MERGED）` 并关闭当前 Work Item。
- 随后修正 GitHub `#141/#143` 正文到已完成真相，更新 `#128` 正文、发布 `#128` closeout 评论，并关闭 `#128`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.3.0` 完成 `FR-0009` 父事项收口，使 CLI 查询与同路径执行闭环已被 formal spec、主干实现、验证证据与 GitHub 关闭语义完整消费。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0009` 父事项 closeout Work Item。
- 阻塞：
  - 必须先保证 `#141/#142/#143` 全部关闭，且 release / sprint / exec-plan 不再把这些子事项误表述为当前 active 入口。
  - 必须在关闭前修正 GitHub `#128` 正文，使其反映 formal spec、CLI query、same-path 证据与当前 parent closeout 入口的主干真相。

## 已验证项

- `gh issue view 128 --json state,title,url,body`
  - 结果：`#128` 为 `OPEN`，当前仍是 `FR-0009` 的 canonical requirement 容器，但正文仍保留初始骨架，未回写 `#141/#142/#143` 已完成事实。
- `gh issue view 141 --json state,title,url,body`
  - 结果：`#141` 为 `CLOSED`；对应 PR `#154` / merge commit `ef4f021d5ffb5f34f6bc2bd2bee7c18af50545a1`，但正文仍停留在 `待开始`。
- `gh issue view 142 --json state,title,url,body`
  - 结果：`#142` 为 `CLOSED`；对应 PR `#156` / merge commit `9aa4dc97d838b0bdbbbad9469e2202037d35af11`，正文已对齐 `已完成（PR #156 已 MERGED）`。
- `gh issue view 143 --json state,title,url,body`
  - 结果：`#143` 为 `CLOSED`；对应 PR `#157` / merge commit `2f4aea6322d93feefa66b63227a3c9ff5299b44c`，但正文仍停留在 `进行中（PR #157 审查中）`。
- `gh issue view 144 --json state,title,url,body`
  - 结果：`#144` 为 `OPEN`，正文当前为 `待开始`。
- `gh pr view 154 --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`，`mergeCommit=ef4f021d5ffb5f34f6bc2bd2bee7c18af50545a1`
- `gh pr view 156 --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`，`mergeCommit=9aa4dc97d838b0bdbbbad9469e2202037d35af11`
- `gh pr view 157 --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`，`mergeCommit=2f4aea6322d93feefa66b63227a3c9ff5299b44c`
- `python3 scripts/create_worktree.py --issue 144 --class docs`
  - 结果：已创建独立 worktree `/Users/mc/code/worktrees/syvert/issue-144-chore-fr-0009`
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：在实质 closeout checkpoint `8591231e48dc2a3e025630d4c20f5d3e27e3c162` 上通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：在实质 closeout checkpoint `8591231e48dc2a3e025630d4c20f5d3e27e3c162` 上通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：在实质 closeout checkpoint `8591231e48dc2a3e025630d4c20f5d3e27e3c162` 上通过
- `python3 scripts/governance_gate.py --mode ci --base-sha $(git merge-base origin/main HEAD) --head-sha $(git rev-parse HEAD) --head-ref issue-144-chore-fr-0009`
  - 结果：在实质 closeout checkpoint `8591231e48dc2a3e025630d4c20f5d3e27e3c162` 上通过

## closeout 证据

- formal spec 证据：PR `#154` 已把 `FR-0009` formal spec 合入主干，对应 `docs/specs/FR-0009-cli-task-query-and-core-path/`
- implementation 证据：
  - PR `#156` / `#142`：落地 `run/query` CLI surface、legacy 平铺执行入口兼容、query 错误 contract、verification matrix carrier
  - PR `#157` / `#143`：落地 same-path 判别式证据，锁定 `run/legacy-run -> durable record -> query` 与 shared store / serializer truth
- release / sprint 证据：`docs/releases/v0.3.0.md` 与 `docs/sprints/2026-S16.md` 在本回合回链 `#128/#141/#142/#143/#144` 与 PR `#154/#156/#157`
- GitHub closeout 证据：当前剩余 GitHub closeout issue 为 active Work Item `#144` 与父 FR `#128`；本回合合入后应先把 `#144` 正文回写为已完成并关闭，再修正 `#141/#143` 正文、发布 `#128` closeout 评论并关闭 `#128`

## GitHub closeout 工件

- `#144` 正文修正目标：
  - 执行状态改为 `已完成（PR #... 已 MERGED）`
  - 回填 merge commit
  - 明确本事项只负责 docs / GitHub closeout 收口，不引入新 runtime 或 formal spec 语义
- `#141` 正文修正目标：
  - 执行状态改为 `已完成（PR #154 已 MERGED）`
  - 回填 merge commit `ef4f021d5ffb5f34f6bc2bd2bee7c18af50545a1`
- `#143` 正文修正目标：
  - 执行状态改为 `已完成（PR #157 已 MERGED）`
  - 回填 merge commit `2f4aea6322d93feefa66b63227a3c9ff5299b44c`
- `#128` 正文修正目标：
  - 明确 formal spec 已由 PR `#154` 合入主干
  - 明确 CLI query surface 已由 `#142` / PR `#156` 落地
  - 明确 same-path 证据已由 `#143` / PR `#157` 落地
  - 将父事项 closeout 入口补为 `#144`
  - 子 Work Item 保持：`#141`、`#142`、`#143`、`#144`
- `#128` closeout 评论草案：
  - `FR-0009` formal spec 已由 PR `#154` 合入主干，spec 真相位于 `docs/specs/FR-0009-cli-task-query-and-core-path/`
  - `#142` / PR `#156` 已完成 CLI 查询任务状态与结果的 public surface 和错误 contract
  - `#143` / PR `#157` 已完成 `run/legacy-run -> durable record -> query` 的同路径闭环与 shared durable truth 证据
  - 当前父事项 closeout 已由 `#144` 承接，`docs/releases/v0.3.0.md`、`docs/sprints/2026-S16.md` 与 active exec-plan 已与 GitHub 真相一致

## 未决风险

- 若 `#128` 关闭前仍把 `#141/#142/#143` 或 release / sprint 索引表述为 active，会留下双 active 执行语义。
- 若 `#128` 关闭前不修正 GitHub 正文与 closeout 评论，后续回溯 `FR-0009` 的 formal spec / implementation / closeout 证据仍需手工拼接。

## 回滚方式

- 仓内回滚：如需回滚，使用独立 revert PR 撤销本事项对 `docs/exec-plans/FR-0009-cli-task-query-and-core-path.md`、`docs/exec-plans/CHORE-0129-fr-0009-parent-closeout.md`、`docs/releases/v0.3.0.md` 与 `docs/sprints/2026-S16.md` 的增量修改。
- GitHub 侧回滚：
  - 若已编辑 `#128` / `#141` / `#143` / `#144` 正文但 PR 未合入，恢复它们到 closeout 前正文，并保留 `#128/#144` 为 `OPEN`
  - 若已发布 closeout 评论但发现仓内工件仍不一致，在对应 issue 追加纠正评论并停止关闭动作
  - 若 `#128` 或 `#144` 已关闭后发现 closeout 事实错误，先重新打开对应 issue，再通过独立 revert PR 与新的 closeout 回合修复仓内 / GitHub 状态

## 最近一次 checkpoint 对应的 head SHA

- 前置完成基线：`2f4aea6322d93feefa66b63227a3c9ff5299b44c`
- 实质 closeout checkpoint：`8591231e48dc2a3e025630d4c20f5d3e27e3c162`
- 说明：当前 `#144` closeout 由包含 `#157` 的主干基线启动；`8591231...` 首次把 requirement container、parent closeout exec-plan 与 release / sprint 索引收口到 `#141/#142/#143` 已合入后的主干真相。
