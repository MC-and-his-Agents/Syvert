# Syvert Branch Retirement

## 目标

- 为已吸收、已替代或已失效的分支保留可追溯归档锚点。
- 删除前先证明分支不再承担活跃工作区职责。
- 避免因 `squash merge` 或独立根历史导致“内容已吸收但分支仍悬挂”。

## 分类

- `merged`
  - 分支提交已是替代分支的祖先提交，可直接按已吸收退役。
- `superseded`
  - 分支内容已被后续 PR、squash merge 或新治理基线替代，但提交图不满足 ancestry。
  - 必须显式声明 `replaced_by` 与 `reason`。

## 退役顺序

1. 确认当前不在目标分支上操作。
2. 确认目标分支未绑定活跃 worktree。
3. 创建归档锚点：
   - 标签命名固定：`archive/branches/<branch>`
   - 标签消息至少记录：`branch`、`sha`、`strategy`、`replaced_by`、`reason`、`retired_at`
4. 如需退役远端分支，先推送归档标签，再删除远端分支。
5. 清理 `$CODEX_HOME/state/syvert/worktrees.json` 中指向该分支的 stale state。
6. 最后删除本地分支。

## 工具入口

- dry-run：
  - `python3 scripts/retire_branch.py --branch <name> --strategy merged --dry-run`
- 已吸收分支：
  - `python3 scripts/retire_branch.py --branch <name> --replaced-by main --strategy merged`
- 已替代分支：
  - `python3 scripts/retire_branch.py --branch <name> --replaced-by main --strategy superseded --reason "<why>"`
- 需要同步删除远端时：
  - 额外增加 `--delete-remote`

## 安全边界

- 不在活跃分支或活跃 worktree 上直接执行退役。
- `merged` 策略只接受真实 ancestry，不把 patch 近似当成已合并。
- `superseded` 策略必须显式填写替代关系与原因，避免无依据删除。
- 退役脚本不负责判断产品方向正确性，只负责归档锚点与删除顺序正确。

## 当前已退役分支记录

| branch | strategy | replaced_by | archive tag | 说明 |
| --- | --- | --- | --- | --- |
| `codex/repo-governance` | `superseded` | `main (PR #1 / 480ee1d)` | `archive/branches/codex/repo-governance` | 独立根历史上的治理 v1 分支，内容已由 PR `#1` 的 squash 结果吸收 |
| `codex/remove-soft-collab-language` | `superseded` | `main (PR #7 / 7fc5e5a)` | `archive/branches/codex/remove-soft-collab-language` | 旧治理文档支线，意图已由治理栈 v2 文档收敛吸收 |
