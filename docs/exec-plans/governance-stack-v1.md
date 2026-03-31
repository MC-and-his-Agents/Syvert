# 治理栈 v1 执行计划

## 事项上下文

- Issue：`#6`
- item_key：`FR-0001-governance-stack-v1`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 状态：`inactive for PR #15`
- 事项说明：当前结构层 active 工件为 `docs/exec-plans/GOV-0014-release-sprint-structure.md`，本事项仅作为上位前提。

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

- 治理栈 v2 repo harness 主事项已完成协议与主线实现，后续结构层落点由独立事项 `GOV-0014-release-sprint-structure` 持续推进。

## 下一步

- 继续推进 `FR-0001` 主线剩余的治理测试回归与仓库侧 dry-run 校验
- 独立结构层事项由 `docs/exec-plans/GOV-0014-release-sprint-structure.md` 维护恢复入口

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 治理基线维持 repo harness 主线闭环，不直接承担 PR2 结构层事项的收口职责。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：治理基线主事项与上位前提。
- 阻塞：剩余治理测试回归与仓库侧配置 dry-run 尚未完成。

## 已验证项

- `workflow-guard` 通过
- `docs-guard` 通过
- `spec-guard --all` 通过
- repo harness 协议与门禁入口已入库

## 未决风险

- 后续结构层与自动化门禁事项需保持与 `FR-0001` 主线的边界清晰
- 仓库侧配置 dry-run 与完整治理测试尚待回归验证

## 最近一次 checkpoint 对应的 head SHA

- `7fc5e5ada722930bf61b30b911f5bb666948fad5`
