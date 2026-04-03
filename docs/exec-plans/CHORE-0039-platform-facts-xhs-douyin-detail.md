# CHORE-0039-platform-facts-xhs-douyin-detail 执行计划

## 关联信息

- item_key：`CHORE-0039-platform-facts-xhs-douyin-detail`
- Issue：`#39`
- item_type：`CHORE`
- release：`v0.1.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0002-content-detail-runtime-v0-1/`
- 关联 PR：

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
- Issue `#39` 当前仍处于 supporting backlog 状态，需要提升为当前 docs-only 执行回合。

## 下一步动作

- 创建平台研究目录与三份研究文档。
- 将 `FR-0002/research.md` 收口为摘要与索引入口。
- 更新 release / sprint 聚合入口并通过 docs-only PR 进入 review。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 的双参考适配器实现补齐“平台事实与适配器输入”层证据，减少后续适配器回合对参考仓源码的重复侦察。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0002` implementation 的 supporting docs 研究事项。
- 阻塞：
  - 无当前流程阻塞；若研究结论要求改动 `FR-0002` contract，需切回 formal spec 链路。

## 已验证项

- `gh issue view 39 --json number,title,body,labels,state,url`
- 已完成对 `/Users/claw/dev/reference/MediaCrawlerPro/Python-main` 中 xhs/douyin detail 相关模块的只读探索。
- 已完成对 `/Users/claw/dev/hotcp` 中 xhs/douyin 浏览器插件采集链路与解析模型的只读探索。
- 已核对 `FR-0002`、`v0.1.0` release 与 `2026-S15` sprint 的现有聚合入口。

## 未决风险

- 若平台知识文档直接上升为 contract 语义，可能绕开 `FR-0002` 的 formal spec 审查边界。
- 若研究结论未明确区分“adapter 内部依赖”和“Core 统一语义”，后续实现仍可能把平台细节渗入 Core。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对研究文档、聚合入口与 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `f667913173bb22057ef9a865717256f1374d8c62`
