# Syvert 仓库宪法

## 项目使命

Syvert 是一个统一承载和治理互联网操作任务及其资源的稳定底座。
本仓库聚焦 `Core + Adapter SDK + 参考适配器 + 探索/验证工具`，用统一任务、资源与结果契约承载互联网操作，不以适配对象数量增长定义成功。

## Loom 上游治理层

Syvert 正式消费 Loom 作为上游 governance runtime 与 canonical governance layer。

Loom 承接跨仓通用治理能力：Work Item admission、gate chain、status control plane、maturity upgrade、GitHub profile binding、closeout / reconciliation 与 shadow parity boundary。

Syvert 继续保留 repo-owned residue：产品使命、roadmap、release / sprint / item_key 业务上下文、guardian 实现、integration contract、adapter/runtime/resource lifecycle 与历史执行证据。

`.loom/companion/` 是 Loom 读取 Syvert repo-specific residue 的正式入口；它不替代本文件、`WORKFLOW.md`、guardian 或 integration contract。

## 宪法规则

1. Core 负责运行时语义，Adapter 负责目标系统语义。
2. 目标系统特定逻辑不得渗入 Core。
3. Adapter 对外运行时契约必须统一；当前验证切片中的成功结果继续返回 `raw payload` 与 `normalized result`。
4. 禁止直推 `main`，所有变更必须经分支与 PR 合入。
5. 合入 `main` 默认使用 Squash Merge。
6. Commit Message 必须使用中文 Conventional Commits。
7. GitHub 是单一调度层，负责 `Phase / FR / Work Item`、状态、优先级、依赖、关闭语义与 Sprint / Project 排期。
8. 仓库是单一语义层，负责 formal spec、exec-plan、风险、验证证据、checkpoint 与恢复上下文。
9. Work Item 是唯一执行入口；只有 Work Item 可以建 worktree、开 PR、进入执行回合。
10. FR 是 canonical requirement 容器；formal spec 绑定到 FR，不绑定到 Phase 或 Work Item。
11. Phase 只承载阶段目标，不直接承载执行 PR。
12. release / sprint 只保留为执行上下文或仓内索引语义，不得退化为状态真相源。
13. 正式规约区与实现区必须分离，正式 `spec` 变更不得与实现代码混入同一 PR。
14. 每个活跃分支默认使用独立 worktree。
15. 核心上下文必须进入版本控制，不得只留在会话里。
16. 通用治理语义默认指向 Loom；Syvert 只维护本仓库特有的业务、运行时、guardian 与 integration residue。

## 当前阶段

- 项目名：`Syvert`
- 仓库路径：`/Users/mc/dev/Syvert`
- 策略：单仓库演进
- 首批参考适配器：小红书、抖音
- 近目标：`v0.1.0` 证明同一 Core 契约可运行两个真实参考适配器

## 权威来源

文档冲突时按以下优先级处理：

1. [AGENTS.md](./AGENTS.md)
2. [vision.md](./vision.md)
3. [docs/roadmap-v0-to-v1.md](./docs/roadmap-v0-to-v1.md)
4. [WORKFLOW.md](./WORKFLOW.md)
5. [docs/AGENTS.md](./docs/AGENTS.md)
6. [docs/process/delivery-funnel.md](./docs/process/delivery-funnel.md)
7. [spec_review.md](./spec_review.md)
8. [code_review.md](./code_review.md)

## 读取顺序

讨论定位与边界时：

1. [AGENTS.md](./AGENTS.md)
2. [vision.md](./vision.md)
3. [docs/roadmap-v0-to-v1.md](./docs/roadmap-v0-to-v1.md)

讨论流程、审查与合入时：

1. [AGENTS.md](./AGENTS.md)
2. [WORKFLOW.md](./WORKFLOW.md)
3. [docs/AGENTS.md](./docs/AGENTS.md)
4. [docs/process/delivery-funnel.md](./docs/process/delivery-funnel.md)
5. [spec_review.md](./spec_review.md)
6. [code_review.md](./code_review.md)

## 交付漏斗

唯一默认路径：

`Roadmap / 阶段目标 -> GitHub Phase -> GitHub FR -> GitHub Work Item -> spec / contract -> spec review -> implementation PR -> PR review -> squash merge`

## 文档索引

- [WORKFLOW.md](./WORKFLOW.md)：agent 运行契约唯一来源
- [.loom/companion/README.md](./.loom/companion/README.md)：Loom 读取 Syvert repo-specific residue 的入口
- [docs/process/agent-loop.md](./docs/process/agent-loop.md)：checkpoint / resume / compact 协议
- [docs/process/worktree-lifecycle.md](./docs/process/worktree-lifecycle.md)：workspace/worktree 生命周期协议
- [docs/process/branch-retirement.md](./docs/process/branch-retirement.md)：分支归档与退役协议
- [spec_review.md](./spec_review.md)：正式规约套件准入标准
- [code_review.md](./code_review.md)：实现 PR 审查标准与 merge gate
