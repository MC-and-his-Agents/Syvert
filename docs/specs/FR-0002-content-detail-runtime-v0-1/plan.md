# FR-0002 实施计划

## 关联信息

- item_key：`FR-0002-content-detail-runtime-v0-1`
- Issue：`#38`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S15`
- 关联 exec-plan：`docs/exec-plans/FR-0002-content-detail-runtime-v0-1.md`

## 实施目标

- 为 `v0.1.0` 交付首个业务 Core/Adapter 契约，使本地单进程 CLI 能在同一执行路径上承载小红书、抖音两个 `content_detail_by_url` 参考适配器。

## 分阶段拆分

- 阶段 1：冻结任务输入、成功/失败 envelope、`normalized` 最小字段集与 Core/Adapter 边界。
- 阶段 2：实现本地单进程 runtime、CLI 入口、最小执行引擎与 adapter contract 宿主。
- 阶段 3：接入小红书、抖音两个参考适配器，并完成双适配器共享 Core 路径验证。
- 阶段 4：补齐最小测试、手动验证与实现 PR 审查证据。

## 实现约束

- 不允许触碰的边界：
  - 不在 Core 内部硬编码平台 URL 规则、签名细节、Cookie 细节或平台失败语义
  - 不提前实现 HTTP API、后台队列、资源系统、错误模型扩展
  - 不将参考仓的一体化平台实现整体迁入 Syvert
- 与上位文档的一致性约束：
  - `vision.md` 与 `docs/roadmap-v0-to-v1.md` 中 `v0.1.0` 的范围约束必须保持不变
  - 正式规约与实现默认分 PR
  - `Issue / item_key / release / sprint` 绑定必须与 active `exec-plan` 保持一致

## 测试与验证策略

- 单元测试：
  - Core 任务输入校验
  - adapter dispatch 与 capability 校验
  - 成功/失败 envelope 组装
  - `normalized` 最小字段集校验
- 集成/契约测试：
  - CLI -> runtime -> adapter 的单进程共享执行路径
  - 小红书与抖音在同一 Core 契约下返回相同顶层 envelope 结构
  - adapter 返回缺失 `raw` 或 `normalized` 时，Core 正确拒绝成功态
- 手动验证：
  - 使用真实 detail URL 验证小红书、抖音各一条内容
  - 核对 Core 主执行路径无平台特定分支

## TDD 范围

- 先写测试的模块：
  - 任务输入模型与执行前校验
  - adapter contract dispatch
  - 成功/失败 envelope 结构
  - `normalized` 最小字段约束
- 暂不纳入 TDD 的模块与理由：
  - 依赖真实平台响应、签名与登录态的适配器端联调保留为研究驱动与手动验证优先，后续再补更强契约测试

## 并行 / 串行关系

- 可并行项：
  - 小红书/抖音平台事实研究
  - Core envelope 与字段集设计
  - runtime/CLI 骨架实现
- 串行依赖项：
  - 必须先冻结 `content_detail_by_url` 契约，再启动实现 PR
  - 必须先有 runtime 宿主，再做双参考适配器验证
- 阻塞项：
  - 无当前 spec 阶段阻塞；真实平台登录态与签名部署要求已下沉为参考适配器实现环境前提。

## 进入实现前条件

- [ ] `spec review` 已通过
- [ ] 关键风险已记录并有缓解策略
- [ ] 关键依赖可用
- [ ] 小红书与抖音 detail 能力研究结论已入库，并已收口为不阻塞 contract 的实现环境前提
- [ ] `content_detail_by_url` 的最小 contract 已冻结
