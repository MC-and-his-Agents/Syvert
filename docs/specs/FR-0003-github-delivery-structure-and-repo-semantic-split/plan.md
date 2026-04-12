# FR-0003 实施计划

## 关联信息

- item_key：`FR-0003-github-delivery-structure-and-repo-semantic-split`
- Issue：`#55`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 exec-plan：`docs/exec-plans/GOV-0027-governance-contract-rewrite.md`、`docs/exec-plans/GOV-0028-harness-compat-migration.md`、`docs/exec-plans/GOV-0029-remove-legacy-todo-md.md`

## 实施目标

- 为 `FR-0003` 建立正式规约入口，冻结 GitHub 调度层与仓内语义层的职责边界。
- 通过 `GOV-0027`、`GOV-0028`、`GOV-0029` 分别完成治理契约落盘、harness 兼容迁移与 legacy `TODO.md` 退出 formal governance flow 的收口。
- 让当前 Work Item 可以通过受控入口合法开 PR、通过审查并完成 closeout。

## 分阶段拆分

- 阶段 1：建立 `FR-0003` formal spec 套件，冻结治理 requirement 与边界。
- 阶段 2：更新顶层治理文档，消除“版本层 / 冲刺层 / 事项层”与 `Phase / FR / Work Item` 的冲突。
- 阶段 3：补齐 `v0.2.0` / `2026-S15` 索引，以及 `GOV-0027`、`GOV-0028`、`GOV-0029` 的 exec-plan / decision 工件链，完成受控 PR 前置条件。
- 阶段 4：由 `GOV-0029` 先完成独立 formal spec / governance contract 审查，收敛 `FR-0003` formal spec、本轮 decision / exec-plan、`WORKFLOW.md`、`docs/AGENTS.md`、`spec_review.md`、`docs/specs/README.md`、`docs/process/agent-loop.md` 与 `docs/specs/_template/**` 的权威口径。
- 阶段 5：在后续独立 governance PR 中落地 guard、policy、`open_pr`、回归测试与存量 legacy `TODO.md` 清理。

## 实现约束

- 不允许触碰的边界：
  - 当前 formal spec / governance contract PR 只允许修改 `FR-0003` formal spec 套件、当前事项 decision / exec-plan、release / sprint 索引，以及使 TODO-exit 语义成为权威口径所必需的治理文档与模板
  - `GOV-0029` 对 `scripts/**`、`scripts/policy/**`、`tests/governance/**`、`open_pr` 行为与存量 suite 清理必须放在后续独立 governance PR
  - 不混入与 `TODO.md` 清理无关的治理改造
  - 不混入业务实现代码
- 与上位文档的一致性约束：
  - 与 `AGENTS.md`、`vision.md`、`docs/roadmap-v0-to-v1.md` 保持阶段边界一致
  - 与 `WORKFLOW.md`、`docs/process/delivery-funnel.md`、`docs/process/agent-loop.md` 保持执行入口与状态真相边界一致

## 测试与验证策略

- 单元测试：
  - formal spec PR 运行 `docs_guard` 与 `spec_guard --all`，确认 formal spec 套件与文档引用结构合法
- 集成/契约测试：
  - formal spec PR 运行 `open_pr --class spec --dry-run` 与 `pr_scope_guard --class spec`，确认当前事项可通过独立规约审查入口
  - 后续独立 governance PR 再运行治理测试套件、`context_guard`、`workflow_guard`、`governance_gate` 与 `open_pr --class governance --dry-run`
- 手动验证：
  - 核对 GitHub `#54 / #55 / #56 / #57 / #58` 与仓内 `FR-0003 / GOV-0027 / GOV-0028 / GOV-0029 / v0.2.0 / 2026-S15` 的映射关系

## TDD 范围

- 先写测试的模块：
  - 无。formal spec PR 本身不引入运行时代码；相关 guard / policy 回归测试放在后续独立 governance PR 中完成
- 暂不纳入 TDD 的模块与理由：
  - formal spec 与索引工件更新属于规约审查输入，不在当前 PR 中实现对应运行时行为

## 并行 / 串行关系

- 可并行项：
  - formal spec 套件编写
  - release / sprint 索引与 decision / exec-plan 补齐
- 串行依赖项：
  - `GOV-0027`、`GOV-0028`、`GOV-0029` 开 PR 前，必须先完成 formal spec、exec-plan 与索引落盘
  - `GOV-0029` 的独立 governance PR 必须等待当前 formal spec PR 合入 `main`
  - merge 前，必须完成当前 PR 所需的 review、guardian 与 checks
- 阻塞项：
  - 若 `release` / `sprint` 索引缺失或 active `exec-plan` 不合法，受控入口会直接拒绝

## 进入实现前条件

- [x] `spec review` 已通过
- [x] 关键风险已记录并有缓解策略
- [x] 关键依赖可用

## spec review 结论

- 结论：`FR-0003` 既有基线已通过；当前 `GOV-0029` 正在对 legacy `TODO.md` 退出 formal governance flow 做增量规约审查
- 未决问题：需确认 legacy `TODO.md` 退出 formal governance flow 的规范来源、实施范围与后续独立治理实现边界已收敛一致
- implementation-ready 判定：`FR-0003` 既有基线已满足；待当前 formal spec PR 通过后，`GOV-0029` 的新增语义扩展为新的已批准基线，并继续进入独立 governance 实现 PR
