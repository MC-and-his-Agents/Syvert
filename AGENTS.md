# Syvert 仓库宪法

## 项目使命

Syvert 是一个任务驱动、适配器可插拔的采集底座。

它的目标不是堆积内置平台实现，而是构建一个稳定的 Core，使不同平台的接入能力可以通过统一契约被接入、执行、治理、审计和演进。

本仓库不是平台集合仓库。
本仓库是 `Core + Adapter SDK + 参考适配器 + 探索/验证工具` 的宿主。


## 宪法规则

以下规则属于仓库宪法，默认不可违背。

1. Core 负责运行时语义，Adapter 负责平台语义。
2. 平台特定逻辑不得渗入 Core。
3. Core 的增长方向是运行时能力，而不是内置平台覆盖数量。
4. Adapter 内部实现技术可以自由选择，但对外运行时契约必须统一。
5. Adapter 必须同时返回 `raw payload` 和 `normalized result`。
6. 参考适配器用于验证 Core 边界，不用于定义产品价值。
7. 对长期协作重要的上下文必须进入版本控制，而不能只存在于聊天记录中。
8. 愿景文档不承载架构细节，路线图不承载产品口号，SDK 文档不承载方向争论。
9. 禁止直推 `main`，所有代码和文档变更都必须在独立分支完成，并通过 PR 合入。
10. 合入 `main` 默认使用 Squash Merge。
11. Commit Message 必须使用中文，并遵循 Conventional Commits。
12. GitHub Issues / Projects 是任务状态、优先级和排期的唯一真理；仓库内只保留实现工件，不保留 backlog 或 sprint 镜像文件。
13. 每个活跃分支默认使用独立 worktree，不在同一个工作目录中来回切换多个分支。


## 当前状态

当前项目处于方向已收敛、实现尚未展开的阶段。

当前已确认的事实：

- 项目名是 `Syvert`
- 当前仓库路径是 `/Users/claw/dev/syvert`
- 当前策略是单仓库演进
- 第一批参考适配器固定为：
  - 小红书
  - 抖音
- 当前主目标是验证 `Core` 契约，而不是扩张平台数量

当前近目标：

- `v0.1.0` 证明一个 Core 可以在同一套契约下运行两个真实参考适配器

当前仓库现实状态：

- [vision.md](/Users/claw/dev/syvert/vision.md) 已建立
- [docs/roadmap-v0-to-v1.md](/Users/claw/dev/syvert/docs/roadmap-v0-to-v1.md) 已建立
- [architecture.md](/Users/claw/dev/syvert/architecture.md) 当前不存在，不得假定其已定义任何结构
- `docs/decisions/` 当前尚未建立，未来若记录方向或架构决策，应优先使用该目录而不是单一汇总文件


## 权威来源

文档冲突时，按以下优先级处理：

1. [AGENTS.md](/Users/claw/dev/syvert/AGENTS.md)
2. [vision.md](/Users/claw/dev/syvert/vision.md)
3. [docs/roadmap-v0-to-v1.md](/Users/claw/dev/syvert/docs/roadmap-v0-to-v1.md)
4. [adapter-sdk.md](/Users/claw/dev/syvert/adapter-sdk.md)
5. [framework-positioning.md](/Users/claw/dev/syvert/framework-positioning.md)

补充规则：

- 空文件、占位文件、历史遗留文件不是权威来源
- 若某文档已被替代，替代关系必须在仓库中显式可见
- 方向级判断优先看 `vision.md`
- 范围级判断优先看 `roadmap`
- 宪法、读取顺序、执行协议优先看 `AGENTS.md`


## 强制阅读路径

只读取必要内容，但必须按正确顺序读取。

产品定位、命名、边界讨论：

1. [AGENTS.md](/Users/claw/dev/syvert/AGENTS.md)
2. [vision.md](/Users/claw/dev/syvert/vision.md)
3. [docs/roadmap-v0-to-v1.md](/Users/claw/dev/syvert/docs/roadmap-v0-to-v1.md)

Core 边界、版本范围、系统主线讨论：

1. [AGENTS.md](/Users/claw/dev/syvert/AGENTS.md)
2. [vision.md](/Users/claw/dev/syvert/vision.md)
3. [docs/roadmap-v0-to-v1.md](/Users/claw/dev/syvert/docs/roadmap-v0-to-v1.md)
4. [framework-positioning.md](/Users/claw/dev/syvert/framework-positioning.md)

Adapter 契约、参考适配器相关讨论：

1. [AGENTS.md](/Users/claw/dev/syvert/AGENTS.md)
2. [vision.md](/Users/claw/dev/syvert/vision.md)
3. [adapter-sdk.md](/Users/claw/dev/syvert/adapter-sdk.md)
4. [docs/roadmap-v0-to-v1.md](/Users/claw/dev/syvert/docs/roadmap-v0-to-v1.md)

开始任何跨文件实现前：

1. 先确认当前任务适用的权威文档
2. 再确认当前阶段边界
3. 再决定是否需要创建或更新计划/决策记录


## 执行协议

### 通用规则

对任何非琐碎任务：

