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
- 不从仓库内 Markdown 获取 backlog 或 sprint 状态，也不在仓库内维护 sprint 状态镜像。
- 每次执行需绑定事项上下文，并在 PR 中显式关联。
- 事项上下文最少包含：
  - `Issue`
  - `item_key`
  - `item_type`
  - `release`
  - `sprint`
- `Issue` 仍是任务状态真相源入口；`item_key`、`release`、`sprint` 是执行上下文字段，不替代 GitHub Issues / Projects。
- `docs/releases/` 与 `docs/sprints/` 只承载仓内聚合索引，不替代 GitHub Issues / Projects 的状态真相源。
- 新事项与存量事项在进入新的执行回合前都必须补齐完整事项上下文。
- 术语约定：
  - `新事项`：首次进入当前交付漏斗、且尚未在仓库内形成 `exec-plan` / `TODO.md` 恢复工件的事项
  - `存量事项`：在本协议升级前已存在仓库内恢复工件，但尚未补齐事项上下文的事项
  - `长任务`：需要 `checkpoint -> resume -> handoff` 恢复能力，并因此必须维护 `exec-plan` 的执行回合

## worktree / bootstrap 规则

- worktree key 固定为 `issue-{number}-{slug}`。
- 优先通过 `python3 scripts/create_worktree.py --issue <n> --class <class>` 创建或复用工作区。
- 分支完成合入或确认被替代后，通过 `python3 scripts/retire_branch.py` 执行归档与退役。
- worktree key 仍仅由 `Issue` 生成；`item_key`、`release`、`sprint` 不改变现有 worktree 生成与复用机制。
- `item_type` 当前约定为：`FR` / `HOTFIX` / `GOV` / `CHORE`。
- `item_key` 固定命名为 `<item_type>-<4-digit>-<slug>`，例如：`FR-0123-content-detail-runtime`、`GOV-0007-release-sprint-protocol`。
- `release` 用于标识事项服务的版本目标；`sprint` 用于标识事项所在执行轮次。
- 治理基线自举允许 `Issue + decision + exec-plan` 作为 bootstrap contract。
- 非治理基线事项进入实现前必须有 formal spec 输入。
- 每个执行回合必须有且仅有一个 active `exec-plan` 与当前 `item_key` 一一对应；上位前提事项可在该工件中被引用，但不替代当前事项的 active 工件。

## checkpoint / resume / compact 规则

- 长任务统一按 `kickoff -> checkpoint -> compact -> resume -> handoff -> merge-ready` 执行。
- `核心事项` 强制存在 `exec-plan`，并记录事项上下文、停点、下一步、已验证项、未决风险、最近一次 checkpoint 对应的 head SHA。
- `exec-plan` 中的 head SHA 用于恢复最近一次 checkpoint，不替代 guardian 对当前受审 head SHA 的绑定与 merge gate 校验。
- 仅当执行回合显式推进新的 checkpoint 时，才刷新 `exec-plan` 中记录的 checkpoint head。
- review 结论、GitHub checks、PR 关联、索引入口等审查态信息的更新，不自动构成新的 checkpoint。
- checkpoint 与 resume 必须保持 `Issue`、`item_key`、`release`、`sprint` 一致；若事项上下文发生变化，必须先更新 `exec-plan` 与 `TODO.md`，再继续执行。
- checkpoint 必须说明当前改动推进了哪个 `release` 目标，以及该事项在当前 `sprint` 中的角色或位置。
- `compact` 仅压缩已入库且可复验的信息，不得压缩未落盘前提。
- `compact` 不得压缩未落盘的事项上下文判断，包括 `release`、`sprint` 绑定与事项角色判定。
- 具体协议以 `docs/process/agent-loop.md` 为准。

## stop conditions

- 缺少必需输入（Issue、事项上下文、formal spec 或 bootstrap contract）。
- 任一进入执行回合的事项缺少 `item_key` / `item_type` / `release` / `sprint` 绑定。
- 当前改动越过阶段边界或破坏规约/实现分离。
- 关键门禁失败且无法在当前回合消除。
- guardian 结果不是 `APPROVE` 或 `safe_to_merge=false`。

## 何时必须更新 `exec-plan` / `TODO`

- 完成一组可验证改动后必须更新一次 checkpoint。
- 变更停点、风险、验证结论或形成新的 checkpoint 时必须更新。
- 若仅发生后续跟进 commit、但尚未形成新的 checkpoint，可保留最近一次 checkpoint head，并由 guardian state 绑定当前受审 head。
- 若仅补充 review / merge gate 元数据，而未显式推进新的执行停点，不要求刷新 checkpoint head。
- 变更 `item_key`、`item_type`、`release`、`sprint` 或事项在当前轮次中的定位时必须更新。
- 进入 review、进入 merge gate 前必须更新到最新状态。

## 何时允许进入 `open_pr` / `merge_pr`

- 进入 `open_pr` 条件：
  - 已声明 PR class 且与改动类别一致
  - 已通过受控入口显式填写完整事项上下文，且该事项在进入当前执行回合前已完成补齐
  - 当前事项存在 `docs/exec-plans/<item_key>.md` 形式的 active `exec-plan`
  - active `exec-plan` 的 `item_key` / `Issue` / `item_type` / `release` / `sprint` 与受控入口填写值一致
  - 若 active `exec-plan` 声明 `active 收口事项`，其值必须与当前 `item_key` 一致
  - PR 描述、风险与验证信息可映射回 `Issue`、`item_key`、`release`、`sprint`
  - `核心事项` 已满足 formal spec 或 bootstrap contract 输入
  - 风险、验证、回滚信息已就绪
- 进入 `merge_pr` 条件：
  - latest guardian verdict=`APPROVE`
  - `safe_to_merge=true`
  - GitHub checks 全绿
  - PR 非 Draft，且审查与合并使用同一 head SHA
