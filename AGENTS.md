# Syvert 仓库宪法

## 项目使命

Syvert 是任务驱动、适配器可插拔的采集底座。
本仓库聚焦 `Core + Adapter SDK + 参考适配器 + 探索/验证工具`，不以平台数量增长定义成功。

## 宪法规则

1. Core 负责运行时语义，Adapter 负责平台语义。
2. 平台特定逻辑不得渗入 Core。
3. Adapter 对外运行时契约必须统一，且返回 `raw payload` 与 `normalized result`。
4. 禁止直推 `main`，所有变更必须经分支与 PR 合入。
5. 合入 `main` 默认使用 Squash Merge。
6. Commit Message 必须使用中文 Conventional Commits。
7. GitHub Issues / Projects 是任务状态真相源，仓库内不保留 backlog 或 sprint 镜像。
8. 正式规约区与实现区必须分离，正式 `spec` 变更不得与实现代码混入同一 PR。
9. 每个活跃分支默认使用独立 worktree。
10. 核心上下文必须进入版本控制，不得只留在会话里。

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

`Roadmap / 阶段目标 -> GitHub backlog -> 候选项 -> spec / contract -> spec review -> implementation PR -> PR review -> squash merge`

## 文档索引

- [WORKFLOW.md](./WORKFLOW.md)：agent 运行契约唯一来源
- [docs/process/agent-loop.md](./docs/process/agent-loop.md)：checkpoint / resume / compact 协议
- [docs/process/worktree-lifecycle.md](./docs/process/worktree-lifecycle.md)：workspace/worktree 生命周期协议
- [spec_review.md](./spec_review.md)：正式规约套件准入标准
- [code_review.md](./code_review.md)：实现 PR 审查标准与 merge gate
