# CHORE-0039-platform-facts-xhs-douyin-detail 执行计划

## 关联信息

- item_key：`CHORE-0039-platform-facts-xhs-douyin-detail`
- Issue：`#39`
- item_type：`CHORE`
- release：`v0.1.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0002-content-detail-runtime-v0-1/`
- active 收口事项：`CHORE-0039-platform-facts-xhs-douyin-detail`
- 关联 PR：`#46`

## 目标

- 为 `v0.1.0` 的参考适配器实现沉淀可直接消费的平台知识包，把小红书 / 抖音 `content_detail_by_url` 的采集路径、运行前置、raw 来源、normalized 候选字段和失败语义落入版本控制。

## 范围

- 本次纳入：
  - `docs/research/platforms/xhs-content-detail.md`
  - `docs/research/platforms/douyin-content-detail.md`
  - `docs/research/platforms/content-detail-adapter-inputs.md`
  - `docs/specs/FR-0002-content-detail-runtime-v0-1/research.md`
  - `docs/releases/v0.1.0.md`
  - `docs/sprints/2026-S15.md`
- 本次不纳入：
  - 适配器实现代码
  - `FR-0002` formal contract 语义变更
  - 评论 / 搜索 / 创作者等非 detail 能力

## 当前停点

- `FR-0002` 已达到 `implementation-ready`，但现有 `research.md` 仍偏结论级摘要，尚不足以直接支撑小红书 / 抖音参考适配器实现。
- Issue `#39` 已在分支 `issue-39-platform-facts-xhs-douyin-detail-constraints-and-capability-mapping` 上提升为当前 docs-only 执行回合。
- 最近一次研究 checkpoint 已推进到 `2320622c816b5f89ab1ba6c9baf18fd5eac9ca8f`，已完成平台研究文档落盘、`FR-0002/research.md` 摘要化，以及 release / sprint 聚合入口更新。
- 当前受审 head 由 PR `#46` 的 `headRefOid` 绑定；本文件同时作为该 PR 的 active 审查追溯入口。

## 下一步动作

- 根据 guardian 结论补齐审查输入与 contract 对齐修复。
- 在最新受审 head 上重新执行 guardian。
- guardian 结论满足 merge gate 后通过受控 `merge_pr` 合入。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 的双参考适配器实现补齐“平台事实与适配器输入”层证据，减少后续适配器回合对参考仓源码的重复侦察。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0002` implementation 的 supporting docs 研究事项。
- 阻塞：
  - 无当前流程阻塞；若研究结论要求改动 `FR-0002` contract，需切回 formal spec 链路。

## 已验证项

- `gh issue view 39 --json number,title,body,labels,state,url`
- 对 `/Users/claw/dev/reference/MediaCrawlerPro/Python-main` 的只读探索已确认：
  - 小红书主 detail API 为 `/api/sns/web/v1/feed`，并依赖 `x-s`、`x-t`、`x-s-common`、`X-B3-Traceid`
  - 抖音主 detail API 为 `/aweme/v1/web/aweme/detail/`，并依赖 `verifyFp`、`msToken`、`webid`、`a_bogus`
  - 结论已分别落盘到 `docs/research/platforms/xhs-content-detail.md` 与 `docs/research/platforms/douyin-content-detail.md`
- 对 `/Users/claw/dev/hotcp` 的只读探索已确认：
  - 小红书页面态可从 `window.__INITIAL_STATE__.note.noteDetailMap` 读取
  - 抖音页面态可从 `SSR_RENDER_DATA`、`RENDER_DATA`、`SIGI_STATE` 与 intercepted payload 观察
  - 结论已落盘到上述平台研究文档与 `docs/research/platforms/content-detail-adapter-inputs.md`
- 已核对 `FR-0002`、`v0.1.0` release 与 `2026-S15` sprint 的现有聚合入口，并将当前研究工件与其建立索引关系。
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/spec_guard.py --mode ci --all`
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
- `python3 scripts/open_pr.py --class spec --issue 39 --item-key CHORE-0039-platform-facts-xhs-douyin-detail --item-type CHORE --release v0.1.0 --sprint 2026-S15 --title "docs: 沉淀小红书与抖音 detail 平台知识" --dry-run`
- 上述 guards / dry-run 最近一次执行结果均为通过；PR `#46` 当前审查输入已补齐到正文与本 exec-plan。
- 当前受审 head 的 guardian 结论以 PR `#46` 与状态面 `guardian.json` 为准。

## 未决风险

- 若平台知识文档直接上升为 contract 语义，可能绕开 `FR-0002` 的 formal spec 审查边界。
- 若研究结论未明确区分“adapter 内部依赖”和“Core 统一语义”，后续实现仍可能把平台细节渗入 Core。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对研究文档、聚合入口与 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- 研究 checkpoint：`2320622c816b5f89ab1ba6c9baf18fd5eac9ca8f`
- 当前受审 head：以 PR `#46` 的最新 `headRefOid` 为准
- 前者用于恢复最近一次研究收口停点，后者用于绑定当前 guardian / merge gate 的实际受审状态。
