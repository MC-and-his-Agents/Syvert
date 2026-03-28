# Syvert 文档工作流

本文档只定义 `docs/` 子树的工作流、文档语义和正式规约区约束。
全局纪律、仓库边界和合入原则以根级 [AGENTS.md](../AGENTS.md) 为准。

## 目录职责

```text
docs/
 ├── AGENTS.md
 ├── roadmap-v0-to-v1.md
 ├── process/
 ├── specs/
 ├── decisions/
 └── exec-plans/
```

- `roadmap-v0-to-v1.md`：阶段目标与版本边界
- `process/`：交付流程、执行协议、治理方法
- `specs/`：正式规约区
- `decisions/`：方向或架构决策记录
- `exec-plans/`：跨多轮任务的计划与恢复工件

## 研发漏斗

Syvert 采用单向漏斗，不做本地 Markdown 与 GitHub Issues 的双向镜像。

1. 需求池与状态只在 GitHub Issues / Projects 中维护。
2. 事项确认后，按 [docs/process/delivery-funnel.md](./process/delivery-funnel.md) 进入正式漏斗。
3. 正式 `spec` 合入后成为仓库中的契约工件；修订必须通过独立 PR。
4. 仓库中的 `TODO.md`、计划或 handoff 只服务执行恢复，不承担 GitHub 任务真相源职责。

## 事项分流

- 轻量事项
  - 适用：纯文案修正、格式整理、非契约性说明补充
  - 默认输入：Issue（如有）+ PR
- 中等事项
  - 适用：跨多个文件，但不改变上位边界、共享契约或共享数据模型
  - 默认输入：Issue + 简化设计说明或 PR 描述 + PR
- 核心事项
  - 适用：Core/Adapter 契约变更、正式规约、治理基线、高风险运行时、跨模块设计
  - 默认输入：完整 `spec` 套件 + `spec review`
  - 治理 bootstrap 例外：若事项本身是在 `main` 首次建立治理/规约基础设施，可先使用 `Issue + decision + exec-plan` 作为 bootstrap contract；落地后恢复正式 `spec` 常态路径

成熟度状态统一为：

- `spec-ready`
- `implementation-ready`
- `merge-ready`

## 正式规约区

`docs/specs/` 是正式规约区，不是 backlog 草稿区，也不是讨论草稿区。

补充规则：

- 正式 FR 目录命名采用 `FR-XXXX-<slug>`
- 标准套件最小包含 `spec.md`、`plan.md`、`TODO.md`
- `TODO.md` 可在实现 PR 中回写进度，但不得修改正式契约语义
- 正式 `spec` 与实现代码默认分离到不同 PR；例外必须满足 `spec_review.md` 的放行条件

## 模板与载体职责

- Issue：事项目标、边界、关闭条件
- Project：状态、优先级、排期
- `spec.md`：需求、验收、异常与边界
- `plan.md`：实施拆分、依赖、验证、进入实现前条件
- `TODO.md`：执行停点、恢复入口、阻断项
- PR：本次改动范围、风险、验证证据、关闭语义

## 文档与门禁的关系

- 本地 hook 提供早反馈，帮助作者在提交前发现基础问题。
- CI 提供仓库级门禁，保证 PR 不绕过正式校验。
- guardian 只负责 merge gate，不负责定义文档语义。

如果文档规则与脚本门禁发生冲突，应优先修正文档和单一规则源，再调整脚本实现，避免长期漂移。
