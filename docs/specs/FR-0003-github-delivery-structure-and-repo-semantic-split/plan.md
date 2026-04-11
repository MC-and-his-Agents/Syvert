# FR-0003 实施计划

## 关联信息

- item_key：`FR-0003-github-delivery-structure-and-repo-semantic-split`
- Issue：`#55`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 exec-plan：`docs/exec-plans/GOV-0027-governance-contract-rewrite.md`

## 实施目标

- 为 `FR-0003` 建立正式规约入口，冻结 GitHub 调度层与仓内语义层的职责边界。
- 通过 `GOV-0027` 对齐顶层治理文档、release/sprint 索引与 decision / exec-plan 工件链。
- 让当前 Work Item 可以通过受控入口合法开 PR、通过审查并完成 closeout。

## 分阶段拆分

- 阶段 1：建立 `FR-0003` formal spec 套件，冻结治理 requirement 与边界。
- 阶段 2：更新顶层治理文档，消除“版本层 / 冲刺层 / 事项层”与 `Phase / FR / Work Item` 的冲突。
- 阶段 3：补齐 `v0.2.0` / `2026-S15` 索引、`GOV-0027` exec-plan 与 decision，完成受控 PR 前置条件。

## 实现约束

- 不允许触碰的边界：
  - 只允许为关闭 legacy `TODO.md` 入口做最小必要的 `scripts/**`、`scripts/policy/**` 与 `tests/governance/**` 调整
  - 不混入与 `TODO.md` 清理无关的治理改造
  - 不混入业务实现代码
- 与上位文档的一致性约束：
  - 与 `AGENTS.md`、`vision.md`、`docs/roadmap-v0-to-v1.md` 保持阶段边界一致
  - 与 `WORKFLOW.md`、`docs/process/delivery-funnel.md`、`docs/process/agent-loop.md` 保持执行入口与状态真相边界一致

## 测试与验证策略

- 单元测试：
  - 运行治理测试套件，确认未破坏现有 guard / workflow 约束
- 集成/契约测试：
  - 运行 `open_pr --dry-run`、`pr_scope_guard`、`governance_gate` 验证当前 Work Item 的受控入口链路
- 手动验证：
  - 核对 GitHub `#54 / #55 / #56` 与仓内 `FR-0003 / GOV-0027 / v0.2.0 / 2026-S15` 的映射关系

## TDD 范围

- 先写测试的模块：
  - 与 legacy `TODO.md` 生命周期相关的 governance guard / policy 回归场景
- 暂不纳入 TDD 的模块与理由：
  - 纯文档口径收敛部分不新增独立运行时入口，以现有治理门禁作为回归证据

## 并行 / 串行关系

- 可并行项：
  - formal spec 套件编写
  - 顶层治理文档口径收敛
  - release / sprint 索引与 decision / exec-plan 补齐
- 串行依赖项：
  - `GOV-0027` 开 PR 前，必须先完成 formal spec、exec-plan 与索引落盘
  - merge 前，必须完成所有 governance guard、review、guardian 与 checks
- 阻塞项：
  - 若 `release` / `sprint` 索引缺失或 active `exec-plan` 不合法，受控入口会直接拒绝

## 进入实现前条件

- [x] `spec review` 已通过
- [x] 关键风险已记录并有缓解策略
- [x] 关键依赖可用

## spec review 结论

- 结论：通过
- 未决问题：无
- implementation-ready 判定：已满足；`FR-0003` 的 formal spec 允许由 `GOV-0027` 作为首个 Work Item 进入治理 PR 收口
