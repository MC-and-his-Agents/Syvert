# ADR-GOV-0345 Record v0.8.0 phase closeout carrier and published-truth plan

## 关联信息

- Issue：`#345`
- item_key：`GOV-0345-v0-8-0-phase-release-closeout-record`
- item_type：`GOV`
- release：`v0.8.0`
- sprint：`2026-S21`
- Parent Phase：`#293`

## 背景

`v0.8.0` 的 GitHub 主状态已经完成：

- Phase `#293` 为 `closed completed`。
- 父 FR `#294/#295/#296/#297/#298` 均为 `closed completed`。
- 阶段 A 前主干基线为 `main == origin/main == 594231b9f18a459bc64b771c486b73808ecaf764`；阶段 A 合入后 main 会前进到新的 merge commit，并由阶段 B 回写 published truth。
- 阶段 A 前 open PR 为空；当前 PR `#346` 是本事项的阶段 A carrier。
- `#312/#322/#327` closeout worktree 已清理，分支已退役。

仓内 release / sprint 索引和父项 closeout evidence 已能覆盖开放 Adapter 接入、Provider 兼容性收敛、runtime validator / decision、SDK docs、evidence 与父项 closeout；剩余缺口是没有一个版本化 carrier 明确记录 Phase `#293` 已完成、`v0.8.0` 发布锚点仍待建立，以及 `#327` 的 post-merge REST closeout comment 记录粒度弱于 `#312/#322`。

同时，既有 `v0.6.0` / `v0.7.0` release closeout pattern 都把 annotated tag 与 GitHub Release 作为正式发布锚点。当前 `v0.8.0` 还没有 tag / GitHub Release，因此本事项需要把“closeout record 补齐”和“published truth 锚点”按阶段收成一致。

## 决策

- 使用治理 Work Item `#345 / GOV-0345-v0-8-0-phase-release-closeout-record` 承接 `v0.8.0` phase closeout carrier 与 published truth 锚点。
- 本事项不重新打开 `#293`、`#294-#298` 或 `#312/#322/#327`，也不创建新的 runtime、formal spec、provider 或 Adapter 语义。
- 本事项采用串行 closeout：
  - 阶段 A：通过 docs PR 建立仓内 carrier，包括 phase closeout exec-plan、ADR、evidence、release / sprint 索引与 `#327` post-merge closeout 记录。
  - 阶段 B：阶段 A 合入后，在阶段 A merge commit 上创建 `v0.8.0` annotated tag 和 GitHub Release。
  - 阶段 C：通过 metadata-only/docs follow-up 回写 tag / GitHub Release 的 published truth，并关闭 `#345`。
- 阶段 A 补齐三类 carrier：
  - phase closeout exec-plan：记录当前主干、GitHub issue / PR 状态、验证入口、风险与回滚。
  - phase closeout evidence artifact：保存可复验 REST / Git 查询入口和关键返回值。
  - `GOV-0345` evidence 索引：让仓内文档能直接证明最终 Phase closeout 和 `#327` post-merge closeout comment 已完成，而不改写 `#327` 历史执行计划。

## 影响

- `v0.8.0` 从“实质交付与 GitHub 主状态完成”推进到“阶段 A closeout carrier 已入库”；阶段 B / 阶段 C 再把 tag、GitHub Release、release / sprint 索引、GitHub 状态与 main truth 收成正式发布态。
- 后续 `v0.9.0` 真实 provider sample 可消费 `v0.8.0` 冻结的 compatibility decision 模型，但必须通过新的 Phase / FR / Work Item 进入。
- 本事项不声明真实 provider 产品正式支持，不引入 Core provider discovery / routing / selector / marketplace。
