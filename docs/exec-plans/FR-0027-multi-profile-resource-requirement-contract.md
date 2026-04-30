# FR-0027 执行计划（requirement container）

## 关联信息

- item_key：`FR-0027-multi-profile-resource-requirement-contract`
- Issue：`#294`
- item_type：`FR`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0027-multi-profile-resource-requirement-contract/`
- 关联 PR：`#304`
- 状态：`inactive requirement container`

## 说明

- `FR-0027` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- 当前 formal spec closeout 由 `docs/exec-plans/CHORE-0298-fr-0027-formal-spec-closeout.md` 承担，后续 evidence、runtime、reference adapter migration 与 parent closeout 分别由 `#300/#301/#302/#303` 的 Work Item 承担。
- `FR-0027` 负责为 `v0.8.0` 冻结 multi-profile resource requirement 的 governing truth：declaration carrier、profile carrier、matcher `one-of` 语义、`invalid_resource_requirement` / `resource_unavailable` 边界，以及 shared profile 必须回指 `FR-0015` approved evidence 的规则。
- `FR-0013` / `FR-0014` / `FR-0015` 继续保留 `v0.5.0` 单声明历史基线；自 `v0.8.0` 起，multi-profile declaration / matcher / proof binding 只以 `FR-0027` 为准。
- `FR-0027` 不新增共享能力词汇，不引入 provider capability offer / compatibility decision，也不重写 `FR-0010` / `FR-0012` 已冻结的资源生命周期与注入边界。
- 当前 formal spec closeout 已通过 PR `#304` 进入 review / guardian / merge gate；最近多轮 guardian 已继续把 profile approval proof 的 shape、adapter 覆盖、tuple 对齐、proof 词汇与 version boundary 写回 formal truth。后续若只补当前受审 PR、checks 或 checkpoint metadata，只作为 review-sync follow-up，不改写 requirement 语义。

## 最近一次 checkpoint 对应的 head SHA

- `c4cc7862e61722d113260d6b0802e8461d8a7ea6`
