# Syvert 文档工作流

本文档只定义 `docs/` 子树语义与交付工件职责。
根级约束以 [AGENTS.md](../AGENTS.md) 为准，运行契约以 [WORKFLOW.md](../WORKFLOW.md) 为准。

## 目录职责

- `docs/roadmap-v0-to-v1.md`：阶段目标与版本边界
- `docs/releases/`：release 聚合索引与模板
- `docs/sprints/`：sprint 聚合索引与模板
- `docs/process/delivery-funnel.md`：唯一交付漏斗
- `docs/process/agent-loop.md`：长任务协议与恢复规则
- `docs/process/worktree-lifecycle.md`：worktree 生命周期规则
- `docs/process/branch-retirement.md`：分支归档与退役规则
- `docs/specs/`：正式规约区
- `docs/decisions/`：决策记录
- `docs/exec-plans/`：事项执行上下文、执行计划与恢复工件

## 术语与状态

- 事项上下文字段：`Issue` / `item_key` / `item_type` / `release` / `sprint`
- 事项类型：`FR` / `HOTFIX` / `GOV` / `CHORE`
- 事项术语：`轻量事项` / `中等事项` / `核心事项`
- 执行术语：
  - `新事项`：首次进入当前交付漏斗、且尚未形成 active `exec-plan` 恢复工件的事项
  - `存量事项`：已存在仓库内恢复工件，但尚未补齐当前事项上下文字段的事项；若缺少 active `exec-plan`，仍不得视为已具备当前执行回合恢复入口
  - `长任务`：需要 `checkpoint / resume / handoff` 恢复能力，并因此维护 `exec-plan` 的执行回合
- GitHub 层次术语：`Phase` / `FR` / `Work Item`
- 仓内语义术语：`formal spec` / `exec-plan` / `decision` / `release index` / `sprint index`
- 成熟度术语：`spec-ready` / `implementation-ready` / `merge-ready`

## 层次职责

- `Phase`
  - GitHub 单一调度层中的阶段目标容器
  - 负责阶段边界、上位目标与关闭语义
  - 不直接承载 formal spec、worktree 或执行 PR
- `FR`
  - GitHub 单一调度层中的 requirement 容器
  - 是 canonical requirement 容器
  - formal spec 绑定到 FR，不绑定到 Phase 或 Work Item
- `Work Item`
  - GitHub 单一调度层中的唯一执行入口
  - 负责进入 worktree、执行回合、PR、review 与 closeout
- `docs/releases/**`
  - release 目标、完成判据与事项聚合索引
  - 是仓内索引，不是 GitHub 状态真相源
- `docs/sprints/**`
  - sprint 执行轮次与工件入口索引
  - 是仓内索引，不是 GitHub 状态真相源
- `docs/specs/**`
  - FR 对应的正式规约语义层
- `docs/exec-plans/**`
  - Work Item 对应的执行与恢复语义层

## 统一事项身份

- 仓内事项统一使用 `item_key` 作为聚合键。
- 支持前缀：`FR`、`HOTFIX`、`GOV`、`CHORE`
- 命名格式：`<PREFIX>-<4位编号>-<slug>`
- `PREFIX` 必须全大写，`slug` 使用短横线英文短语。
- 一个事项在仓内只对应一个 `item_key`。
- 新事项与存量事项在进入新的执行回合前，都必须在相关工件中显式声明 `item_key` 并补齐事项上下文。
- 历史事项允许保留旧文件名；若未迁移，只要求在后续增量工件中保持关联一致，不做一次性全量追溯。

## 正式规约区规则

`docs/specs/` 只承载正式规约，不承载 backlog 草稿。

- FR 目录命名：`FR-XXXX-<slug>`
- 最小套件：`spec.md`、`plan.md`
- 正式规约与实现默认分 PR；例外按 [spec_review.md](../spec_review.md) 执行
- formal spec 绑定到 GitHub FR；Work Item 只通过 `item_key`、exec-plan、PR 与该 formal spec 建立关联

## 载体职责

- GitHub Phase：阶段目标与上位关闭条件
- GitHub FR：canonical requirement、formal spec 绑定点与上位关闭条件
- GitHub Work Item：执行入口、PR 关闭语义与回合级 closeout
- GitHub Project / Sprint：状态、优先级、排期与执行轮次
- `docs/releases/**`：release 目标、完成判据、事项聚合入口
- `docs/sprints/**`：sprint 协作主题、退出条件与工件入口
- `spec.md`：需求、验收、异常与边界
- `plan.md`：实施拆分、依赖、验证、进入实现前条件
- `exec-plan`：长任务执行细节、事项上下文、checkpoint 与恢复上下文；是默认恢复主入口
- PR：仅绑定当前 Work Item 的变更范围、风险、验证证据、关闭语义，并显式引用上位 FR / Phase

## 聚合原则

- 不采用“每个事项目录里混放 `spec`、`exec-plan`、`decision`”的物理嵌套方案。
- 继续使用“按工件类型分区、按绑定关系逻辑聚合”的模型：formal spec 绑定 FR `item_key`，active `exec-plan` 绑定当前 Work Item `item_key`。
- `docs/releases/` 与 `docs/sprints/` 是横向索引层，不是新的事实源，也不回写 GitHub backlog 状态。
- 仓库内不得再引入与 GitHub `Phase / FR / Work Item` 并行的第二套调度层级。

## 门禁关系

- 本地 hook：早反馈，不替代 CI
- reviewer：按 `spec_review.md` / `code_review.md` 的 rubric 做实质审查，不由 CI 或 guardian 代替
- CI：仓库自动化门禁，不替代 reviewer 的语义审查，也不替代 guardian 的合并前门禁
- guardian：基于当前 PR head 与最小必要上下文执行 merge gate 审查，不替代 reviewer 的 rubric 判断
- `merge_pr`：受控合并入口，消费 guardian + checks + head 一致性结果，不替代 reviewer / guardian / CI 任何一方
- review rubric != merge gate；前者判断质量与阻断项，后者判断当前 head 是否允许受控合并
- review / guardian 输入优先采用最小必要上下文，避免与当前事项无关的重复探索
