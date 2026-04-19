# ADR-GOV-0033 Close out v0.3.0 phase and publish anchors in a single governed round

## 关联信息

- Issue：`#159`
- item_key：`GOV-0033-v0-3-0-phase-and-release-closeout`
- item_type：`GOV`
- release：`v0.3.0`
- sprint：`2026-S16`

## 背景

`v0.3.0` 的功能、formal spec、implementation 与 parent closeout 已经全部合入主干，`#127/#128` 及其下属 Work Item 也都已关闭。

但当前仓内与 GitHub 仍停留在“版本 closeout 已完成、发布锚点尚未建立”的中间态：

- `#126` Phase 仍未关闭，正文与 Project 状态仍停留在开始前口径
- `docs/releases/v0.3.0.md` 与 `docs/sprints/2026-S16.md` 仍保留 closeout 过渡叙述
- 仓库还没有 `v0.3.0` tag，也没有 GitHub Release `v0.3.0`

如果继续把这些动作分散处理，会再次制造“主干真相已完成，但 Phase / 发布锚点仍滞后”的分叉。

## 决策

- 使用单一治理 Work Item `#159 / GOV-0033-v0-3-0-phase-and-release-closeout` 承接 `v0.3.0` 的最后一段 phase / release 收口。
- 当前回合只允许修改 release / sprint 索引与本事项 decision / exec-plan，不重新打开 `FR-0008`、`FR-0009` 或任何 runtime / formal spec 语义。
- 受控 docs PR 合入后，立即在主干上创建 `v0.3.0` tag 与 GitHub Release，并把 `#126` / `#159` 的正文、Project 状态与关闭语义对齐。
- 发布锚点必须后置于 closeout PR 合入，避免 tag 或 GitHub Release 指向非主干事实。

## 影响

- `v0.3.0` 将从“功能与 closeout 已完成”推进到“Phase、索引、tag 与 GitHub Release 全部一致”的正式发布态。
- `#126` 不再继续停留在 `OPEN` / `Todo` 的滞后状态。
- `docs/releases/v0.3.0.md` 与 `docs/sprints/2026-S16.md` 会切换为完成态索引，不再误导后续执行轮次把 `v0.3.0` 视为仍在收口。
