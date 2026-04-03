# CHORE-0041-runtime-cli-skeleton 执行计划

## 关联信息

- Issue：`#41`
- item_key：`CHORE-0041-runtime-cli-skeleton`
- item_type：`CHORE`
- release：`v0.1.0`
- sprint：`2026-S15`
- active 收口事项：`CHORE-0041-runtime-cli-skeleton`

## 目标

- 为 `FR-0002` 之后的首个实现切片提供 active `exec-plan` 绑定，使 `#41` 的实现回合在 PR 审查、风险、验证与回滚语义上具备可追溯上下文。

## 范围

- 本次纳入：
  - 为 `CHORE-0041-runtime-cli-skeleton` 建立独立 active `exec-plan`
- 本次不纳入：
  - 任何实现代码
  - release / sprint 聚合索引更新
  - 真实 adapter 联调

## 当前停点

- `FR-0002` formal spec 已合入 `main`。
- `#41` 的实现工作已在独立分支推进，但当前缺少可供受控审查链路引用的 active `exec-plan`。

## 下一步动作

- 在实现分支继续推进 runtime / CLI skeleton。
- 由 guardian / merge gate 使用本文件作为当前回合的追溯入口。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 的首个实现切片补齐执行上下文追溯入口，不改变 `FR-0002` 已冻结的 contract。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`#41` 的执行回合追溯工件。
- 阻塞：
  - 无。

## 已验证项

- `gh issue view 41`
- 已核对 `docs/specs/FR-0002-content-detail-runtime-v0-1/spec.md`
- 已核对 `docs/releases/v0.1.0.md`

## 未决风险

- 若实现回合不再复用本 `item_key`，需要同步调整 active `exec-plan` 绑定。

## 回滚方式

- 如需回滚，使用独立 revert PR 删除本文件。

## 最近一次 checkpoint 对应的 head SHA

- `130d51f7f1a5a6e9e7d91bd910827851a27305ea`
