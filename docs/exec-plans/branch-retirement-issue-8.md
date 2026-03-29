# 分支归档/淘汰专项执行计划

## Issue

- `#8` 治理：收敛历史分支归档与淘汰流程

## 目标

- 为 Syvert 建立唯一的分支归档/淘汰协议。
- 提供本地可执行的分支退役入口，覆盖归档锚点、state 清理与本地/远端删除顺序。
- 安全退役当前遗留分支 `codex/repo-governance` 与 `codex/remove-soft-collab-language`。

## 范围

- `docs/process/branch-retirement.md`
- `scripts/retire_branch.py`
- `tests/governance/test_retire_branch.py`
- 文档索引与治理门禁引用更新

## 当前停点

- 已确认两条遗留分支的历史关系：
  - `codex/repo-governance`：独立根历史遗留，内容已被 PR `#1` 的 squash 结果吸收。
  - `codex/remove-soft-collab-language`：基于 `v1` 主干的旧增量分支，意图已被 PR `#7` 的治理文档重写吸收。

## 下一步动作

- 补齐退役脚本与测试。
- 生成归档锚点并执行实际退役。
- 用 `open_pr` 创建 governance PR，完成 guardian 与 merge gate。

## 已验证项

- 当前仓库只有主 worktree，未发现残留 guardian 临时 worktree。
- 两条候选分支均不再绑定活跃 worktree。
- 当前 `main` 与 `origin/main` 已对齐。

## 未决风险

- 若远端 archive tag 未先推送，删除远端分支会丢失可追溯锚点。
- 若 stale worktree state 未清理，后续状态面可能继续展示已退役分支。

## 当前 head SHA

- `7fc5e5ada722930bf61b30b911f5bb666948fad5`
