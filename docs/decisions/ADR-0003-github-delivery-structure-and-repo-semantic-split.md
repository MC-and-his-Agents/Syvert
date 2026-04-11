# ADR-0003 GitHub delivery structure and repo semantic split

## 关联信息

- Issue：`#57`
- item_key：`GOV-0028-harness-compat-migration`
- item_type：`GOV`
- release：`v0.2.0`
- sprint：`2026-S15`

## 背景

Syvert 已经有 `Issue / item_key / release / sprint` 事项上下文、worktree 入口、formal spec 套件与 exec-plan 恢复协议，但治理文档仍同时使用“版本层 / 冲刺层 / 事项层”与 GitHub `Phase / FR / Work Item` 两套分层描述。

这种双轨口径会让以下问题持续存在：

- formal spec 到底绑定 FR 还是绑定执行事项，不够稳定
- Phase / FR / Work Item 与 release / sprint 的职责边界不够清晰
- Work Item 是否是唯一执行入口，没有被提升为统一显式规则

## 决策

对 `pre-v0.2.0 kickoff governance convergence` 阶段，正式采用以下治理契约：

- GitHub 是单一调度层，负责 `Phase / FR / Work Item`、状态、优先级、依赖、关闭语义、Sprint / Project 排期
- 仓库是单一语义层，负责 formal spec、exec-plan、风险、验证证据、checkpoint、恢复上下文
- `Work Item` 是唯一执行入口；只有 Work Item 可以建 worktree、开 PR、进入执行回合
- `FR` 是 canonical requirement 容器；formal spec 绑定到 FR，而不是绑定到 Phase 或 Work Item
- `Phase` 只承载阶段目标，不直接承载执行 PR
- `release / sprint` 只保留为执行上下文或仓内索引语义，不得退化为状态真相源

## 非目标

- 不在本轮删除现有 `TODO.md`
- 不在本轮之外引入无关 harness 改造
- 不引入第二套仓内调度模型

## 影响

- 后续治理与实现事项都应围绕 GitHub `Phase -> FR -> Work Item` 层级组织
- formal spec 的主绑定点固定为 FR，执行回合的主绑定点固定为 Work Item
- `docs/releases/**` 与 `docs/sprints/**` 保留为仓内索引，不再承担状态真相解释职责
- `GOV-0028` 被授权把 harness、guard、template 与 review 输入迁移到新的治理契约，但不改动 `FR-0003` formal spec 套件的最小 contract。
- `GOV-0029` 仅在 `GOV-0028` 兼容路径稳定后，负责 legacy `TODO.md` 的最终删除清理。
