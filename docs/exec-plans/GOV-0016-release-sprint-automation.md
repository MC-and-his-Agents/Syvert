# GOV-0016 自动化门禁执行计划

## 事项上下文

- Issue：`#16`
- item_key：`GOV-0016-release-sprint-automation`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 decision：`docs/decisions/ADR-0002-release-sprint-automation-gate.md`
- 关联 PR：`#17`
- active 收口事项：`GOV-0016-release-sprint-automation`
- bootstrap contract：`当前 PR #17 的 active bootstrap contract`

## 目标

- 将 PR1/PR2 已定义的事项上下文约束收敛为 deterministic 自动化门禁。
- 降低治理审查对人工语义判断的依赖，提升 merge gate 的可判定性和可复验性。

## 范围

- 本次纳入：`context_guard` 规则实现、`governance-gate` 接入、治理测试补齐。
- 本次不纳入：业务实现代码、平台适配器能力、非治理流程重构。

## 当前停点

- PR `#17` 已完成自动化门禁脚本与测试落地，正在基于最新 head 等待 guardian 审查收口。

## 下一步动作

- 继续对 guardian 最新审查结论闭环，必要时进行最小修复并更新验证证据。
- 在 `APPROVE + safe_to_merge=true` 后执行受控合并。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 治理基线补齐“可自动检查的事项上下文门禁”能力。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：PR3 自动化层收口事项。
- 阻塞：等待 guardian 对最新受审 head 给出可合并结论。

## 已验证项

- `workflow-guard` 通过
- `docs-guard` 通过
- `spec-guard --all` 通过
- `context-guard` 通过
- `governance-gate` 通过
- `tests/governance` 通过

## 回滚方式

- 若合并前审查继续阻断，回滚本事项新增/修改的治理脚本与测试提交，恢复到上一稳定 checkpoint 后重审。
- 若合并后发现规则误伤，通过独立修复 PR 回退 `context_guard` 新增规则并补充迁移说明。

## 未决风险

- bootstrap contract 与事项绑定语义仍依赖文档字段规范，后续需继续强化自动检查粒度。
- guardian 基础设施仍存在偶发超时风险，可能影响审查闭环时效。

## 最近一次 checkpoint 对应的 head SHA

- `368227640a8865af8c97cdc4bc9ca2610f936bf8`
