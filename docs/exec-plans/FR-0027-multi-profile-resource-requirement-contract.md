# FR-0027 执行计划（requirement container）

## 关联信息

- item_key：`FR-0027-multi-profile-resource-requirement-contract`
- Issue：`#294`
- item_type：`FR`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0027-multi-profile-resource-requirement-contract/`
- 关联 PR：`#304`、`#305`、`#306`、`#307`
- 状态：`inactive requirement container`

## 说明

- `FR-0027` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- 当前 formal spec closeout 由 `docs/exec-plans/CHORE-0298-fr-0027-formal-spec-closeout.md` 承担，后续 evidence、runtime、reference adapter migration 与 parent closeout 分别由 `#300/#301/#302/#303` 的 Work Item 承担。
- `FR-0027` 负责为 `v0.8.0` 当前双参考 slice 冻结 multi-profile resource requirement 的 governing truth：declaration carrier、profile carrier、matcher `one-of` 语义、`invalid_resource_requirement` / `resource_unavailable` 边界，以及 shared profile 必须回指 `FR-0015` approved evidence 的规则。
- `FR-0013` / `FR-0014` / `FR-0015` 继续保留 `v0.5.0` 单声明历史基线；自 `v0.8.0` 起，当前双参考 slice 的 multi-profile declaration / matcher / proof binding 只以 `FR-0027` 为准。
- `FR-0027` 不新增共享能力词汇，不引入 provider capability offer / compatibility decision，也不重写 `FR-0010` / `FR-0012` 已冻结的资源生命周期与注入边界。
- `FR-0027` 的子 Work Item 已全部合入主干：
  - `#299` / PR `#304`：formal spec closeout，merge commit `9feb47387c655e1d0b50474249fed577637654c8`
  - `#300` / PR `#305`：FR-0015 profile evidence truth，merge commit `8414b0625ec0b9c4f17be135cb47d75998765056`
  - `#301` / PR `#306`：matcher/runtime V2 contract，merge commit `431c4b0f9182f3a14d3b642a315bd266986e5923`
  - `#302` / PR `#307`：reference adapter declaration migration，merge commit `d6f1e7f08ad967b147a8e4be8a24f2e2c42432cb`
- 当前 parent closeout 由 `docs/exec-plans/CHORE-0302-fr-0027-parent-closeout.md` / `#303` 承担；本 closeout PR 合入后，GitHub FR `#294` 应写入 closeout comment 并关闭。
- `FR-0027` 已成为后续 `#296`、`#298` formal freeze / implementation rollout 的前置 truth；后续事项不得再绑定旧的单声明资源依赖模型。

## 最近一次 checkpoint 对应的 head SHA

- `c71d65e39fca547f02264522a663694164e24001`
