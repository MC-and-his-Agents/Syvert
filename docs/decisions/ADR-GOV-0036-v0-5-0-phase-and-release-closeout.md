# ADR-GOV-0036 Close out v0.5.0 phase and publish anchors in a single governed round

## 关联信息

- Issue：`#215`
- item_key：`GOV-0036-v0-5-0-phase-and-release-closeout`
- item_type：`GOV`
- release：`v0.5.0`
- sprint：`2026-S18`

## 背景

`v0.5.0` 的 formal spec、runtime implementation、evidence baseline rerun 与顶层定位治理已经全部合入主干：

- `FR-0015` formal spec / follow-up / rerun implementation 已由 PR `#198/#208/#212` 合入主干
- `FR-0013` formal spec / runtime 已由 PR `#200/#213` 合入主干
- `FR-0014` formal spec / runtime 已由 PR `#199/#214` 合入主干
- `GOV-0035` 已由 PR `#207` 合入主干

但当前仓内与 GitHub 仍停留在“版本功能已经完成、正式发布锚点与 closeout 状态尚未统一”的中间态：

- 仓库尚无 `docs/releases/v0.5.0.md` 与 `docs/sprints/2026-S18.md`
- 仓库尚无 `v0.5.0` tag
- GitHub 尚无 Release `v0.5.0`
- GitHub Phase `#188` 与 FR `#189/#190/#191` 仍为 `OPEN`
- 当前尚无专门承接 `v0.5.0` phase / release 收口的合法治理 Work Item

如果把这些动作拆散处理，会再次制造“主干功能真相已完成，但 release/sprint 索引、发布锚点与 GitHub 状态仍滞后”的分叉。

## 决策

- 使用单一治理 Work Item `#215 / GOV-0036-v0-5-0-phase-and-release-closeout` 承接 `v0.5.0` 的最后一段 phase / release 收口。
- 本事项采用两个串行阶段，但仍保持同一个 Work Item：
  - 阶段 A：通过受控 docs PR 建立仓内 carrier，包括 release / sprint 索引、本事项 decision 与 active exec-plan。
  - 阶段 B：在阶段 A PR 合入主干后，立即创建 `v0.5.0` tag 与 GitHub Release，并以第二个 metadata-only/docs PR 回写 published truth、同步 active exec-plan，并完成 `#188/#189/#190/#191/#215` 的 GitHub closeout。
- 当前 PR 只允许修改 release / sprint 索引与本事项 decision / exec-plan，不重新打开 `FR-0013`、`FR-0014`、`FR-0015` 或任何 runtime / formal spec 语义。
- 发布锚点必须后置于阶段 A PR 合入后的主干提交，避免 tag 或 GitHub Release 指向非主干事实。

## 影响

- `v0.5.0` 将沿同一 Work Item 从“功能与 FR closeout 已完成”推进到“仓内 carrier 完成”，再推进到“tag、GitHub Release、Phase / FR 与仓内最终真相全部一致”的正式发布态。
- 发布动作不会反向污染 `FR-0013` / `FR-0014` / `FR-0015` 的 requirement 或 implementation truth。
- `docs/releases/v0.5.0.md` 与 `docs/sprints/2026-S18.md` 会先进入受控索引，再在发布锚点建立后切换为完成态索引。
