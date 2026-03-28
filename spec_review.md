# Syvert 正式规约审查标准

本文档定义 `docs/specs/` 正式规约套件的审查口径。

## 适用时机

- `核心事项` 默认进入正式规约审查
- `中等事项` 触及共享契约/共享数据模型/高风险链路时进入正式规约审查
- 治理 bootstrap 例外：若事项本身用于首次建立治理/规约基础设施，且正式规约机制尚未在 `main` 可用，可先以 `Issue + decision + exec-plan` 进入治理 PR；该例外不放宽业务实现事项

目标是把事项从 `spec-ready` 推进到 `implementation-ready`。

## 最小套件要求

每个 FR 目录至少包含：

- `spec.md`
- `plan.md`
- `TODO.md`

模板路径见 [docs/specs/_template](./docs/specs/_template)。

## `spec.md` 必查项

- 存在 `## GWT 验收场景`
- 存在 `## 异常与边界场景`
- 存在 `## 验收标准`
- 至少包含一组 `Given / When / Then`

## `plan.md` 必查项

必须包含以下七节：

1. `实施目标`
2. `分阶段拆分`
3. `实现约束`
4. `测试与验证策略`
5. `TDD 范围`
6. `并行 / 串行关系`
7. `进入实现前条件`

并且需要显式说明 `spec review` 通过后如何进入实现。
若事项属于 repo harness 变更，`plan.md` 需覆盖 `WORKFLOW.md`、agent loop、worktree lifecycle、状态面一致性。

## 按需文档触发条件

- `contracts/`：存在稳定接口或跨进程协议
- `data-model.md`：引入或修改持久化/共享实体
- `risks.md`：涉及安全、账号、写入、迁移、并发或不可逆动作
- `research.md`：存在关键未知项且需要研究证据

## 规约与实现分离规则

- 正式规约变更默认不与实现代码混在同一 PR
- 若实现 PR 仅回写 `TODO.md` 进度且不改变正式契约语义，可与实现同 PR
- 一旦修改正式契约语义，应回到规约审查链路
- 治理 bootstrap 例外仅允许 `governance` 类 PR 同时携带 bootstrap contract 或对应正式规约工件；不得混入业务实现代码

## 审查结论

`spec review` 的结论至少包括：

- 是否通过（通过 / 需修改）
- 未决问题与风险
- 进入实现前条件是否满足

只有审查通过且进入实现前条件满足，事项才可标记为 `implementation-ready`。
