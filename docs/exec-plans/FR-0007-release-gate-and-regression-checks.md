# FR-0007 执行计划（requirement container）

## 关联信息

- item_key：`FR-0007-release-gate-and-regression-checks`
- Issue：`#67`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0007-release-gate-and-regression-checks/`
- 状态：`inactive requirement container`

## 说明

- `FR-0007` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- `FR-0007` formal spec 已由 PR `#84` 合入主干；对应 `docs/exec-plans/CHORE-0079-fr-0007-formal-spec-closeout.md` 保留 formal spec 收口轮次的原始执行记录。
- `FR-0007` 的版本 gate 编排与统一结果模型已由 PR `#122` 完成并关闭 `#118`；对应 `docs/exec-plans/CHORE-0118-fr-0007-version-gate-orchestrator.md` 保留该实现轮次的原始执行记录。
- `FR-0007` 的双参考适配器真实回归执行器已由 PR `#124` 完成并关闭 `#119`；对应 `docs/exec-plans/CHORE-0119-fr-0007-dual-reference-adapter-regression.md` 保留该实现轮次的原始执行记录。
- `FR-0007` 的平台泄漏检查器已由 PR `#123` 完成并关闭 `#120`；对应 `docs/exec-plans/CHORE-0120-fr-0007-platform-leakage-check.md` 保留该实现轮次的原始执行记录。
- 上述子事项 exec-plan 中残留的 active / current 表述仅绑定各自已结束的历史执行轮次，不构成当前 `FR-0007` 的 active 入口，也不重新打开这些 Work Item。
- `FR-0007` 的父事项 closeout 由 `docs/exec-plans/CHORE-0121-fr-0007-parent-closeout.md` 记录 `#121` 执行回合，并负责把 `#67` 与 `#63` 的关闭语义、release / sprint 索引和 GitHub 真相收口到同一条证据链。

## 最近一次 checkpoint 对应的 head SHA

- `f9f2b564f17c3ef269eb25faecd12f1c0e18442b`
