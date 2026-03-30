# 治理栈 v1 执行计划

## 事项上下文

- Issue：`#6`
- item_key：`FR-0001-governance-stack-v1`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 当前关联 PR：`#15`

## 目标

- 建立 Syvert 的治理文档分层结构
- 建立本地 hook 与 CI 双门禁
- 建立受控 PR / merge 入口与 guardian merge gate
- 建立最小 GitHub 项目管理自动化

## 范围

- 本次纳入：治理文档、hook、CI、PR/merge 工具、治理测试、GitHub 仓库配置
- 本次不纳入：业务实现代码、平台适配器能力、常态化定时 review 轮询

## 风险与约束

- 这是治理基线自举项，正式规约机制与治理工具在同一轮建立
- 不能放宽业务实现区与正式规约区的边界
- merge gate 只能信任本地受控 guardian verdict，不信任可伪造的远端 review payload

## 交付物

- `AGENTS.md` / `docs/AGENTS.md` / `docs/process/delivery-funnel.md`
- `code_review.md` / `spec_review.md`
- `.githooks/**` / `.github/workflows/**`
- `scripts/**`
- `tests/governance/**`

## 验证

- 治理测试套件通过
- `docs-guard`、`spec-guard`、`governance-gate` 通过
- GitHub required checks 全绿
- guardian 对当前 PR 给出最新有效 verdict

## 当前停点

- PR2 结构层文档与模板已落地，正在补齐 active governance 工件的事项上下文与 review-ready 信息。

## 下一步

- 清理 guardian 指出的阻断项并重跑审查
- 在 checks 全绿且 latest guardian=`APPROVE` 后走 `merge_pr`

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 治理基线补齐结构层索引与模板入口，使 `release / sprint / item_key` 能在仓内形成稳定聚合关系。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：治理结构层 PR2 的收口项，为后续 PR3 自动化门禁提供稳定的文档输入。
- 阻塞：等待 guardian 基于当前 PR head 重新给出 `APPROVE`。

## 已验证项

- `workflow-guard` 通过
- `docs-guard` 通过
- `spec-guard --all` 通过
- PR #15 的 GitHub checks 已能稳定触发并转绿

## 未决风险

- `docs/sprints/` 仍需严格保持为索引入口，不能演化成仓内状态镜像
- 后续 PR3 引入自动化门禁时，需要明确历史事项的兼容策略

## 当前 head SHA

- 当前 PR HEAD（进入 review 前同步）：`HEAD`
