# GOV-0014 结构层执行计划

## 事项上下文

- Issue：`#14`
- item_key：`GOV-0014-release-sprint-structure`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 PR：`#15`
- active 收口事项：`GOV-0014-release-sprint-structure`
- 上位前提事项：`FR-0001-governance-stack-v1`（非当前 PR 收口主体）

## 目标

- 为 PR2 落地 `release` / `sprint` 聚合索引与 `exec-plan` 模板入口。
- 让当前治理结构层事项具备独立的恢复入口，并明确与 `FR-0001` 的前提/收口边界。

## 范围

- 本次纳入：`docs/releases/**`、`docs/sprints/**`、`docs/exec-plans/_template.md`、相关治理说明文档
- 本次不纳入：新的自动化门禁实现、业务代码改动、仓内状态镜像

## 当前停点

- release / sprint 的模板与当前实例已入库，等待 guardian 对 PR `#15` 的最新审查结论。

## 下一步动作

- 基于最新 PR head 重跑 guardian 审查
- guardian 通过后使用 `merge_pr` 执行受控合并

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 治理基线补齐结构层聚合索引与事项级恢复入口。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：PR2 结构层收口事项
- 阻塞：等待 guardian 通过并进入 merge gate

## 与 FR-0001 的边界

- `FR-0001-governance-stack-v1` 在当前 PR 仅作为治理基线前提，不承担结构层收口责任
- PR `#15` 的审查与收口以本工件（`GOV-0014-release-sprint-structure`）为 active 恢复入口

## 已验证项

- `workflow-guard` 通过
- `docs-guard` 通过
- `spec-guard --all` 通过
- PR `#15` 的 GitHub checks 已全绿

## 未决风险

- `release` / `sprint` 文档仍需持续保持为索引入口，避免演化成状态面
- guardian 基础设施存在偶发 `stream disconnected` / `502` 风险

## 最近一次 checkpoint 对应的 head SHA

- `5416f30d8e59f9991f6c40730f829329f0cf1975`
