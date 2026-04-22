# FR-0015 执行计划（requirement container）

## 关联信息

- item_key：`FR-0015-dual-reference-resource-capability-evidence`
- Issue：`#191`
- item_type：`FR`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 spec：`docs/specs/FR-0015-dual-reference-resource-capability-evidence/`
- 关联 PR：`#198`
- 状态：`inactive requirement container`

## 说明

- `FR-0015` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- 当前 formal spec closeout 由 `docs/exec-plans/CHORE-0140-fr-0015-formal-spec-closeout.md` 承担 `#194` 的执行轮次，当前受审 PR 为 `#198`；本 FR 自身不直接成为执行入口。
- `FR-0015` 只冻结双参考适配器资源能力证据记录 carrier、批准规则与 `v0.5.0` 最小能力词汇，不实现证据采集流水线，也不定义 matcher / scheduler / provider 生态。
- `FR-0015` 冻结的 `account`、`proxy` 词汇是 `FR-0013` 资源需求声明与 `FR-0014` 能力匹配可以消费的唯一共享资源能力标识；下游事项不得自行新增能力名或反向改写本 FR 的批准基线。
- `FR-0015` 必须复用 `FR-0010` 的 `account / proxy` 资源类型与 `FR-0012` 的 Core 注入边界；相邻事项不得把字段级材料、技术绑定或平台私有 token 反向提升为共享能力。
- 当前分支已形成最新 formal spec 语义 checkpoint `10e468f99c5ed4f7ea39a4987803df4a77e4242a`；其后若只追加当前受审 PR、checks 或 checkpoint metadata，只作为 review-sync follow-up，不改写 requirement 语义。

## 最近一次 checkpoint 对应的 head SHA

- `10e468f99c5ed4f7ea39a4987803df4a77e4242a`
