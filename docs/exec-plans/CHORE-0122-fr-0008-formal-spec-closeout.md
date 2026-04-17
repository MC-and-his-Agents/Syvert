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
- guardian 首轮审查已返回 `REQUEST_CHANGES`，指出两项 formal spec 自相矛盾：
  - 是否把“尚未通过共享 admission”的失败纳入 `TaskRecord` 生命周期
  - `TaskTerminalResult` 是否额外引入重复的 `status` 轴
- guardian 第二轮审查继续返回 `REQUEST_CHANGES`，指出三项未冻结清楚的 contract：
  - 初始 `accepted` 建档本身是否 fail-closed
  - post-admission 共享失败是否一律纳入 durable `TaskRecord`
  - 读侧是否会拒绝生命周期不完整的持久化历史
- guardian 第三轮审查继续返回 `REQUEST_CHANGES`，指出 `FR-0008` 对 pre-`accepted` admission/pre-execution 失败与 post-`accepted` durable failure 的边界仍未和上游 `FR-0004` / `FR-0005` contract 完全对齐。
- 当前 checkpoint `1f3b833555de3e8e4f74ea0d0de075aa67ae099c` 已按前三轮 guardian 结论收口：
  - 把可持久化失败限定为“已通过共享 admission 并进入执行主路径之后”的失败
  - 删除 `TaskTerminalResult.status`，改为由 `envelope.status` 作为唯一终态结果状态真相源
  - 初始 `accepted` 建档失败被明确为进入后续共享执行前的 fail-closed 阻断
  - post-admission 共享失败被统一纳入 durable `TaskRecord`
  - 读侧非法记录规则已补齐“缺少当前状态要求的生命周期事件”这一类截断历史
  - `accepted` 的建档时点已明确后移到“共享 admission + 共享 pre-execution 校验全部通过之后”，从而与 `FR-0004` / `FR-0005` 已冻结的 admission/pre-execution 失败语义保持一致

## 下一步动作

- 推送当前 head，等待 `PR #145` checks 与 guardian 重新绑定到最新提交。
- 基于当前 checkpoint 重跑 guardian，确认已消除 formal spec 边界阻断。
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
- `python3 scripts/pr_guardian.py review 145`
  - 结果：guardian 首轮返回 `REQUEST_CHANGES`
  - 已修复阻断：
    - 共享 admission 拒绝不再被错误写入 `TaskRecord` 生命周期
    - `TaskTerminalResult` 不再额外持久化 shadow `status`
- `python3 scripts/pr_guardian.py review 145`
  - 结果：guardian 第二轮返回 `REQUEST_CHANGES`
  - 已修复阻断：
    - 初始 `accepted` 建档失败必须在进入后续执行前 fail-closed
    - post-admission 共享失败必须统一纳入 durable `TaskRecord`
    - 读侧必须拒绝生命周期不完整的持久化历史
- `git commit -m 'docs(spec): 收紧 FR-0008 持久化生命周期契约'`
  - 结果：已生成 checkpoint `f6c799cd86bae44c9eff0752562fb24b84dd8721`
- `git commit -m 'docs(spec): 明确 FR-0008 durable truth 边界'`
  - 结果：已生成 checkpoint `60acbdd673fa3e653c348ca58a586cc8ef8f19d9`
- `python3 scripts/pr_guardian.py review 145`
  - 结果：guardian 第三轮返回 `REQUEST_CHANGES`
  - 已修复阻断：
    - `accepted` 只在共享 admission 与共享 pre-execution 校验全部通过后创建
    - unsupported capability / target_type / collection_mode、registry / declaration 失败等上游 pre-execution 失败被明确留在 pre-`accepted` 边界之外
- `git commit -m 'docs(spec): 对齐 FR-0008 与上游 admission 边界'`
  - 结果：已生成 checkpoint `1f3b833555de3e8e4f74ea0d0de075aa67ae099c`

## 未决风险

- 若 formal spec 提前混入 `FR-0009` 的查询 surface，后续实现边界会重新漂移。
- 若 formal spec 没有把“持久化失败必须 fail-closed”写成硬约束，实现阶段容易退化为 stdout/stderr 成功但无 durable truth 的假闭环。

## 回滚方式

- 使用独立 revert PR 撤销本事项对 `FR-0008` formal spec 套件、当前 active exec-plan 与 `v0.3.0` / `2026-S16` 索引的更新。

## 最近一次 checkpoint 对应的 head SHA

- `1f3b833555de3e8e4f74ea0d0de075aa67ae099c`
