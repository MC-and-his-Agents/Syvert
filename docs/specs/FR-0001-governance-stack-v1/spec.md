# FR-0001 治理栈 v1 闭环

## 背景与目标

- 背景：Syvert 当前阶段需要一套可执行、可审计、可回归的治理基线，用于约束文档分层、正式规约、PR 分流、CI 门禁和受控 merge 入口。本事项绑定 GitHub Issue `#5`。
- 目标：建立治理栈 v1 的最小闭环，使治理规则既能进入版本控制，也能被 hook、CI 和本地 guardian 一致执行。

## 范围

- 本次纳入：
  - 根级与 `docs/` 子树治理文档分层
  - 正式规约区模板与审查标准
  - 本地 hook 与 CI 门禁
  - `open_pr`、`pr_guardian`、`merge_pr`、`review_poller` 等受控入口
  - GitHub Issue / PR / branch protection 的最小协作约束
- 本次不纳入：
  - 将 AI guardian 绑定到 GitHub-hosted CI
  - 在仓库内维护 backlog 或 sprint 镜像
  - 将 formal spec 正文镜像回 GitHub Issue

## 需求说明

- 功能需求：
  - 治理栈必须提供单一规则源，用于 PR 类别、路径分类和正式规约最低结构。
  - 治理栈必须提供本地早反馈与仓库级 CI 门禁。
  - merge 动作必须通过受控入口执行，不能把裸 `gh pr merge` 作为日常路径。
  - guardian 审查结果必须绑定当前 `head SHA`，且只允许受控 merge 入口消费最新有效结果。
- 契约需求：
  - 正式 merge gate 必须以统一口径表达：`verdict=APPROVE`、`safe_to_merge=true`、PR 非 Draft、审查与合并使用同一 `head SHA`、GitHub checks 全绿。
  - `governance` 类 PR 必须允许携带与其绑定的正式规约输入，但不得与实现代码混改。
- 非功能需求：
  - 复杂治理逻辑统一用 Python 3.9+ 标准库实现。
  - 关键治理脚本必须有可回归测试。

## 约束

- 阶段约束：当前阶段目标是建立治理基线，不扩展产品功能，不引入平台特定实现。
- 架构约束：
  - hook 不替代 CI，CI 不替代 guardian，guardian 不替代人工方向判断。
  - GitHub Issues / Projects 仍是任务状态真相源。
  - guardian 作为本地/运维工具运行，不进入 GitHub-hosted CI。

## GWT 验收场景

### 场景 1

Given 仓库存在正式治理文档、policy 配置和 hook / CI 脚本  
When 开发者在独立分支上创建 `governance` 类 PR  
Then PR 能通过中文 Conventional Commits、docs guard、spec guard 和 governance gate 的基础校验

### 场景 2

Given 某个 PR 已通过最新 guardian 审查并产出绑定当前 `head SHA` 的有效结果  
When 通过 `merge_pr` 进入受控 merge 入口  
Then merge 入口消费该有效结果，并在 GitHub checks 全绿、PR 非 Draft、head 未变化时完成 squash merge

### 场景 3

Given `merge_pr` 运行时未找到绑定当前 `head SHA` 的有效 guardian 结果  
When merge 入口执行合并前校验  
Then merge 入口必须先补跑新的 guardian 审查，再根据新结果决定是否允许合并

## 异常与边界场景

- 异常场景：
  - guardian 未给出 `APPROVE` 或 `safe_to_merge=false` 时，受控 merge 入口必须拒绝合并。
  - GitHub checks 未全绿、PR 为 Draft、或 PR `head SHA` 与最新 guardian 审查不一致时，受控 merge 入口必须拒绝合并。
  - `governance` 类 PR 混入实现代码时，CI 必须阻断。
- 边界场景：
  - `governance` 类 PR 可以携带与本事项绑定的 formal spec 工件，用于满足核心事项的正式输入要求。
  - formal spec 的 `TODO.md` 可在后续实现 PR 中回写进度，但不得修改正式规约语义。

## 验收标准

- [ ] 治理栈 v1 的文档、脚本、hook、CI 和 merge 入口都进入版本控制
- [ ] merge gate 在高优先级文档中只有一套一致口径
- [ ] guardian verdict 复用只信任绑定当前 `head SHA` 的本地受控结果
- [ ] `tests/governance` 覆盖 guardian verdict 复用与补跑路径
- [ ] 本事项关联 GitHub Issue，并具备 formal spec 输入

## 依赖与外部前提

- 外部依赖：
  - 本地存在 `gh` 与 `codex` CLI，并完成认证
  - GitHub 仓库已开启 branch protection 与 squash merge only
- 上下游影响：
  - 后续所有 `governance` / `spec` / `implementation` / `docs` PR 都会受该治理基线约束
