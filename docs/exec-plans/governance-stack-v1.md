# 治理栈 v1 执行计划

## 关联信息

- item_key：`FR-0001-governance-stack-v1`
- Issue：`#6`
- 事项类型：`FR`
- 所属 release：`v0.1.0`
- 所属 sprint：`2026-S13`
- 关联 spec：`docs/specs/FR-0001-governance-stack-v1/`
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 关联 PR：`#13`

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

- 修复 guardian 指出的信任边界与流程输入问题

## 下一步

- 补齐 Issue、formal spec 与 bootstrap contract
- 重跑 guardian 审查
- 通过 `merge_pr` 走受控合并