1. 先用仓库术语定义任务，而不是只用聊天术语
2. 先确认任务受哪些文档约束
3. 优先做最小且不破坏方向清晰度的改动
4. 任务完成后，仓库本身必须能解释改了什么、为什么改
5. 默认在独立分支上工作，不在 `main` 上直接开展实现或文档修改
6. 默认为当前工作分支分配独立 worktree，降低并行开发和多 agent 协作时的上下文污染

### 多步任务

对任何跨文件、跨阶段或跨多轮任务：

1. 必须留下可恢复工件
2. 计划、决策、进度至少要有一个进入版本控制
3. 不允许把关键前提只留在聊天里
4. 不允许通过代码改动悄悄重定义产品边界
5. 若任务属于当前阶段核心项，应先形成 `spec`、`contract` 或等价工件，再进入实现

### 完成标准

完成一个任务时，应满足：

1. 相关文档与实现不发生明显冲突
2. 未解决问题被显式记录
3. 若改变了方向、边界或执行方式，必须同步更新对应文档
4. 变更应通过 PR 进入主干，并默认以 Squash Merge 合并


## 仓库地图

当前顶层文件职责：

- [AGENTS.md](/Users/claw/dev/syvert/AGENTS.md)
  仓库宪法、全局上下文入口、读取顺序、执行协议
- [vision.md](/Users/claw/dev/syvert/vision.md)
  产品愿景、长期定位、成功标准
- [framework-positioning.md](/Users/claw/dev/syvert/framework-positioning.md)
  当前定位草稿，偏产品结构与边界
- [adapter-sdk.md](/Users/claw/dev/syvert/adapter-sdk.md)
  当前适配器契约草稿
- [docs/roadmap-v0-to-v1.md](/Users/claw/dev/syvert/docs/roadmap-v0-to-v1.md)
  从 `v0.1.0` 到 `v1.0.0` 的阶段路线

`docs/` 应逐步成为仓库记录系统，未来承载：

- 决策记录
- 架构文档
- 执行计划
- 规格说明
- 参考资料摘要
- 生成型工件

建议的未来文档形态：

- `docs/decisions/`：离散的方向/架构决策记录
- `docs/exec-plans/`：跨多轮任务的执行计划与进度
- `docs/specs/`：实现前规格

明确不应保留的仓库内工件：

- backlog 镜像
- sprint 看板镜像
- Issue 状态副本

未来目录职责目标：

- `core/` 负责运行时
- `sdk/` 负责适配器契约
- `adapters/` 负责参考适配器与外部接入
- `tooling/` 负责探索与验证工具

当前不要把未来目录目标误当成已经存在的实现结构。

worktree 约束：

- 一个活跃分支对应一个独立 worktree
- 不在同一个工作目录中频繁切换不同分支
- 并行任务、并行 agent、实验性修改必须优先使用独立 worktree
- 仓库初始化期若尚无首个提交，可暂时在主工作目录启动；首个提交后应尽快切换到 worktree 模式


## 变更规则

修改 Core 相关内容时：

- 不得引入平台特定分支来描述 Core
- 不得以内置适配器数量来定义成功
- 不得把平台实现细节写进愿景级文档

修改 Adapter 相关内容时：

- 保持“技术实现自由，运行时契约统一”的边界
- 标准化责任留在 Adapter，不回流到 Core
- `raw + normalized` 结果规则不得丢失

修改资源模型相关内容时：

- 先定义资源语义，再讨论具体实现
- Core 可以认识资源类别，不应硬绑定具体技术栈

修改仓库治理相关内容时：

- 优先增强人和 agent 的长期协作能力
- 优先采用显式、可版本化、可校验的规则
- 优先索引知识，而不是重复堆砌长文
- 不要在仓库中引入与 GitHub Issues / Projects 重复的进度追踪体系
- 优先使用独立 worktree 承载并行分支，避免工作区串扰

修改测试相关内容时：

- 单元测试放在被测文件同级 `__tests__/`
- 集成测试、端到端测试、contract 测试统一放在仓库根目录 `tests/`
- 新能力默认采用 `contract + TDD + spec` 共同驱动

修改交付流程相关内容时：

- 默认推进顺序是：
  `Roadmap / 阶段目标 -> GitHub backlog -> 选择当前项 -> spec / contract -> review -> 实施 -> PR review -> squash merge`
- 项目以阶段目标驱动推进，必要时采用短 Sprint，但不把 Sprint 仪式本身当作顶层约束


## 文档规则

1. `AGENTS.md` 负责规则、优先级、当前状态、阅读顺序和执行协议。
2. `vision.md` 负责解释项目为什么存在、要成为什么。
3. `roadmap` 负责定义分阶段目标，不代表已实现事实。
4. `framework-positioning` 和 `adapter-sdk` 属于实现前草稿，不自动高于宪法与愿景。
5. 空文档不是事实源。
6. 新文档若替代旧文档，必须显式写出替代关系。
7. `docs/specs/`、`docs/decisions/`、`docs/exec-plans/` 属于实现工件，允许保留；backlog 和 sprint 管理文件不应进入仓库。


## 工作标准

Syvert 应能被一个新工程师或一个新 agent 读懂，而不依赖口头传承。

如果关键上下文不在仓库里，工作就还没有完成。
