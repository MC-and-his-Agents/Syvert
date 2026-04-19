# FR-0012 执行计划（requirement container）

## 关联信息

- item_key：`FR-0012-core-injected-resource-bundle`
- Issue：`#167`
- item_type：`FR`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 spec：`docs/specs/FR-0012-core-injected-resource-bundle/`
- 状态：`requirement container`

## 说明

- `FR-0012` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- 当前 formal spec closeout 由 `docs/exec-plans/CHORE-0132-fr-0012-formal-spec-closeout.md` 记录 `#168` 的执行轮次。
- `FR-0012` 只冻结 Core 注入 `ResourceBundle` 与 Adapter 资源边界；生命周期主 contract 继续由 `FR-0010` 持有，tracing / usage log 继续由 `FR-0011` 持有。
- 后续 reference adapter 改造必须消费本 formal spec，而不是在各自 adapter 中重新定义私有资源来源路径或影子 bundle schema。

## 最近一次 checkpoint 对应的 head SHA

- `待补充：首个 formal spec checkpoint 提交后回填`
