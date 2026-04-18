# ADR-GOV-0032 Lock legacy metadata-only review sync marker compatibility

## 关联信息

- Issue：`#152`
- item_key：`GOV-0032-legacy-metadata-only-review-sync-marker`
- item_type：`GOV`
- release：`v0.3.0`
- sprint：`2026-S16`

## 背景

`#150` 已把 guardian 对 metadata-only closeout follow-up 的例外边界收紧为显式 contract，并新增了正向 / 反向回归。但当前实现仍保留对 legacy marker `metadata-only review sync` 的兼容支持，以避免历史 closeout `exec-plan` 在未迁移前失去追溯语义。

如果这条兼容路径只存在于实现代码，而没有独立回归，后续重构时可能在不影响新 marker 的情况下无意删除 legacy 支持，导致历史工件的 metadata-only closeout 判定回退。

## 决策

- 保留 `metadata-only review sync` 作为 legacy marker 的兼容触发词。
- 为该 legacy marker 增加专门治理回归，独立证明它仍能触发 metadata-only closeout follow-up 判定。
- 当前事项不改写 `#150` 已合入的 live head / checkpoint carrier contract，不放宽 merge gate，也不新增新的 marker。

## 影响

- legacy closeout `exec-plan` 在逐步迁移到新 marker 前，仍有明确测试保护。
- 后续若要移除 `metadata-only review sync` 兼容，必须通过新的治理事项显式完成迁移和删除，而不是在重构中静默消失。
