# ADR-0001 治理栈首轮落地的 bootstrap contract

## 背景

Syvert 当前在 `main` 上尚未具备正式的治理栈、`docs/specs/` 模板、hook、CI 门禁和 guardian merge 入口。

本轮变更的目标正是建立这些基础设施本身。若严格要求“先有正式规约机制，再通过该机制治理治理栈首轮落地”，会出现自举悖论：流程要求依赖的基础设施尚未在 `main` 可用。

## 决策

对“首次建立治理/规约基础设施”的治理 bootstrap 项，允许在正式规约机制尚未进入 `main` 前，使用以下版本化工件作为 pre-implementation contract：

- GitHub Issue
- `docs/decisions/**`
- `docs/exec-plans/**`

如同一 `governance` PR 已包含对应正式规约工件，也允许一并提交，但不得混入业务实现代码。

## 约束

- 该例外仅适用于治理基线自举，不适用于普通实现事项
- PR 必须仍然经过 `code_review.md` 定义的 merge gate
- PR 必须仍然提供风险、验证、回滚和关闭语义
- 一旦治理栈进入 `main`，后续核心事项恢复正式 `spec -> spec review -> implementation PR` 常态路径

## 影响

- 为治理栈 v1 首轮落地提供自洽的前置契约
- 避免为满足形式流程而引入无法执行的拆分
- 不放宽业务实现事项的正式规约要求
