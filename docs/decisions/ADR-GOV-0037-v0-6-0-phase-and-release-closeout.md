# ADR-GOV-0037 Close out v0.6.0 phase and publish anchors in a single governed round

## 关联信息

- Issue：`#236`
- item_key：`GOV-0037-v0-6-0-phase-and-release-closeout`
- item_type：`GOV`
- release：`v0.6.0`
- sprint：`2026-S19`

## 背景

`v0.6.0` 的四个 FR parent 已全部收口并关闭：

- `FR-0016` 最小执行控制：`#219`，parent closeout PR `#248`
- `FR-0017` 失败可见性与最小可观测信号：`#220`，parent closeout PR `#250`
- `FR-0018` HTTP 任务 API 与 Core 同路径服务面：`#221`，parent closeout PR `#251`
- `FR-0019` 可运维发布门禁与回归矩阵：`#222`，parent closeout PR `#253`

当前剩余工作是把 release / sprint 索引、发布锚点、GitHub Release 与 Phase `#218` 状态收成一致。

## 决策

- 使用单一治理 Work Item `#236 / GOV-0037-v0-6-0-phase-and-release-closeout` 承接 `v0.6.0` 的 phase / release closeout。
- 本事项采用两个串行阶段：
  - 阶段 A：通过 docs PR 建立仓内 carrier，包括 release / sprint 索引、本 decision 与 active exec-plan。
  - 阶段 B：阶段 A 合入后，在阶段 A merge commit 上创建 `v0.6.0` tag 和 GitHub Release，再通过 metadata-only/docs follow-up 回写 published truth，并关闭 Phase `#218` 与 Work Item `#236`。
- 本事项不重新打开 `FR-0016` 到 `FR-0019` 的 formal spec、runtime 或 evidence 语义。

## 影响

- `v0.6.0` 将从“FR parent 全部完成”推进到“仓内 release/sprint carrier 完成”，再推进到“tag、GitHub Release、Phase 与仓内最终真相一致”的正式发布态。
- tag 与 GitHub Release 后置于阶段 A PR 合入后的主干提交，避免发布锚点指向未合入或未审查的事实。
