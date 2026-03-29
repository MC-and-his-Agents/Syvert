# Syvert Worktree Lifecycle

## key 与命名

- worktree key 固定：`issue-<number>-<slug>`
- 目录命名由 `WORKFLOW.md` 的 `workspace.naming` 决定，当前固定为 `issue-{number}-{slug}`

## 创建与复用顺序

1. 使用 `create_worktree.py` 读取 `WORKFLOW.md`。
2. 计算 workspace root 与 key。
3. 若同 key worktree 已存在则复用。
4. 不存在时创建分支与 worktree，并写入状态面。

## branch / worktree / issue 对应关系

- 一个 Issue 对应一个确定性 worktree key。
- 分支默认与 worktree key 对齐，当前实现为 `issue-<number>-<slug>`。
- 状态映射写入 `$CODEX_HOME/state/syvert/worktrees.json`。

## 清理与恢复

- 终止事项后可清理 worktree，但保留状态记录直到关闭周期完成。
- 恢复时优先读取状态面，按 key 定位已有 worktree。
- head SHA 漂移时先刷新状态，再继续执行。
- 分支退役前必须先解除 worktree 绑定；退役顺序以 [branch-retirement.md](./branch-retirement.md) 为准。

## 路径写入边界

- 允许写入：
  - 当前仓库工作目录
  - `WORKFLOW.md` 约定的 workspace root 下的 issue worktree
  - `$CODEX_HOME/state/syvert/` 状态文件
- 禁止写入：
  - 仓库外的任意其他业务目录
  - 未在契约中声明的全局状态目录
