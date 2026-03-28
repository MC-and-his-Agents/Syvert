---
tracker:
  kind: github
  scope: current-repo
workspace:
  root: $SYVERT_WORKSPACE_ROOT
  naming: issue-{number}-{slug}
agent:
  max_turns: 20
codex:
  thread_sandbox: workspace-write
  approval_policy: never
---

# Syvert Repo Workflow Contract

## 任务输入来源

- 任务来源固定为当前仓库的 GitHub Issues / Projects。
- 不从仓库内 Markdown 获取 backlog 或 sprint 状态。
- 每次执行需绑定 Issue 编号，并在 PR 中显式关联。

## worktree / bootstrap 规则

- worktree key 固定为 `issue-{number}-{slug}`。
- 优先通过 `python3 scripts/create_worktree.py --issue <n> --class <class>` 创建或复用工作区。
- 治理基线自举允许 `Issue + decision + exec-plan` 作为 bootstrap contract。
- 非治理基线事项进入实现前必须有 formal spec 输入。

## checkpoint / resume / compact 规则

- 长任务统一按 `kickoff -> checkpoint -> compact -> resume -> handoff -> merge-ready` 执行。
- `核心事项` 强制存在 `exec-plan`，并记录停点、下一步、已验证项、未决风险、当前 head SHA。
- `compact` 仅压缩已入库且可复验的信息，不得压缩未落盘前提。
- 具体协议以 `docs/process/agent-loop.md` 为准。

## stop conditions

- 缺少必需输入（Issue、formal spec 或 bootstrap contract）。
- 当前改动越过阶段边界或破坏规约/实现分离。
- 关键门禁失败且无法在当前回合消除。
- guardian 结果不是 `APPROVE` 或 `safe_to_merge=false`。

## 何时必须更新 `exec-plan` / `TODO`

- 完成一组可验证改动后必须更新一次 checkpoint。
- 变更停点、风险、验证结论或 head SHA 时必须更新。
- 进入 review、进入 merge gate 前必须更新到最新状态。

## 何时允许进入 `open_pr` / `merge_pr`

- 进入 `open_pr` 条件：
  - 已声明 PR class 且与改动类别一致
  - `核心事项` 已满足 formal spec 或 bootstrap contract 输入
  - 风险、验证、回滚信息已就绪
- 进入 `merge_pr` 条件：
  - latest guardian verdict=`APPROVE`
  - `safe_to_merge=true`
  - GitHub checks 全绿
  - PR 非 Draft，且审查与合并使用同一 head SHA
