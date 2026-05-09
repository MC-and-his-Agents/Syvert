# CHORE-0411 v1.3.0 read-side collection closeout 执行计划

## 关联信息

- item_key：`CHORE-0411-v1-3-read-side-collection-closeout`
- Issue：`#411`
- item_type：`CHORE`
- release：`v1.3.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#403`
- 关联 spec：`docs/specs/FR-0403-read-side-collection-result-cursor-contract/`
- 上游依赖：
  - `#406` / PR `#407`
  - `#408` / PR `#412`
  - `#409` / PR `#413`
  - `#410` / PR `#414`
- 关联 PR：待创建
- 状态：`active`
- active 收口事项：`CHORE-0411-v1-3-read-side-collection-closeout`

## 目标

- 对齐 `#403` / `v1.3.0` 的 release truth、sprint truth、GitHub issue state 与 deferred boundary。
- 在本 Work Item 内完成 `v1.3.0` tag / GitHub Release / published truth carrier。
- 不关闭 Phase `#381`，不推进 `#404/#405`。

## 范围

- 本次纳入：
  - `docs/releases/v1.3.0.md`
  - `docs/sprints/2026-S25.md`
  - `docs/exec-plans/artifacts/CHORE-0411-v1-3-read-side-collection-closeout-evidence.md`
  - 当前 exec-plan
- 本次不纳入：
  - 新 runtime / consumer / evidence 实现
  - `#404/#405` 执行
  - Phase `#381` closeout

## 当前停点

- `#406/#408/#409/#410` 已合入并关闭。
- `v1.3.0` annotated tag 与 GitHub Release 已创建，待回写 published truth carrier。
- 待 closeout PR、review、merge 与 issue closeout。

## 下一步动作

- 回写 release / sprint / closeout evidence truth。
- 跑 docs / workflow / version / governance gate。
- 创建并合并 closeout PR。
- 关闭 `#403` 与 `#411`。

## 当前 checkpoint 推进的 release 目标

- 将 `v1.3.0` 从 planning truth 升级为 published truth。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`#403` 首个 collection batch 的最终收口。
- 阻塞：closeout PR 合入前，`#403` 仍不得关闭。

## 已验证项

- `v1.3.0` annotated tag 已创建并推送。
- GitHub Release `v1.3.0` 已创建。

## 未决风险

- 若 closeout truth 漏写 deferred boundary，会错误暗示 Phase `#381` 已完成。
- 若 published truth carrier 漏写 tag object / target / release URL，将破坏版本管理一致性。

## 回滚方式

- 若 closeout truth 错误，使用独立修正 PR 与 GitHub issue update 修正；不回滚已合入 runtime/consumer/evidence PR。

## 最近一次 checkpoint 对应的 head SHA

- `3fbb7f862257e122bd323dd650abcf7457814a91`
