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
- 当前 formal spec closeout 由 `docs/exec-plans/CHORE-0140-fr-0015-formal-spec-closeout.md` 记录 `#194` 的执行轮次。
- `FR-0015` 只冻结双参考适配器资源能力证据记录 contract、正式研究边界与 `v0.5.0` 的有限共享资源能力词汇表，不重写 `FR-0010` / `FR-0011` / `FR-0012` 的运行时主 contract。
- `FR-0015` 在 `v0.5.0` 只批准 `managed_account` 与 `managed_proxy` 两个共享资源能力标识；任何单平台特例或技术特定候选都必须留在 `adapter_only` / `rejected` 记录中。
- 后续 `#192` / `FR-0013` 与 `#193` / `FR-0014` 必须消费本 formal spec，而不是在各自 formal spec 或实现 PR 中另建新的能力标识。
- 当前分支已形成首个 formal spec 语义 checkpoint `82250e919f0aa1316dc0c33723d75454126a3f3f`；其后若仅追加 checkpoint 同步、PR metadata 或 review-sync 追溯，只作为 metadata-only follow-up，不改写 requirement 语义。

## 最近一次 checkpoint 对应的 head SHA

- `82250e919f0aa1316dc0c33723d75454126a3f3f`
