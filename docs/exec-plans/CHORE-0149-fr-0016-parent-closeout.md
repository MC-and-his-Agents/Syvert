# CHORE-0149 FR-0016 parent closeout 执行计划

## 关联信息

- item_key：`CHORE-0149-fr-0016-parent-closeout`
- Issue：`#225`
- item_type：`CHORE`
- release：`v0.6.0`
- sprint：`2026-S19`
- 父 FR：`#219`
- 关联 spec：`docs/specs/FR-0016-minimal-execution-controls/`
- 状态：`active`

## 目标

- 在不引入新 runtime 或 formal spec 语义的前提下，收口 `FR-0016` 父事项。
- 将 formal spec、runtime implementation、验证证据、GitHub issue / Project 状态与当前主干事实对齐。

## 范围

- 本次纳入：
  - `docs/exec-plans/CHORE-0149-fr-0016-parent-closeout.md`
  - `docs/exec-plans/FR-0016-minimal-execution-controls.md` 的 inactive requirement container closeout 索引
  - 合入后 GitHub `#219/#225` 状态与 Project closeout 对齐
- 本次不纳入：
  - `syvert/**` runtime 代码
  - `tests/**` 测试实现
  - `FR-0016` formal spec 语义变更
  - `FR-0017/#227`、`FR-0018/#232`、`FR-0019/#234` 的后续实现或 gate matrix

## 当前停点

- `#223` formal spec closeout 已由 PR `#237` squash merge，merge commit `295b565adae2a384d3a314755706d66c5ea59b09`。
- `#224` runtime implementation 已由 PR `#247` squash merge，merge commit `6590801d561a44db21fc07014948d33f427fd3a0`。
- `#223` 与 `#224` GitHub issue 均已关闭，Project 状态均为 `Done`。
- `#219` 仍为 `OPEN` / Project `Todo`，等待本父事项 closeout 回写后关闭。
- `#225` 当前 PR：`#248 https://github.com/MC-and-his-Agents/Syvert/pull/248`
- 当前 worktree：`/Users/mc/code/worktrees/syvert/issue-225-chore-fr-0016`
- 当前主干基线：`6590801d561a44db21fc07014948d33f427fd3a0`

## 下一步动作

- 消费 PR `#248` 的 CI、guardian 与 merge gate 反馈。
- 合入后 fast-forward main。
- 更新 `#225` 正文为已完成并关闭，Project 状态切到 `Done`。
- 在 `#219` 发布 closeout 评论，引用 `#223/#224/#225` 与 PR `#237/#247/#248`，随后关闭父 FR 并切 Project 到 `Done`。
- 退役 `issue-225-chore-fr-0016` 分支与 worktree。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.6.0` 完成 `timeout_retry_concurrency` 维度的父事项收口，使后续 `FR-0019/#234` operability gate matrix 可以直接引用 `FR-0016` 的 formal spec、runtime evidence 与 GitHub closeout truth。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0016` parent closeout Work Item。
- 阻塞：
  - `#227/#228` 之后的 `#234` gate matrix 需要 `FR-0016` closeout truth。
  - `#236` release closeout 前必须完成 `#219` 父 FR 状态同步。

## closeout 证据

- formal spec 证据：
  - PR `#237`：冻结 `ExecutionControlPolicy`、attempt timeout、Core-owned retry predicate、fail-fast concurrency gate、`ExecutionAttemptOutcome` 与 `ExecutionControlEvent`。
  - 主干路径：`docs/specs/FR-0016-minimal-execution-controls/`
- runtime 证据：
  - PR `#247`：在 Core `execute_task_with_record` 路径内实现 attempt timeout、固定 retry predicate、process-local concurrency slot 与 admission guard。
  - 关键验证：`tests/runtime/test_execution_control.py` 覆盖 timeout closeout、retry、pre/post accepted concurrency rejection、accepted/resource-prep 窗口、slot accounting invariant 与 shared envelope 投影。
## 已验证项

- `gh pr view 237 --json state,mergedAt,mergeCommit,headRefOid,url`
  - 结果：`state=MERGED`，`mergedAt=2026-04-23T17:01:50Z`，`mergeCommit=295b565adae2a384d3a314755706d66c5ea59b09`
- `gh pr view 247 --json state,mergedAt,mergeCommit,headRefOid,url`
  - 结果：`state=MERGED`，`mergedAt=2026-04-25T02:49:07Z`，`mergeCommit=6590801d561a44db21fc07014948d33f427fd3a0`
- `gh issue view 219 --json title,state,body,projectItems`
  - 结果：`#219` 为 `OPEN`，Project 状态为 `Todo`
- `gh issue view 223 --json title,state,projectItems`
  - 结果：`#223` 为 `CLOSED`，Project 状态为 `Done`
- `gh issue view 224 --json title,state,projectItems`
  - 结果：`#224` 为 `CLOSED`，Project 状态为 `Done`
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过，`spec-guard 通过。`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过，`docs-guard 通过。`
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过，`workflow-guard 通过。`
- `python3 scripts/governance_gate.py --mode local --base-ref origin/main`
  - 结果：通过，`governance-gate 通过。`
- `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，`PR scope 校验通过。`

## 待完成

- 合入本 closeout PR `#248`。
- 合入后将 `#225` 正文更新为已完成并关闭，Project 切到 `Done`。
- 回写并关闭父 FR `#219`，说明 formal spec 与 runtime evidence 已合入主干。
- fast-forward main，退役 `issue-225-chore-fr-0016` 分支与 worktree。

## 未决风险

- 若 `#219` 关闭前未引用 `#223/#224/#225` 与 PR `#237/#247`，后续 `FR-0019/#234` gate matrix 回溯 `timeout_retry_concurrency` 证据时需要手工拼接。
- 若误在本事项修改 runtime 或 formal spec，可能破坏 `#224` 已通过 guardian 的实现边界。

## 回滚方式

- 仓内回滚：使用独立 revert PR 撤销本事项对 `docs/exec-plans/*FR-0016*` closeout 元数据的修改。
- GitHub 侧回滚：若已关闭 `#219/#225` 后发现 closeout 事实错误，重新打开对应 issue，追加纠正评论，并通过新的 closeout Work Item 修复仓内事实。

## 最近一次 checkpoint 对应的 head SHA

- 本 exec-plan 是 `#225` 的首个版本化恢复工件；恢复点由 PR `#248` 的 live head 与 guardian / merge gate 绑定。
- 当前可恢复 checkpoint：`b32f963c4277b7b837d46dfbe79d91baebfb59ab`
- 不使用 `6590801d561a44db21fc07014948d33f427fd3a0` 作为本文件 checkpoint，因为该主干基线不包含 `CHORE-0149-fr-0016-parent-closeout.md`。
- 本次追加 `FR-0016` inactive requirement container 索引与 GitHub 验证入口属于 `metadata-only closeout follow-up`，不推进新的 runtime / formal spec 语义。
