# ADR-GOV-0287 Close out v0.7.0 phase and publish anchors in a single governed round

## 关联信息

- Issue：`#287`
- item_key：`GOV-0287-v0-7-0-phase-and-release-closeout`
- item_type：`GOV`
- release：`v0.7.0`
- sprint：`2026-S20`

## 背景

`v0.7.0` 的产品 FR 与治理支撑事项已全部收口并关闭：

- `FR-0021` Adapter Provider Port 边界与 native provider 拆分：`#265`，parent closeout PR `#286`
- `FR-0022` 治理脚本 GitHub API quota 与 fallback hardening：`#274`，phase / parent closeout PR `#281`

当前剩余工作是把 release / sprint 索引、发布锚点、GitHub Release 与 Phase `#264` 状态收成一致。

## 决策

- 使用单一治理 Work Item `#287 / GOV-0287-v0-7-0-phase-and-release-closeout` 承接 `v0.7.0` 的 phase / release closeout。
- 本事项采用串行 closeout：
  - 阶段 A：通过 PR `#288` 建立仓内 carrier，包括 release / sprint 索引、本 decision 与 active exec-plan。
  - 阶段 B：阶段 A 合入后，在阶段 A merge commit 上创建 `v0.7.0` tag 和 GitHub Release，再通过 PR `#289` 回写 published truth。
  - 最终状态同步：通过 PR `#290` 对齐 release / sprint / exec-plan 对 PR `#289` 已合入的状态描述；PR `#290` 合入后再关闭 Phase `#264` 与 Work Item `#287`。
- 本事项不重新打开 `FR-0021` 或 `FR-0022` 的 formal spec、runtime 或 evidence 语义。
- 本事项不批准外部 provider 接入、不新增小红书/抖音业务能力、不引入 Core provider registry / selector / fallback priority。

## 影响

- `v0.7.0` 将从“FR-0021 parent closeout 完成”推进到“仓内 release/sprint carrier 完成”，再推进到“tag / GitHub Release published truth 已回写”，最后推进到“Phase、Work Item 与仓内最终真相一致”的正式发布态。
- tag 与 GitHub Release 后置于阶段 A PR 合入后的主干提交，避免发布锚点指向未合入或未审查的事实。
- 后续外部 provider、更多站点能力或 adapter 独立仓库工作仍必须通过独立 FR，不得反向扩大 `v0.7.0` 的批准范围。
