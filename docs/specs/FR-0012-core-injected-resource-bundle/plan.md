# FR-0012 实施计划

## 关联信息

- item_key：`FR-0012-core-injected-resource-bundle`
- Issue：`#167`
- item_type：`FR`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 exec-plan：
  - `docs/exec-plans/FR-0012-core-injected-resource-bundle.md`
  - `docs/exec-plans/CHORE-0132-fr-0012-formal-spec-closeout.md`

## 实施目标

- 在进入实现前冻结 Core 注入资源包与 Adapter 资源边界，使后续 reference adapter 改造、平台泄漏检查与最小资源闭环都消费同一执行 contract。

## 分阶段拆分

- 阶段 1：`#168` 收口 formal spec，明确注入 carrier、禁止性边界与资源处置提示语义。
- 阶段 2：后续实现 Work Item 基于该 spec 改造 Core 调用边界与 reference adapter 的执行接入方式。
- 阶段 3：平台泄漏检查与回归测试消费本 formal spec 的禁止性约束。

## 实现约束

- 不允许触碰的边界：
  - 不得重新定义 `FR-0010` 的 bundle/lease/status 主 contract
  - 不得把 tracing / usage log schema 吞入本事项
  - 不得提前定义资源需求声明、能力匹配或 provider 选择策略
- 与上位文档的一致性约束：
  - 与 `docs/roadmap-v0-to-v1.md` 对 `v0.4.0` 的目标保持一致
  - 与 `AGENTS.md` 对“Core 负责运行时语义，Adapter 负责平台语义”的规则保持一致
  - 与 `FR-0010` 的 bundle 词汇和 release 语义保持一致

## 测试与验证策略

- formal spec 阶段：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
- implementation 阶段：
  - Core 调用边界测试：验证缺 bundle 时不会调用 Adapter
  - Adapter boundary 测试：验证 Adapter 只能消费注入 bundle，不能自行拉取执行资源
  - 资源处置提示测试：验证 Adapter 只能返回 hint，最终 release 仍由 Core 执行
- 手动验证：
  - 逐条核对 `FR-0012` 与 `FR-0010 / FR-0011` 的交界，确保没有重写生命周期主 contract 或 tracing schema

## TDD 范围

- 先写测试的模块：
  - Core 调用前的 resource_bundle 完整性校验
  - Adapter 禁止自行来源化资源的 boundary 回归
  - 资源处置 hint 到 Core release 的责任划分
- 暂不纳入 TDD 的模块与理由：
  - reference adapter 的具体平台实现细节与 release/sprint closeout 索引不属于本 formal spec 阶段

## 并行 / 串行关系

- 可并行项：
  - `#168` 可与 `#164`、`#166` 的 formal spec closeout 并行推进，因为主要写集分离
- 串行依赖项：
  - `FR-0012` 必须消费 `FR-0010` 已冻结的 bundle/lease carrier 与 release 语义
  - reference adapter 改造必须在本 formal spec 通过后再进入实现 PR
- 阻塞项：
  - 若 Core / Adapter 资源边界没有冻结，reference adapter 会继续长出私有资源来源路径并污染 Core 主路径

## 进入实现前条件

- [ ] `FR-0012` formal spec 已通过 spec review
- [ ] `resource_bundle` 注入 carrier 已冻结
- [ ] Adapter 可做 / 不可做的资源边界已冻结
- [ ] 资源处置 hint 与 Core 最终 release 的责任分工已冻结

## spec review 结论

- 结论目标：把“Core 注入资源包、Adapter 不自行来源化资源”的 GitHub 意图推进到 implementation-ready 的执行边界 contract。
- 审查关注：
  - 是否清楚定义了 bundle 注入边界与缺 bundle fail-closed
  - 是否把 Adapter 的允许面与禁止面冻结清楚
  - 是否避免重写 lifecycle 主 contract 与 tracing schema
- implementation-ready 判定：formal spec 通过 spec review 且进入实现前条件满足后，后续 Core / Adapter 改造 Work Item 才可进入执行回合。
