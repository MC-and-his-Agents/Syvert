# Research

## 研究边界

- 本研究只服务 `v0.1.0` 的单一能力：`content_detail_by_url`。
- 参考来源仅用于提炼平台事实与能力映射，不作为可直接迁移实现。
- 账号池、代理池、checkpoint、平台存储、评论/搜索/创作者能力不进入本轮研究范围。

## 来源约束

- 参考仓 `/Users/claw/dev/reference/MediaCrawlerPro/Python-main` 使用非商业学习许可，应作为研究输入而不是直接复用实现。
- Syvert 的正式契约必须独立定义，不从参考仓复制一体化爬虫架构。

## 跨平台共性结论

- 两个平台的详情能力都明显依赖平台特定 URL/ID 规则、签名或请求前置，因此这些逻辑必须属于 Adapter。
- 两个平台都能提炼出相同的最小公共内容结构：内容标识、类型、标题、正文、发布时间、作者、统计信息、媒体信息。
- 两个平台都存在“拿到原始响应后再做 extractor 映射”的处理链路，这与 Syvert 的 `raw + normalized` 结果契约方向一致。
- 参考仓中的账号、代理、存储与 checkpoint 是成品系统能力，不应反向塑造 `v0.1.0` Core 设计。

## 小红书 detail 事实

- detail 场景依赖 detail URL，而不是仅靠裸 `note_id`；URL 里常携带 `xsec_token` 与 `xsec_source`。
- 参考实现使用 detail 请求链路获取 note 内容，并在异常场景下从 HTML `window.__INITIAL_STATE__` 回退提取。
- 小红书签名结果至少包含 `x_s`、`x_t`、`x_s_common`、`x_b3_traceid`，说明签名服务是 Adapter 侧依赖，而不是 Core 依赖。
- 小红书可从响应中提炼出 `note_id`、`type`、`title/desc`、发布时间、作者、统计、图片/视频 URL、IP 属地等字段。

## 抖音 detail 事实

- 参考实现的 detail 流程偏 `aweme_id` 驱动，说明 Syvert 需要自行定义“URL-first 输入如何转为 adapter 内部 detail 调用”的规则。
- 抖音 detail 请求存在 `ms_token`、`webid`、`verify_fp`、`a_bogus` 等前置，属于 Adapter 内部的 URL 解析与签名准备责任。
- 抖音 extractor 可提炼出 `aweme_id`、`aweme_type`、`title/desc`、发布时间、作者、统计、封面/视频地址等字段。
- 抖音的内容类型、媒体地址与用户标识字段命名与小红书明显不同，因此 `normalized` 只能冻结最小公共字段，平台特有字段保留在 `raw`。

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
