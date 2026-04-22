# ADR-GOV-0034 Close out v0.4.0 phase and publish anchors in a single governed round

## 关联信息

- Issue：`#185`
- item_key：`GOV-0034-v0-4-0-phase-and-release-closeout`
- item_type：`GOV`
- release：`v0.4.0`
- sprint：`2026-S17`

## 背景

`v0.4.0` 的 formal spec、runtime、reference adapter 收口与回归修复已经全部合入主干，`#163/#165/#167` 及其下属 Work Item 也都已关闭。

但当前仓内与 GitHub 仍停留在“版本功能已经完成、正式发布锚点尚未建立”的中间态：

- 仓库尚无 `docs/releases/v0.4.0.md` 与 `docs/sprints/2026-S17.md`
- 仓库尚无 `v0.4.0` tag
- GitHub 尚无 Release `v0.4.0`
- `#185` 之外尚无专门承接 `v0.4.0` 发布锚点与最终 metadata 同步的治理入口

如果把这些动作拆散处理，会再次制造“主干 runtime 真相已完成，但 release/sprint 索引与发布锚点仍滞后”的分叉。

## 决策

- 使用单一治理 Work Item `#185 / GOV-0034-v0-4-0-phase-and-release-closeout` 承接 `v0.4.0` 的最后一段 phase / release 收口。
- 本事项采用两个串行阶段，但仍保持同一个 Work Item：
  - 阶段 A：通过受控 docs PR 收口仓内 carrier，包括 release / sprint 索引、本事项 decision 与 active exec-plan。
  - 阶段 B：在阶段 A 合入主干后，立即创建 `v0.4.0` tag 与 GitHub Release，并用第二个 metadata-only/docs PR 把 release / sprint 索引与 active exec-plan 同步到最终发布真相。
- 当前 PR 只允许修改 release / sprint 索引与本事项 decision / exec-plan，不重新打开 `FR-0010`、`FR-0011`、`FR-0012` 或任何 runtime / formal spec 语义。
- 发布锚点必须后置于阶段 A PR 合入后的主干提交，避免 tag 或 GitHub Release 指向非主干事实。

## 影响

- `v0.4.0` 将沿同一 Work Item 从“功能与 FR closeout 已完成”推进到“仓内 carrier 完成”，再推进到“tag、GitHub Release 与仓内最终真相全部一致”的正式发布态。
- 发布动作不会反向污染 `FR-0010` / `FR-0011` / `FR-0012` 的 requirement truth。
- `docs/releases/v0.4.0.md` 与 `docs/sprints/2026-S17.md` 会从缺失态进入受控索引，再在发布锚点建立后切换为完成态索引。
