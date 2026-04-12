# CHORE-0095-fr-0004-parent-closeout 执行计划

## 关联信息

- item_key：`CHORE-0095-fr-0004-parent-closeout`
- Issue：`#95`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0004-input-target-and-collection-policy/`
- 关联 decision：
- 关联 PR：`#96`
- 状态：`active`
- active 收口事项：`CHORE-0095-fr-0004-parent-closeout`

## 目标

- 在不引入新实现、新 formal spec 语义或额外 Work Item 的前提下，通过合法 Work Item `#95` 完成父 FR `#64` 的最终 closeout。
- 把 `FR-0004` 的 formal spec、`#87/#89/#88` 实现、`#68` 聚合 closeout、release / sprint 索引与 GitHub issue 真相映射回同一条父事项证据链。

## 范围

- 本次纳入：
  - `docs/exec-plans/FR-0004-input-target-and-collection-policy.md`
  - `docs/exec-plans/CHORE-0095-fr-0004-parent-closeout.md`
  - `docs/exec-plans/CHORE-0068-fr-0004-implementation-closeout.md`
  - `docs/specs/FR-0004-input-target-and-collection-policy/plan.md`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
  - GitHub `#64` issue 正文修正
  - GitHub `#64` closeout 评论
  - GitHub `#85` spec 索引 issue 的收口处理
- 本次不纳入：
  - 任何新的 runtime / adapter / test 实现
  - `FR-0004` formal spec 语义改写
  - `FR-0005`、`FR-0006`、`FR-0007` 的事项状态调整

## 当前停点

- `origin/main@74f7407ac109d4ef8eeb86522ae5caf1a5804a38` 已包含 `FR-0004` closeout 所需的关键前提：PR `#82`、`#90`、`#91`、`#92`、`#93`。
- `#68` 已由 PR `#93` 合入并关闭；当前 `FR-0004` GitHub closeout 仍包含 Work Item `#95`、父 FR `#64` 与 spec 索引 issue `#85`。
- `#64` 正文仍保留过期的 `formal spec：待创建`，需要在关闭前修正为主干真相。
- `#85` 仍为 `OPEN`，但其正文显示它是 `spec_issue_sync.py` 自动维护的 `FR-0004` spec 索引 issue；若不与 `#64` 同步收口，会留下额外的 open FR-0004 GitHub 镜像。
- 当前执行现场为独立 worktree：`/Users/mc/code/worktrees/syvert/issue-95-fr-0004-closeout`。

## 下一步动作

- 已把 `FR-0004` requirement container、`#68` 历史 closeout 记录、release / sprint 索引与 spec plan 对齐到 `#95` 成为唯一 active closeout 入口后的主干真相。
- 当前 head 已完成 `docs_guard`、`spec_guard`、`governance_gate`、`pr_scope_guard`、`open_pr --dry-run` 与受控 PR 创建。
- 合并后先关闭当前 Work Item `#95`，再修正 GitHub `#64` 正文、发布 `#64` closeout 评论并关闭 `#64`；最后关闭 `#85` 以避免 `FR-0004` 留下第二个 open issue 镜像。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 完成 `FR-0004` 父事项收口，使 `InputTarget` 与 `CollectionPolicy` 的 requirement 已被 formal spec、主干实现、验证证据与 GitHub 关闭语义完整消费。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0004` 父事项 closeout Work Item。
- 阻塞：
  - 必须先保证 `#68` 已关闭，且 release / sprint / exec-plan 不再把 `#68` 误表述为当前 active closeout。
  - 必须在关闭前修正 `#64` 正文中过期的 formal spec 状态，并处理 `#85` 的 open spec 索引镜像。

## 已验证项

- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`spec_review.md`
- 已阅读：`code_review.md`
- 已阅读：`docs/specs/FR-0004-input-target-and-collection-policy/`
- `gh issue list --repo MC-and-his-Agents/Syvert --state all --search 'FR-0004 in:title'`
  - 结果：当前返回 `#64`、`#85`、`#87`、`#88`、`#89`、`#95`
- `gh issue view 64 --repo MC-and-his-Agents/Syvert --json state,body,title,url`
  - 结果：`#64` 当前为 `OPEN`，且正文仍保留过期的 `formal spec：待创建`
- `gh issue view 68 --repo MC-and-his-Agents/Syvert --json state,closedAt,url`
  - 结果：`#68` 已由 PR `#93` 自动关闭
- `gh issue view 85 --repo MC-and-his-Agents/Syvert --json state,title,body,url`
  - 结果：`#85` 为 `spec_issue_sync.py` 自动维护的 spec 索引 issue，当前仍为 `OPEN`
- `gh issue view 95 --repo MC-and-his-Agents/Syvert --json state,title,url`
  - 结果：`#95` 已建立为当前父事项 closeout Work Item
- `gh issue view 87 --repo MC-and-his-Agents/Syvert --json state,closedAt,url`
  - 结果：`#87` 为 `CLOSED`
- `gh issue view 88 --repo MC-and-his-Agents/Syvert --json state,closedAt,url`
  - 结果：`#88` 为 `CLOSED`
- `gh issue view 89 --repo MC-and-his-Agents/Syvert --json state,closedAt,url`
  - 结果：`#89` 为 `CLOSED`
