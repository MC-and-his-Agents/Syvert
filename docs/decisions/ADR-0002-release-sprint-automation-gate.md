# ADR-0002 release/sprint 事项上下文自动化门禁

## 背景

Issue `#16` 对应的 PR3 目标是把已落地的治理协议与结构层约束变成可自动校验的门禁，减少审查阶段对人工语义判断的依赖。

在 PR `#17` 推进过程中，guardian 多次暴露“规则未接入主门禁”“bootstrap contract 关联可被历史工件绕过”等问题，说明需要为当前事项建立独立且可追踪的治理决策工件。

## 决策

对事项 `GOV-0016-release-sprint-automation` 采用以下收口策略：

- 在治理门禁中引入 deterministic `context_guard` 规则。
- 在 `governance-gate` 中同时执行 workflow 与 context 两条校验链路。
- 对 bootstrap contract 使用 `Issue + decision + exec-plan` 的显式绑定，当前事项绑定工件为：
  - Issue：`#16`
  - decision：`docs/decisions/ADR-0002-release-sprint-automation-gate.md`
  - exec-plan：`docs/exec-plans/GOV-0016-release-sprint-automation.md`

## 约束

- 仅允许治理/流程自动化范围变更，不得混入业务实现代码。
- 当前事项必须维持与 `item_key` 一一对应的 active exec-plan。
- 合并前必须满足 guardian `APPROVE` 与 `safe_to_merge=true`。

## 影响

- 将 release/sprint/item_key 相关规则从文档约定升级为可执行门禁。
- 提高治理 PR 的可复验性和 merge gate 判定稳定性。
- 为后续 PR3 收口和 PR4 扩展自动化提供可追溯决策基线。
