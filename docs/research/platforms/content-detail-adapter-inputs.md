# `content_detail_by_url` 适配器输入与平台对比

## 适用范围

- 本文只服务 `v0.1.0` 的小红书 / 抖音参考适配器实现。
- 目标是把平台事实压缩成适配器实现输入，而不是定义新的 formal contract。

## 共性与差异矩阵

| 维度 | 小红书 | 抖音 | 对 Syvert 的含义 |
| --- | --- | --- | --- |
| 用户输入 | 用户态详情 URL | 用户态详情 URL | Core 最小任务输入固定为 `adapter_key`、`capability`、`input.url` |
| adapter 内部主 ID | `note_id` | `aweme_id` | URL 解析必须属于 adapter |
| 主采集路径 | detail API `/api/sns/web/v1/feed` | detail API `/aweme/v1/web/aweme/detail/` | 两者都可走 API，但前置完全平台化 |
| fallback | HTML / `window.__INITIAL_STATE__` | SSR / `RENDER_DATA` / `SIGI_STATE` / intercepted payload | fallback 只能在 adapter 内部切换 |
| 关键前置 | Cookie、headers、`xsec_token`、签名字段 | Cookie、`verifyFp`、`msToken`、`webid`、`a_bogus` | 这些都不是 Core 字段 |
| raw 来源 | API 响应、HTML 状态、插件截获响应 | API 响应、全局变量、插件截获响应 | `raw` 允许保留平台真实结构 |
| normalized 候选 | 内容主信息、作者、统计、图片/视频 | 内容主信息、作者、统计、图片/视频 | 只冻结共同字段 |
| 主要失败形态 | 登录态失效、验证码、签名失效、URL 解析失败 | 登录态失效、指纹/签名失效、内容过滤、URL 解析失败 | 失败 envelope 统一，细节在 `error.details` |

## 推荐 adapter 主路径与 fallback

### 小红书

- 推荐主路径：`URL -> note_id/xsec -> detail API -> extractor -> raw + normalized`
- 推荐 fallback：`URL -> note_id/xsec -> HTML/INITIAL_STATE -> extractor -> raw + normalized`
- 不推荐把 `xsec_token` 暴露为 Core 必填输入；它应由 adapter 从 URL 内部解析。

### 抖音

- 推荐主路径：`URL -> aweme_id -> verify params + a_bogus -> detail API -> extractor -> raw + normalized`
- 推荐 fallback：`URL -> aweme_id -> page globals / intercepted payload -> parser -> raw + normalized`
- 不推荐让 Core 参与 `aweme_id` 推导或 `verifyFp/msToken/webid/a_bogus` 准备。

## `raw` / `normalized` 切分原则

- `normalized` 只保留 `FR-0002` 已冻结的最小字段：
  - `platform`
  - `content_id`
  - `content_type`
  - `canonical_url`
  - `title`
  - `body_text`
  - `published_at`
  - `author.author_id`
  - `author.display_name`
  - `author.avatar_url`
  - `stats.like_count`
  - `stats.comment_count`
  - `stats.share_count`
  - `stats.collect_count`
  - `media.cover_url`
  - `media.video_url`
  - `media.image_urls`
- `raw` 保留平台原始结构和调试需要的信息：
  - rich media 底层流信息
  - 页面全局状态包装结构
  - 平台特有业务字段
- `xsec_token`、`verifyFp`、`msToken`、`webid`、`a_bogus` 这类 URL 派生值或请求前置参数属于 adapter 内部上下文，不应为了调试便利被强行塞入 `raw` 结果契约。
- 若 adapter 只能得到 `raw` 而无法构造完整 `normalized`，任务必须失败，不应返回成功态。

## 适配器实现前置清单

- 小红书：
  - URL 解析器，能提取 `note_id`、`xsec_token`、`xsec_source`
  - API 采集所需的 Cookie / headers / 签名环境
  - HTML / `__INITIAL_STATE__` fallback 能力
- 抖音：
  - URL 解析器，能把用户态 URL 转成 `aweme_id`
  - `verifyFp`、`msToken`、`webid` 的准备逻辑
  - `a_bogus` 生成能力
  - 页面态 / intercepted payload fallback 能力

## 不进入 `v0.1.0` 的事项

- 评论 / 搜索 / 创作者能力扩展
- 账号池、代理池、checkpoint、平台存储
- 契约测试框架与假适配器
- HTTP API、资源系统、后台队列、重试 / 取消控制
- 将插件架构或参考仓的一体化爬虫架构迁入 Syvert Core
