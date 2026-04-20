# FR-0010 执行计划（requirement container）

## 关联信息

- item_key：`FR-0010-minimal-resource-lifecycle`
- Issue：`#163`
- item_type：`FR`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 spec：`docs/specs/FR-0010-minimal-resource-lifecycle/`
- 关联 PR：`#170`、`#178`
- 状态：`inactive requirement container`

## 说明

- `FR-0010` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- 当前 formal spec closeout 由 `docs/exec-plans/CHORE-0130-fr-0010-formal-spec-closeout.md` 记录 `#164` 的执行轮次，PR `#170` 已完成原始主 contract 冻结。
- `FR-0010` 冻结资源生命周期主 contract：资源类型、bundle/lease carrier、状态迁移、`acquire / release` 语义，以及 host-side durable snapshot / bootstrap / revision / 默认本地入口 traceability。
- `seed_resources(records)` 作为 internal bootstrap surface，不得新建或漂移成无 active lease 可解释的 `IN_USE` truth；但对已经被 active lease 唯一解释的既有 `IN_USE` 资源，仍允许 same-value replay / no-op。
- task-bound tracing / audit contract 留给 `FR-0011`，Adapter 注入边界留给 `FR-0012`；相邻事项不得反向改写本 FR 的主 contract。
- 后续实现 Work Item 必须消费本 formal spec，而不是在实现 PR 中重开状态名、slot 命名或 lease 语义。
- `FR-0010` 的原始 formal spec closeout checkpoint 为 `c6b76888bda690a5d3a781723af647174a77659a`；`#177` / PR `#178` 作为 traceability follow-up，继续把 snapshot / bootstrap / revision / 默认本地入口语义补回 formal suite，并由 `docs/exec-plans/CHORE-0134-fr-0010-store-bootstrap-formal-contract-traceability.md` 承担当前收口链路。
- 因此，`FR-0010` requirement container 的最新 canonical traceability baseline 不再只锚定 `#170`，而是以“`#170` 完成主 contract 冻结，`#178` 完成 store / bootstrap traceability 收口”的组合作为当前 formal suite 真相；后续实现 Work Item 应直接引用这一组基线，而不是回退到只看原始 closeout checkpoint。

## 最近一次 checkpoint 对应的 head SHA

- `4c8c9e3f1efe78771ebdb792a91ff17996ea7dc3`
