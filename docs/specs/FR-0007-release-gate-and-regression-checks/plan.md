# FR-0007 实施计划

## 关联信息

- item_key：`FR-0007-release-gate-and-regression-checks`
- Issue：`#67`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 exec-plan：`docs/exec-plans/CHORE-0079-fr-0007-formal-spec-closeout.md`

## 实施目标

- 为 `v0.2.0` 冻结版本级 gate requirement，确保 contract harness、双参考适配器回归与平台泄漏检查在进入实现前具有统一验收面。
- 明确 `FR-0007` 与 `FR-0006`、`FR-0004`、`FR-0005` 的职责边界与依赖关系，避免后续实现回合混淆。
- 让当前 formal spec PR 可以通过受控入口、spec review、guardian 与 merge gate，成为主干上的 requirement truth。

## 分阶段拆分

- 阶段 1：建立 `FR-0007` formal spec 套件，冻结版本 gate、双参考适配器回归与平台泄漏检查的 requirement 边界。
- 阶段 2：补齐风险说明、版本 gate 契约摘要与 `v0.2.0` / `2026-S15` 索引入口，使仓内可直接追溯 `FR-0007`。
- 阶段 3：通过 formal spec 门禁与受控 PR 入口完成独立 spec PR，并收口 guardian / merge gate / GitHub 状态。
- 阶段 4：在后续独立 Work Item 中实现 harness 消费、真实回归执行与平台泄漏检查，不在当前 PR 中落地运行时代码。

## 实现约束

- 不允许触碰的边界：
  - 当前 PR 只允许修改 `FR-0007` formal spec 套件、当前事项 exec-plan 与与其绑定的最小 release / sprint 索引
  - 不修改 `src/**`、`scripts/**`、`tests/**`
  - 不写死某个 CI 工作流、脚本参数、fixture 目录结构或 guardian 实现细节
  - 不混入 `FR-0004`、`FR-0005`、`FR-0006` 的 formal spec 本体
- 与上位文档的一致性约束：
  - 与 `vision.md`、`docs/roadmap-v0-to-v1.md` 对 `v0.2.0`“可验证 Core”目标保持一致
  - 与 `WORKFLOW.md`、`docs/AGENTS.md`、`spec_review.md` 对 formal spec / exec-plan / release-sprint index 的职责边界保持一致

## 测试与验证策略

- 单元测试：
  - 无。当前 PR 仅收敛 formal spec 与索引工件，不引入运行时代码
- 集成/契约测试：
  - `python3 scripts/spec_guard.py --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/open_pr.py --class spec --issue 79 --item-key CHORE-0079-fr-0007-formal-spec-closeout --item-type CHORE --release v0.2.0 --sprint 2026-S15 --closing fixes --dry-run`
- 手动验证：
  - 核对 `#63 -> #67` 的 GitHub 事项关系、`docs/releases/v0.2.0.md` 与 `docs/sprints/2026-S15.md` 的入口索引
  - 按 `spec_review.md` rubric 审核 requirement 是否覆盖 gate 对象、触发语义、失败语义、边界与依赖

## TDD 范围

- 先写测试的模块：
  - 无。formal spec PR 本身不引入运行时代码或测试逻辑
- 暂不纳入 TDD 的模块与理由：
  - 版本 gate 执行器、参考适配器回归 harness、平台泄漏检查器属于后续独立实现 Work Item，不在本轮 formal spec PR 中实现

## 并行 / 串行关系

- 可并行项：
  - `spec.md`、`plan.md`、`risks.md`、`contracts/README.md` 起草
  - release / sprint 索引补齐
- 串行依赖项：
  - 必须先冻结 `FR-0007` formal spec，后续 Work Item 才能实现具体 gate
  - merge 前必须完成当前 PR 的 spec review、checks、guardian 与受控 merge
- 阻塞项：
  - 若 `FR-0004`、`FR-0005`、`FR-0006` 的上游 formal spec 未完成，`FR-0007` 只能停留在 requirement 依赖声明层，不能声称 gate 已实现

## 进入实现前条件

- [x] `FR-0007` requirement 已冻结到可进入实现拆分的边界
- [x] 关键风险已记录并有缓解策略
- [x] 关键依赖可用
- [x] `FR-0007` 已明确区分版本 gate 与 harness 基座职责

## spec review 结论

- 结论：当前 PR 的目标是把 `FR-0007` 从“issue 意图”推进到可实施拆分、可追溯的 formal spec 基线。
- 未决问题：需确认平台泄漏检查边界没有越权替代实现设计，也未遗漏与 `FR-0006`、registry、错误模型的依赖语义。
- implementation-ready 判定：当前 formal spec PR 合入后，`FR-0007` requirement 本身达到 implementation-ready；后续 Work Item 在实现 gate 时必须消费当时已批准的 `FR-0004`、`FR-0005`、`FR-0006` 契约，而不得自行重写这些上游语义。
