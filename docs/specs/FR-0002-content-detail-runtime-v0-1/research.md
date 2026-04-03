# Research

## 研究边界

- 本研究只服务 `v0.1.0` 的单一能力：`content_detail_by_url`。
- 参考来源仅用于提炼平台事实与能力映射，不作为可直接迁移实现。
- 账号池、代理池、checkpoint、平台存储、评论/搜索/创作者能力不进入本轮研究范围。

## 研究入口

- 小红书平台事实：[`docs/research/platforms/xhs-content-detail.md`](../../research/platforms/xhs-content-detail.md)
- 抖音平台事实：[`docs/research/platforms/douyin-content-detail.md`](../../research/platforms/douyin-content-detail.md)
- 跨平台对比与适配器输入：[`docs/research/platforms/content-detail-adapter-inputs.md`](../../research/platforms/content-detail-adapter-inputs.md)

## 来源约束

- 参考仓 `/Users/claw/dev/reference/MediaCrawlerPro/Python-main` 使用非商业学习许可，应作为研究输入而不是直接复用实现。
- Syvert 的正式契约必须独立定义，不从参考仓复制一体化爬虫架构。

## 跨平台共性结论

- 两个平台的详情能力都明显依赖平台特定 URL/ID 规则、签名或请求前置，因此这些逻辑必须属于 Adapter。
- 两个平台都能提炼出相同的最小公共内容结构：内容标识、类型、标题、正文、发布时间、作者、统计信息、媒体信息。
- 两个平台都存在“拿到原始响应后再做 extractor 映射”的处理链路，这与 Syvert 的 `raw + normalized` 结果契约方向一致。
- 参考仓中的账号、代理、存储与 checkpoint 是成品系统能力，不应反向塑造 `v0.1.0` Core 设计。

## 平台摘要

- 小红书：
  - 主路径可走 detail API，异常时可由 HTML `window.__INITIAL_STATE__` 回退。
  - URL 内部常包含 `note_id`、`xsec_token`、`xsec_source`，解析责任属于 adapter。
  - 签名服务与浏览器风格 headers 属于 adapter 内部运行前置。
- 抖音：
  - 主路径可走 `aweme_id` 驱动的 detail API，异常时可由页面全局状态或 intercepted payload 回退。
  - `verifyFp`、`msToken`、`webid`、`a_bogus` 都属于 adapter 内部实现环境。
  - URL-first 输入需要在 adapter 内部转成 API-ready 的 detail 调用。

## 对 FR-0002 契约的直接影响

- Core 输入不负责自动识别平台，`adapter_key` 由调用方显式提供。
- Adapter 必须承担 URL 解析、签名准备、请求头/Cookie 组织和平台错误识别。
- 成功态必须同时返回 `raw` 与 `normalized`；只返回其一会破坏调试、审计与消费统一性。
- `normalized` 只定义双平台共同必需的最小字段，避免为了兼容单平台特殊形态而污染 Core。

## 明确不由本 spec 收口的问题

- 小红书与抖音真实调试所需的登录态获取流程：属于参考适配器实现环境准备，不改变本轮 Core contract。
- 签名服务的具体部署方式：属于 adapter 运行环境约束，不改变本轮输入/输出 contract。
- 评论、搜索、创作者等非 detail 能力的能力映射：明确不在 `v0.1.0` 范围内。
- `v0.2.0+` 的错误模型、假适配器与契约测试框架：后续版本事项处理，不阻塞本轮 formal spec。
