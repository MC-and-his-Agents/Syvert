# FR-0004 实施计划

## 关联信息

- item_key：`FR-0004-input-target-and-collection-policy`
- Issue：`#64`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`
- 状态：`historical formal-spec planning record; formal spec merged via PR #82`
- 当前 active exec-plan：`docs/exec-plans/CHORE-0095-fr-0004-parent-closeout.md`
- formal spec 历史 exec-plan：`docs/exec-plans/CHORE-0068-fr-0004-formal-spec-closeout.md`
- implementation 聚合历史 exec-plan：`docs/exec-plans/CHORE-0068-fr-0004-implementation-closeout.md`

## 实施目标

- 为 `v0.2.0` 冻结 `InputTarget` 与 `CollectionPolicy` 的 formal spec 基线，使 Core 输入受理、adapter 支持声明、资源前置校验与后续契约测试都围绕同一套共享模型推进。
- 通过独立 spec PR 收口本 FR 的边界、验收条件、风险与进入实现前条件，不混入运行时代码或治理改造。

## 分阶段拆分

- 阶段 1：核对 `vision.md`、roadmap、release/sprint 索引、`FR-0002` 与现有 Core / Adapter 文档，冻结 FR-0004 的目标与边界。
- 阶段 2：建立 `FR-0004` formal spec 套件，定义 `InputTarget`、`CollectionPolicy`、兼容关系与非目标。
- 阶段 3：补齐最小 active `exec-plan` 与 release / sprint 索引，使当前 spec PR 可通过受控入口。
- 阶段 4：运行 formal spec 相关门禁、完成 spec review、guardian 与 merge gate，合入主干并确认 closeout 一致。

## 实现约束

- 不允许触碰的边界：
  - 不修改 `src/**`、`scripts/**`、`tests/**`
  - 不在本 PR 中创建 implementation 工件或推进实现细节
  - 不混入 `FR-0005`、`FR-0006`、`FR-0007` 的 formal spec 实质内容
  - 不把错误模型、registry、fake adapter、harness、version gate 的具体 contract 提前写进 `FR-0004`
- 与上位文档的一致性约束：
  - 与 `vision.md`、`docs/roadmap-v0-to-v1.md` 保持 `v0.2.0` 的版本目标一致
  - 与 `WORKFLOW.md`、`docs/AGENTS.md`、`docs/process/delivery-funnel.md` 保持“FR 绑定 formal spec、Work Item 进入执行回合”的流程口径一致
  - 与 `FR-0002` 保持既有 URL 输入语义兼容，不在 formal spec 层制造破坏性断裂

## 测试与验证策略

- 单元测试：
  - 无。当前 PR 不修改运行时代码或测试代码；本轮验证以 formal spec 门禁与受控入口校验为主
- 集成/契约测试：
  - 运行 `docs_guard`、`workflow_guard`、`spec_guard`、`governance_gate`，确认 formal spec 套件、引用关系与治理入口不漂移
  - 运行 `open_pr --class spec --dry-run` 与 `pr_scope_guard --class spec`，确认当前事项能通过受控 PR 入口
- 手动验证：
  - 核对 GitHub `#63 / #64 / #95` 与仓内 `FR-0004 / v0.2.0 / 2026-S15 / active exec-plan` 的映射关系，并确认 `#68` 已退化为历史 implementation closeout 记录
  - 对照 `adapter-sdk.md`、`framework-positioning.md` 与 `FR-0002`，确认 Core / Adapter 边界、兼容关系与非目标没有漂移

## TDD 范围

- 先写测试的模块：
  - 无。formal spec PR 只冻结需求与契约边界，不引入可执行实现
- 暂不纳入 TDD 的模块与理由：
  - fake adapter、adapter harness、version gate 与平台泄漏检查 gate 依赖后续 FR；当前 PR 只提供它们必须遵守的共享模型基线

## 并行 / 串行关系

- 可并行项：
  - `InputTarget` 与 `CollectionPolicy` 的语义草拟
  - release / sprint 索引与最小 exec-plan 补齐
  - formal spec review 输入准备
- 串行依赖项：
  - 必须先冻结 `FR-0004` formal spec，后续实现回合才能合法推进
  - merge 前，必须完成当前 spec PR 的 checks、guardian 与受控 merge
- 阻塞项：
  - 若 active `exec-plan` 缺失或事项上下文不一致，`open_pr` 会直接拒绝
  - 若 formal spec 越界吞并错误模型、registry、harness 或 version gate，`spec review` 应直接阻断

## 进入实现前条件

- [x] `spec review` 已通过
- [x] 关键风险已记录并有缓解策略
- [x] 关键依赖可用
- [x] `InputTarget` 与 `CollectionPolicy` 的最小语义、边界与兼容关系已冻结

## spec review 结论

- 结论：`APPROVE`。`FR-0004` formal spec 已由 PR `#82` 合入主干。
- 未决问题：无。formal spec 审查回合已完成；后续只允许在独立 implementation / closeout 回合中消费该 formal spec。
- implementation-ready 判定：`是`。`#87/#89/#88` 已按 formal spec 边界完成 implementation 回合，且 `#68` 已完成 implementation 聚合 closeout。
