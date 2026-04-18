# ADR-GOV-0031 Guardian live review head stays outside versioned exec-plans

## 关联信息

- Issue：`#150`
- item_key：`GOV-0031-guardian-live-head-binding`
- item_type：`GOV`
- release：`v0.3.0`
- sprint：`2026-S16`

## 背景

`#149` 的 parent closeout 审查暴露出一条治理层自引用循环：

- active `exec-plan` 被要求静态记录“当前受审 head / 门禁绑定”
- 但 closeout PR 自身又会继续修改这个版本化 `exec-plan`
- 一旦为了追平最新 head 提交 metadata-only review sync，PR head 会再次变化
- guardian 下一轮又会要求文档继续追写新的 head

结果是 closeout 回合围绕“文档是否追平最新 SHA”无限追逐，而不是继续审查 checkpoint 语义、追溯关系与 merge gate 本身。

## 决策

- 当前 live review head 的唯一真相固定为 PR `headRefOid` 与 guardian state / merge gate 的当前绑定结果，不写回 versioned `exec-plan` 作为静态真相。
- active `exec-plan` 只承载最近一次 checkpoint / resume truth；若需要描述后续 metadata-only review sync，只能作为追溯说明，而不是必须穷尽到当前 HEAD 的静态列表。
- guardian prompt 必须显式提醒 reviewer：不要要求 active `exec-plan` 追写当前 live head；若当前 diff 仅补 review / merge gate / closeout metadata，也不要把 metadata-only head 视为新的 checkpoint。
- metadata-only closeout follow-up 的审查重点固定为 checkpoint 语义、追溯关系、验证证据与门禁结果是否自洽，而不是文档中的静态 SHA 是否等于当前 HEAD。
- 当前事项不放宽 reviewer rubric、guardian verdict schema、`safe_to_merge` 语义或 merge gate 条件；只修正 live head carrier 与 checkpoint carrier 的职责边界。

## 影响

- closeout PR 不再因为追写“当前受审 head”而触发自引用的 metadata-only SHA 追逐。
- guardian 仍然绑定当前 PR live head，但这个绑定留在 PR 元数据与 guardian state，而不是留在会继续被 PR 自身改写的版本化文档里。
- 后续若需要补充 closeout 追账，只能增加追溯说明或验证记录，不能再次把 `exec-plan` 退化成 live head 状态面。