- `gh pr view 82 --repo MC-and-his-Agents/Syvert --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`
- `gh pr view 90 --repo MC-and-his-Agents/Syvert --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`
- `gh pr view 91 --repo MC-and-his-Agents/Syvert --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`
- `gh pr view 92 --repo MC-and-his-Agents/Syvert --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`
- `gh pr view 93 --repo MC-and-his-Agents/Syvert --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`，`mergeCommit=74f7407ac109d4ef8eeb86522ae5caf1a5804a38`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/open_pr.py --class spec --issue 95 --item-key CHORE-0095-fr-0004-parent-closeout --item-type CHORE --release v0.2.0 --sprint 2026-S15 --title 'docs(closeout): 收口 FR-0004 父事项' --closing fixes --dry-run`
  - 结果：通过
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
  - 结果：已校验当前 PR 的提交信息，全部通过
- 已创建当前受审 PR：`#96 https://github.com/MC-and-his-Agents/Syvert/pull/96`

## closeout 证据

- formal spec 证据：PR `#82` 已把 `InputTarget` 与 `CollectionPolicy` formal spec 合入主干，对应 `docs/specs/FR-0004-input-target-and-collection-policy/`
- implementation 证据：
  - PR `#90` / `#87`：Core 显式接收 `InputTarget` / `CollectionPolicy`，完成最小结构校验
  - PR `#91` / `#89`：Core 到 adapter-facing request 的共享投影与 admission 承接
  - PR `#92` / `#88`：`FR-0002` legacy URL 路径映射到 `url + hybrid`，并补齐反例与兼容证据
- implementation 聚合证据：PR `#93` 已把 `#68` closeout 到主干，并将 formal spec、实现子事项、release / sprint / exec-plan 的引用关系收成一致
- release / sprint 证据：`docs/releases/v0.2.0.md` 与 `docs/sprints/2026-S15.md` 已回链 `#64/#68/#87/#89/#88` 与 PR `#82/#90/#91/#92/#93`
- GitHub closeout 证据：当前剩余 GitHub closeout issue 为 active Work Item `#95`、父 FR `#64` 与 spec 索引 issue `#85`；PR `#96` 合入后应先关闭 `#95`，再关闭 `#64/#85`

## GitHub closeout 工件

- `#64` 正文修正目标：
  - 将过期字段 `formal spec：待创建` 改为 `formal spec：已由 PR #82 完成并合入主干`
  - 在关闭条件下补明：implementation 已由 `#87/#89/#88` 与 `#68` 聚合 closeout 消费完成；父 FR closeout 由 `#95` / PR `#96` 承接
  - 关系段保持：层级 `FR`、版本 `v0.2.0`、父阶段 `#63`、子 Work Item 包含 `#68` 与 `#95`
- `#64` closeout 评论草案：
  - `FR-0004` formal spec 已由 PR `#82` 合入主干，spec 真相位于 `docs/specs/FR-0004-input-target-and-collection-policy/`
  - `#87` / PR `#90` 已完成 Core 显式接收 `InputTarget` 与 `CollectionPolicy` 以及最小结构校验
  - `#89` / PR `#91` 已完成 Core 到 adapter-facing request 的共享投影与 admission 承接
  - `#88` / PR `#92` 已完成 `FR-0002` legacy URL 到 `url + hybrid` 的兼容映射、反例与验证证据
  - `#68` / PR `#93` 已完成 implementation 聚合 closeout，并统一 release / sprint / exec-plan 回链
  - 当前父事项 closeout 已由 `#95` / PR `#96` 收口，`docs/releases/v0.2.0.md`、`docs/sprints/2026-S15.md` 与 active exec-plan 已与 GitHub 真相一致
- `#85` 处理方案：
  - 在关闭 `#64` 后，向 `#85` 发布说明评论：该 issue 仅为 `spec_issue_sync.py` 维护的 spec 索引镜像；`FR-0004` 的 canonical scheduling issue 为 `#64`，且已由 `#95` / PR `#96` 完成父事项 closeout
  - 随后关闭 `#85`，避免 GitHub 上残留第二个 open FR-0004 issue 镜像
  - 若后续需要恢复 `FR-0004` closeout，则按“GitHub 侧回滚”步骤先重新打开 `#85`

## 未决风险

- 若 `#64` 关闭前不修正文中的 `formal spec：待创建`，会继续造成 GitHub issue 与主干事实失配。
- 若 `#85` 留作 `OPEN`，GitHub 上会继续存在第二个 open FR-0004 issue 镜像，破坏 closeout 语义的一致性。

## 回滚方式

- 仓内回滚：如需回滚，使用独立 revert PR 撤销本事项对 `docs/exec-plans/FR-0004-input-target-and-collection-policy.md`、`docs/exec-plans/CHORE-0095-fr-0004-parent-closeout.md`、`docs/exec-plans/CHORE-0068-fr-0004-implementation-closeout.md`、`docs/specs/FR-0004-input-target-and-collection-policy/plan.md`、`docs/releases/v0.2.0.md` 与 `docs/sprints/2026-S15.md` 的增量修改。
- GitHub 侧回滚：
  - 若已编辑 `#64` 正文但 PR 未合入，恢复 `#64` 到 closeout 前正文，并保留 `#64`、`#85` 为 `OPEN`
  - 若已发布 `#64` closeout 评论但发现仓内工件仍不一致，在 `#64` 追加纠正评论并停止关闭动作
  - 若 `#85` 已关闭但 `#64` closeout 需要撤回，先重新打开 `#85` 并说明恢复原因为“FR-0004 父事项 closeout 回滚”
  - 若 `#64` 已关闭后发现 closeout 事实错误，先重新打开 `#64`，再通过独立 revert PR 与新的 closeout 回合修复仓内 / GitHub 状态

## 最近一次 checkpoint 对应的 head SHA

- `654f085c62c78a78e870a5e79b3b277ea5bed934`
- 说明：其后的提交仅用于收口 guardian 指出的 `#95` 关闭路径、GitHub closeout 工件与 checkpoint 叙述，不改写 `FR-0004` requirement truth；当前受审 head 以 PR `#96` 最新 head 与 guardian verdict 绑定为准。
