# FR-0001 契约说明

本事项不引入业务运行时契约，但会新增治理层稳定契约：

1. `WORKFLOW.md` 运行契约
   - front matter 顶层键固定：`tracker`、`workspace`、`agent`、`codex`
   - `tracker.kind=github`、`tracker.scope=current-repo`
   - `workspace.naming=issue-{number}-{slug}`

2. worktree 生命周期契约
   - `create_worktree.py` 负责创建/复用 `issue-<number>-<slug>` 分支与工作区
   - worktree 状态统一写入 `$CODEX_HOME/state/syvert/worktrees.json`

3. 状态面契约
   - `governance_status.py` 聚合 guardian、review poller、worktrees、checks
   - 状态目录固定为 `$CODEX_HOME/state/syvert/`

4. merge gate 契约
   - `pr_guardian` 输出 `verdict`、`safe_to_merge`、`summary`
   - `merge_pr` 只消费绑定当前 `head SHA` 的最新有效 guardian 结果
   - 判定字段与语义以 `code_review.md` 为准

如需细化 schema 与字段版本演进，在本目录增补独立契约文档。
