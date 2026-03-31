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

- active 恢复入口已刷新并与当前受审 PR 的 latest head 对齐，等待 guardian 基于同一受审 head 给出最终结论。

## 下一步动作

- 基于当前受审 PR 的 latest head 重跑 guardian 审查
- 若 guardian 通过，则执行 `merge_pr` 进入受控合并

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
- active exec-plan 已刷新并与当前受审 PR 的 latest head 对齐

## 回滚方式

- 若 guardian 继续阻断或合并前发现口径回归，回滚本次结构层文档变更提交并恢复到前一稳定 checkpoint（`8c016c20c780c1cd413e882684dd113451bb3f32`）后重新审查。
- 若已合并后发现问题，按受控流程提交修复 PR，优先回退 `docs/releases/**`、`docs/sprints/**` 与本 exec-plan 的本轮改动，再补充修复说明。

## 未决风险

- `release` / `sprint` 文档仍需持续保持为索引入口，避免演化成状态面
- guardian 基础设施存在偶发 `stream disconnected` / `502` 风险

## 最近一次 checkpoint 对应的 head SHA

- `617d8cc16c0bb9a2fae9d82f8f38de87bf99088d`
