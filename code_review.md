# Syvert 实现 PR 审查标准

本文档定义实现 PR 的审查口径与合并门禁。

## 审查输入

审查时至少对齐以下输入：

- [AGENTS.md](./AGENTS.md)
- [WORKFLOW.md](./WORKFLOW.md)
- [docs/AGENTS.md](./docs/AGENTS.md)
- [docs/process/delivery-funnel.md](./docs/process/delivery-funnel.md)
- [docs/process/agent-loop.md](./docs/process/agent-loop.md)
- [docs/process/worktree-lifecycle.md](./docs/process/worktree-lifecycle.md)
- 相关 `spec` / `plan` / `TODO`（如有）
- 对治理 bootstrap 项，补充对应 Issue、`docs/decisions/**` 与 `docs/exec-plans/**`
- 对应 Issue / PR 描述与验收口径

## 审查优先级

优先检查阻断项，再看风格项。

阻断项包括：

- 与阶段边界冲突
- 与正式规约冲突
- 破坏 Core / Adapter 职责边界
- 缺少关键测试或验证证据
- 高风险链路缺少回滚策略

## 事项分级视角

- `轻量事项`：允许简化审查记录，但不能跳过门禁
- `中等事项`：必须证明范围与影响可控
- `核心事项`：必须绑定正式规约输入，且验证证据充分

## 审查结论

统一使用以下结论字段：

- `verdict`: `APPROVE` 或 `REQUEST_CHANGES`
- `safe_to_merge`: `true` 或 `false`

规则：

- 只要存在阻断项，`safe_to_merge` 必须为 `false`
- `REQUEST_CHANGES` 不得伴随 `safe_to_merge=true`

## 合并门禁

进入 `merge-ready` 前，必须同时满足：

1. 最新 guardian 结论为 `APPROVE`
2. guardian 结果 `safe_to_merge=true`
3. GitHub checks 全绿
4. PR 不是 Draft
5. 合并时 head 与审查时 head 一致
6. 必须通过受控入口 `merge_pr`

受控 merge 入口应优先消费绑定当前 `head SHA` 的最新本地 guardian verdict；只有 verdict 缺失、已过期或 `head SHA` 已变化时，才补跑新的 guardian 审查。

## 合并方式

- 默认 Squash Merge
- 禁止把裸 `gh pr merge` 当作日常流程
- 合并动作应通过统一受控入口执行

## 职责边界说明

- `hook` 负责本地早反馈，不替代 CI
- `CI` 负责自动化校验，不替代 guardian
- `guardian` 负责合并前审查门禁
