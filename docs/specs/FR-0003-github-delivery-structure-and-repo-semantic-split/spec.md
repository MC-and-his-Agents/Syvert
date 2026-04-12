# FR-0003 GitHub delivery structure and repo semantic split

## 关联信息

- item_key：`FR-0003-github-delivery-structure-and-repo-semantic-split`
- Issue：`#55`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`

## 背景与目标

- 背景：当前仓库治理文档已经建立了 `Issue / item_key / release / sprint` 事项上下文与受控入口，但顶层分层口径仍混有“版本层 / 冲刺层 / 事项层”与 GitHub `Phase / FR / Work Item` 两套表达，导致 GitHub 调度层与仓内语义层的边界不够稳定。
- 目标：正式定义“GitHub 单一调度层 + 仓内单一语义层”的治理契约，并把 GitHub 层级收敛为 `Phase -> FR -> Work Item`，确保 formal spec、exec-plan、PR、release/sprint 索引都能围绕同一层级模型稳定协作。

## 范围

- 本次纳入：
  - 定义 GitHub 与仓库的职责边界
  - 定义 `Phase / FR / Work Item` 的职责与关闭语义
  - 规定 `Work Item` 是唯一执行入口
  - 规定 `FR` 是 canonical requirement 容器，formal spec 绑定到 FR
  - 规定 `release / sprint` 只保留为执行上下文或仓内索引语义
  - 收敛 legacy `TODO.md` 在 formal governance flow 中的地位
  - 冻结 legacy `TODO.md` 退出 formal governance flow 后必须满足的最小语义：formal spec 最小套件、模板、review / workflow 规则、guard、policy、测试与存量清理边界
- 本次不纳入：
  - 与 legacy `TODO.md` 清理无关的 `scripts/**` 行为改造
  - 与 legacy `TODO.md` 清理无关的 harness 自动化入口、guardian、merge gate 运行时改造
  - 与本事项无关的业务实现代码
  - 任何业务实现代码或业务 spec

## 需求说明

- 功能需求：
  - GitHub 必须被定义为单一调度层，负责 `Phase / FR / Work Item`、状态、优先级、依赖、关闭语义、Sprint / Project 排期。
  - 仓库必须被定义为单一语义层，负责 formal spec、exec-plan、风险、验证证据、checkpoint、恢复上下文。
  - `Work Item` 必须被定义为唯一执行入口；只有它可以建 worktree、开 PR、进入执行回合。
- 契约需求：
  - `FR` 必须被定义为 canonical requirement 容器，formal spec 绑定到 FR，而不是绑定到 Phase 或 Work Item。
  - `Phase` 必须被定义为阶段目标容器，不直接承载执行 PR。
  - `release / sprint` 必须被定义为执行上下文或仓内索引语义，不得退化为第二套状态真相源。
  - post-transition 的 formal spec 最小套件定义为 `spec.md` + `plan.md`；legacy `TODO.md` 不得再被视为必需工件、状态镜像或恢复入口，未触碰的历史文件只允许以 inert legacy 形式留在仓库中。
  - governance guard 与 policy 必须把 legacy `TODO.md` 视为 inert 历史文件：允许未触碰时保留、允许通过删除完成清理、禁止新增或继续回写。
- 非功能需求：
  - 所有相关治理文档口径必须一致，不能出现并行分层定义。
  - 本事项必须保持 governance-only 边界，不混入业务实现代码。
  - `GOV-0029` 的 formal spec 收敛与后续治理实现必须分开进入独立 PR。

## 约束

- 阶段约束：
  - 本事项服务于 `pre-v0.2.0 kickoff governance convergence`，只做治理契约收敛。
- 架构约束：
  - GitHub 不承载 formal spec 正文、exec-plan 或 checkpoint 细节。
  - 仓库不承载 backlog / sprint / project 状态真相。
  - formal spec 与实现 PR 仍默认分离。
  - `GOV-0029` 必须先通过独立 formal spec 审查，再以独立 governance 实现 PR 落地模板、guard、policy、测试与存量 legacy `TODO.md` 清理。

## GWT 验收场景

### 场景 1

Given GitHub 事项树中存在 `Phase -> FR -> Work Item` 父子结构  
When 仓库文档描述治理层级与职责边界  
Then 文档必须把 GitHub 描述为单一调度层，并明确 `Phase / FR / Work Item` 的各自职责

### 场景 2

Given 当前 Work Item 进入执行回合  
When agent 创建 worktree、更新 exec-plan、打开 PR  
Then 文档必须明确只有 Work Item 可以执行这些动作，FR 与 Phase 只能作为上位容器被引用

### 场景 3

Given 一个 FR 已建立 formal spec 套件且关联多个 Work Item  
When 审查需求归属与执行归属  
Then 文档必须明确 formal spec 绑定 FR，exec-plan 与 PR 绑定各自 Work Item

### 场景 4

Given 仓内存在历史 `TODO.md`，但当前 PR 没有触碰该文件  
When reviewer / guardian 按 formal governance flow 审查当前事项  
Then legacy `TODO.md` 可以作为未触碰的 inert 历史文件保留，但不得被要求作为 formal spec 必需项、恢复主入口或必须同步维护的流程工件

### 场景 5

Given 当前 formal spec / governance contract PR 已把高优先级治理文档口径收成一致  
When `GOV-0029` 的后续独立 governance 实现 PR 对已授权套件删除 legacy `TODO.md` 并同步修改 guard / policy / `open_pr` / 回归测试  
Then 删除必须被允许，且实现链路必须覆盖 guard、policy、`open_pr`、回归测试与存量 suite 清理的对齐收口

### 场景 6

Given `GOV-0029` 先以 formal spec / governance contract PR 更新 `FR-0003` formal spec  
When 后续需要落地模板、guard、policy、测试与存量 legacy `TODO.md` 清理  
Then 必须另开独立 governance 实现 PR；若 PR 继续回写或新增 legacy `TODO.md`，则必须被拒绝

## 异常与边界场景

- 异常场景：
  - 若文档继续把 release / sprint 写成状态真相源，会与 GitHub 单一调度层冲突。
  - 若文档允许 Phase 或 FR 直接开 PR / 建 worktree，会破坏 Work Item 唯一执行入口约束。
- 边界场景：
  - legacy `TODO.md` 可以作为历史文件被清理，但不得再作为 formal governance flow 的必需工件或恢复入口。
    - `release / sprint` 允许继续作为仓内索引存在，但只能承担聚合与执行上下文职责。
  - `GOV-0029` 可在独立实现 PR 中清理存量 legacy `TODO.md`，但不得在 formal spec PR 中直接混入实现代码或测试改造。

## 验收标准

- [ ] `AGENTS.md`、`WORKFLOW.md`、`docs/AGENTS.md`、`docs/process/delivery-funnel.md`、`docs/process/agent-loop.md` 对 GitHub / 仓库边界口径一致
- [ ] 文档明确写出 `Phase / FR / Work Item` 各自职责
- [ ] 文档明确写出 `Work Item` 是唯一执行入口
- [ ] formal spec 明确绑定 FR，exec-plan 明确绑定 Work Item
- [ ] release / sprint 被定义为执行上下文或索引，而不是状态真相源
- [ ] 当前 formal spec / governance contract PR 已让 `WORKFLOW.md`、`docs/AGENTS.md`、`spec_review.md`、`docs/specs/README.md` 与 `docs/process/agent-loop.md` 对 legacy `TODO.md` 的治理口径一致
- [ ] 后续独立 governance 实现 PR 已让 `docs/specs/_template/**`、formal spec 最小套件、guard、policy、`open_pr` 与 `tests/governance/**` 对 legacy `TODO.md` 的处理收口一致，并完成存量 legacy `TODO.md` 清理

## 依赖与外部前提

- 外部依赖：
  - GitHub 中已存在 `#54 -> #55 -> #56/#57/#58` 的事项树
- 上下游影响：
  - `#57` 在此 formal spec 基础上完成 harness 兼容迁移
  - `#58` 在此 formal spec 基础上先完成规约审查，再进入独立治理实现 PR 收口 legacy `TODO.md`
