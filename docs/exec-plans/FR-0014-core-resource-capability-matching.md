# FR-0014 执行计划（requirement container）

## 关联信息

- item_key：`FR-0014-core-resource-capability-matching`
- Issue：`#190`
- item_type：`FR`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 spec：`docs/specs/FR-0014-core-resource-capability-matching/`
- 状态：`inactive requirement container`

## 说明

- `FR-0014` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- 当前 formal spec closeout 由 `docs/exec-plans/CHORE-0139-fr-0014-formal-spec-closeout.md` 承担 `#193` 的执行轮次；本 FR 自身不直接成为执行入口。
- `FR-0014` 只冻结 matcher 的输入 / 输出 / fail-closed 边界：它只判断“当前能力集合是否满足声明”，不定义 scheduler、provider selector、资源编排 DSL 或技术桥接逻辑。
- `FR-0014` 只能消费 `FR-0013` 已冻结的 `AdapterResourceRequirementDeclaration` 与 `FR-0015` 已批准的 `account / proxy` 词汇；下游实现不得通过 matcher 反向改写这些上游真相。
- `FR-0014` 不重写 `FR-0010` 的 bundle / lease / slot 语义，也不重写 `FR-0012` 的注入边界；相邻事项不得把这些语义重新塞回 matcher。
- 当前分支已形成最新 formal spec 语义 checkpoint `d5360230e4a1938be460bba2e9ae97554caf37f9`；其后若只追加当前受审 PR、checks 或 checkpoint metadata，只作为 review-sync follow-up，不改写 requirement 语义。

## 最近一次 checkpoint 对应的 head SHA

- `d5360230e4a1938be460bba2e9ae97554caf37f9`
