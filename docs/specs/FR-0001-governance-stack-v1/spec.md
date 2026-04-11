# FR-0001 治理栈 v2 Repo Harness 闭环

## 背景与目标

- 背景：v1 已建立规则闭环，但尚缺 repo harness 层的运行契约、长任务恢复协议、workspace 生命周期与统一状态面。本事项绑定 GitHub Issue `#6`。
- 目标：建立治理栈 v2，使规则闭环升级为 `Repo Harness` 闭环，并保持本地优先、可执行、可回归。

## 范围

- 本次纳入：
  - 运行契约 `WORKFLOW.md`
  - `agent-loop` 与 `worktree-lifecycle` 协议
  - `create_worktree`、`governance_status`、`workflow_guard`、`sync_repo_settings` 入口
  - 现有 `open_pr`、`pr_guardian`、`review_poller`、`governance_gate` 升级
  - GitHub 仓库侧设置的脚本化对齐
- 本次不纳入：
  - 常驻 daemon 编排器
  - tracker 抽象层
  - 将 AI guardian 绑定到 GitHub-hosted CI
  - 在仓库内维护 backlog 或 sprint 镜像
  - 将 formal spec 正文镜像回 GitHub Issue

## 需求说明

- 功能需求：
  - 提供可被脚本读取的 `WORKFLOW.md` 运行契约。
  - 提供长任务 checkpoint / resume / compact 统一协议。
  - 提供 worktree 生命周期入口，输出确定性 workspace。
  - 提供统一状态面，聚合 guardian、review poller、worktree、checks。
  - merge 动作必须通过受控入口，guardian 结果必须绑定 `head SHA`。
- 契约需求：
  - `WORKFLOW.md` front matter 顶层键固定为 `tracker`、`workspace`、`agent`、`codex`。
  - `tracker.kind=github`，`tracker.scope=current-repo`。
  - `workspace.root` 支持 `$SYVERT_WORKSPACE_ROOT`，默认 `~/code/worktrees/syvert`。
  - `workspace.naming=issue-{number}-{slug}`。
  - merge gate 统一口径保持：`APPROVE`、`safe_to_merge=true`、checks 全绿、PR 非 Draft、head 一致。
- 非功能需求：
  - 复杂治理逻辑统一用 Python 3.9+ 标准库实现。
  - 关键治理脚本必须有可回归测试。

## 约束

- 阶段约束：当前阶段目标是建立治理基线，不扩展产品功能，不引入平台特定实现。
- 架构约束：
  - hook 不替代 CI，CI 不替代 guardian。
  - GitHub Issues / Projects 仍是任务状态真相源。
  - guardian 作为本地/运维工具运行，不进入 GitHub-hosted CI。

## GWT 验收场景

### 场景 1

Given 仓库存在合法 `WORKFLOW.md` 与 `docs/process/agent-loop.md`、`docs/process/worktree-lifecycle.md`  
When 执行 `workflow_guard` 于 pre-commit 或 CI  
Then 结构非法时必定失败，结构合法时通过

### 场景 2

Given 一个打开的 Issue 与合法 `WORKFLOW.md`  
When 执行 `create_worktree.py --issue <n> --class governance`  
Then 输出确定性 branch/worktree 路径，并在复用时保持同一 key

### 场景 3

Given 本地状态目录存在 guardian/review-poller/worktrees 记录  
When 执行 `governance_status.py`  
Then 可得到统一 text/json 状态视图，且兼容 legacy 状态读取

## 异常与边界场景

- 异常场景：
  - `WORKFLOW.md` 缺少必需键或必需段落时，本地与 CI 同时失败。
  - `governance` 或 `spec` 事项缺少 formal spec 或 bootstrap contract 时，`open_pr` 必须拒绝。
  - guardian 未给出 `APPROVE` 或 `safe_to_merge=false` 时，`merge_pr` 必须拒绝。
- 边界场景：
  - `docs/specs/**/TODO.md` 仅作为 legacy 历史文件保留；不得新增、回写进度、承载恢复上下文或作为正式治理流入口。
  - v2 不引入 daemon，不引入仓库内 backlog/sprint 镜像。

## 验收标准

- [ ] v2 文档契约（AGENTS/WORKFLOW/agent-loop/worktree-lifecycle）全部入库
- [ ] 新增 repo harness 脚本入口全部可执行并具备测试覆盖
- [ ] 状态面统一到 `$CODEX_HOME/state/syvert/`
- [ ] GitHub 仓库侧设置可被脚本 dry-run 校验
- [ ] 治理规则文档术语与门禁语义保持统一且无额外角色假设

## 依赖与外部前提

- 外部依赖：
  - 本地存在 `gh` 与 `codex` CLI，并完成认证
  - GitHub 仓库可访问 `branch protection` API
- 上下游影响：
  - 后续所有 `governance` / `spec` / `implementation` / `docs` PR 都受 v2 harness 门禁约束
