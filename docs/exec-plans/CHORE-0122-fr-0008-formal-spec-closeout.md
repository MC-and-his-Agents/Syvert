# CHORE-0122 执行计划

## 关联信息

- item_key：`CHORE-0122-fr-0008-formal-spec-closeout`
- Issue：`#137`
- item_type：`CHORE`
- release：`v0.3.0`
- sprint：`2026-S16`
- 关联 spec：`docs/specs/FR-0008-task-record-persistence/`
- 关联 PR：
- active 收口事项：`CHORE-0122-fr-0008-formal-spec-closeout`

## 目标

- 作为 `FR-0008` 下的真实 Work Item，完成任务记录与持久化 formal spec 的独立收口。
- 通过独立 spec PR 完成 checks / guardian / merge gate / closeout，使 `FR-0008` 在进入实现前形成主干上的 requirement truth。

## 范围

- 本次纳入：
  - `docs/specs/FR-0008-task-record-persistence/`
  - `docs/exec-plans/CHORE-0122-fr-0008-formal-spec-closeout.md`
  - `docs/releases/v0.3.0.md`
  - `docs/sprints/2026-S16.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `scripts/**`
  - `FR-0009` 的 CLI 查询 surface
  - `#138/#139/#140` 的实现与 closeout

## 当前停点

- `#137` 已作为 `FR-0008` formal spec 的真实执行入口建立独立 worktree，执行分支为 `issue-137-fr-0008-formal-spec`。
- `FR-0008` formal spec 套件、`v0.3.0` release 索引与 `2026-S16` sprint 索引已在当前分支首次落盘。
- 当前 checkpoint `1f67b47e83cc38158c6b50d4f8c950ad0204d7b2` 已冻结任务状态、终态结果、执行日志、共享序列化与本地持久化边界，并把 `FR-0008` 与 `FR-0009` 查询 surface 明确分离。

## 下一步动作

- 基于当前 checkpoint 运行 `governance_gate`、`open_pr --dry-run` 与受控推送。
- 通过受控入口创建 spec PR，并同步 `#137` / `#127` 的 GitHub 执行语义。
- 在 guardian / checks 通过后，用受控 merge 完成 PR 收口并关闭 `#137`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.3.0` 冻结最小任务记录与持久化 requirement，使后续实现 Work Item 可以在不改写需求的前提下落地共享模型与本地持久化管线。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0008` 的 spec-only closeout Work Item，负责把持久化任务记录 contract 先冻结为实现输入。
- 阻塞：
  - 必须先完成 formal spec 收口，`#138` / `#139` 才能合法进入 implementation PR。
  - 若状态/结果/日志或 fail-closed 边界在 formal spec 中表达不清，后续实现将不可避免地重新做 requirement 决策。

## 已验证项

- `gh issue view 127 --json number,title,body,state,projectItems,url`
- `gh issue view 137 --json number,title,body,state,projectItems,url`
- `gh issue view 128 --json number,title,body,state,url`
- `gh issue view 140 --json number,title,body,state,url`
- `gh issue view 141 --json number,title,body,state,url`
- `gh issue view 142 --json number,title,body,state,url`
- `gh issue view 143 --json number,title,body,state,url`
- `gh issue view 144 --json number,title,body,state,url`
- `sed -n '1,220p' vision.md`
- `sed -n '129,180p' docs/roadmap-v0-to-v1.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,260p' WORKFLOW.md`
- `sed -n '1,220p' docs/AGENTS.md`
- `sed -n '1,220p' spec_review.md`
- `python3 scripts/create_worktree.py --issue 137 --class spec`
  - 结果：已创建独立 worktree `/Users/mc/code/worktrees/syvert/issue-137-fr-0008-formal-spec`
- `python3 scripts/spec_guard.py --all`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `git commit -m 'docs(spec): 冻结 FR-0008 任务记录与持久化 formal spec'`
  - 结果：已生成 checkpoint `1f67b47e83cc38158c6b50d4f8c950ad0204d7b2`

## 未决风险

- 若 formal spec 提前混入 `FR-0009` 的查询 surface，后续实现边界会重新漂移。
- 若 formal spec 没有把“持久化失败必须 fail-closed”写成硬约束，实现阶段容易退化为 stdout/stderr 成功但无 durable truth 的假闭环。

## 回滚方式

- 使用独立 revert PR 撤销本事项对 `FR-0008` formal spec 套件、当前 active exec-plan 与 `v0.3.0` / `2026-S16` 索引的更新。

## 最近一次 checkpoint 对应的 head SHA

- `1f67b47e83cc38158c6b50d4f8c950ad0204d7b2`
