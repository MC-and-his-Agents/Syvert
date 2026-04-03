# 小红书 `content_detail_by_url` 平台知识

## 研究边界

- 只服务 `v0.1.0` 的 `content_detail_by_url` 能力。
- 不覆盖评论抓取扩展、搜索、创作者主页、账号池、代理池、checkpoint 或存储策略。
- 参考来源仅用于提炼平台事实，不用于迁移实现。

## 参考来源

- API 采集路线：`/Users/claw/dev/reference/MediaCrawlerPro/Python-main`
  - 重点文件：
    - `/Users/claw/dev/reference/MediaCrawlerPro/Python-main/media_platform/xhs/client.py`
    - `/Users/claw/dev/reference/MediaCrawlerPro/Python-main/media_platform/xhs/extractor.py`
    - `/Users/claw/dev/reference/MediaCrawlerPro/Python-main/media_platform/xhs/handlers/detail_handler.py`
- 插件 / 浏览器内路线：`/Users/claw/dev/hotcp`
  - 重点文件：
    - `/Users/claw/dev/hotcp/src/app/extension/entrypoints/injected/platforms/xhs.ts`
    - `/Users/claw/dev/hotcp/src/app/extension/entrypoints/injected/platforms/xhs_interceptor.ts`
    - `/Users/claw/dev/hotcp/src/shared/parsers/xhs/parser.ts`
    - `/Users/claw/dev/hotcp/docs/research/xhs/data_source.md`

## 采集主路径

### MediaCrawlerPro API 路线

- 主 detail 接口为 `/api/sns/web/v1/feed`，请求体核心字段是 `source_note_id`，并可附带 `xsec_token` 与 `xsec_source`。
- 评论接口存在 `/api/sns/web/v2/comment/page` 与子评论分页接口，但不进入本轮实现范围。
- API 请求前需要浏览器风格请求头和签名结果，签名字段至少包括 `x-s`、`x-t`、`x-s-common`、`X-B3-Traceid`。
- detail handler 先从用户态 URL 解析 `note_id`、`xsec_token`、`xsec_source`，再进入 detail 请求链路。

### HTML / 页面状态兜底

- 当 API 路线出现验证或不稳定时，MediaCrawlerPro 会回退到详情页 HTML，并从 `window.__INITIAL_STATE__` 中提取 note 数据。
- `hotcp` 研究与实现都表明，详情页与 SPA 路由切换后的数据会落在 `window.__INITIAL_STATE__.note.noteDetailMap[noteId].note`，这是插件侧最稳的页面态来源。

### hotcp 插件 / 浏览器内路线

- 通过注入脚本和网络拦截器监听小红书页面请求与响应，同时读取 `window.__INITIAL_STATE__` 作为首选或 fallback 数据源。
- 这条路线复用了用户真实浏览器上下文，因此不需要在 Syvert Core 中显式建模签名服务或页面全局状态。

## URL / ID 规则

- 用户态详情 URL 典型形态是 `https://www.xiaohongshu.com/explore/<note_id>?xsec_token=...&xsec_source=...`。
- adapter 内部必须从用户提交的 URL 中解析：
  - `note_id`
  - `xsec_token`
  - `xsec_source`
- `xsec_token` 并非所有请求都必需，但它与风控、详情访问和评论请求链路强相关，因此必须由 adapter 负责解析与使用，而不是提升到 Core 输入字段。

## 运行前置

- Cookie / 登录态：detail 能力需要有效浏览器会话。
- 请求头 / UA：API 路线需要浏览器风格 headers。
- 签名依赖：API 路线需要签名服务提供 `x-s`、`x-t`、`x-s-common`、`X-B3-Traceid`。
- 插件路线：依赖浏览器注入、页面脚本读取权限和网络拦截能力。
- 上述依赖都属于 adapter 内部实现前提，不属于 Core 统一运行时语义。

## Raw payload 来源

- API detail 响应：`/api/sns/web/v1/feed` 返回的 note detail 包体。
- HTML / SSR 页面状态：`window.__INITIAL_STATE__` 中的 note detail map。
- 插件拦截包体：浏览器内拦截到的 detail / comment 相关响应。

## Normalized 候选字段

建议进入 Syvert `normalized` 的最小公共字段：

- `content_id`
- `content_type`
- `title`
- `desc`
- `canonical_url`
- `author.id`
- `author.name`
- `published_at`
- `stats.likes`
- `stats.comments`
- `stats.collects`
- `stats.shares`
- `media.images`
- `media.video`

建议只保留在 `raw` 的平台特有字段：

- `xsec_token`
- `xsec_source`
- 小红书特有的图片 `infoList` / `stream` 结构
- live photo / video multi-stream 的底层格式字段
- 页面态特有包装结构，如 `noteDetailMap`

## 失败语义

- 未登录 / Cookie 失效：无法访问详情或请求被重定向。
- 验证码 / 风控：API 路线尤其容易受 `xsec_token` 与滑块校验影响。
- 签名失效：签名服务不可用或生成字段无效时，请求失败。
- 内容不存在 / 已删除：`note_id` 可解析，但 detail 无法返回内容。
- URL 解析失败：用户输入 URL 无法提取 `note_id`。

## 对 Syvert 的直接设计结论

- 小红书的 URL 解析、`xsec_token` 处理、签名准备、headers/Cookie 组织必须留在 adapter。
- adapter 可以把“API 请求失败后读取 HTML `__INITIAL_STATE__`”作为内部 fallback，但 fallback 选择权不应泄漏到 Core。
- Core 只消费统一的 `raw + normalized` 结果，不关心数据来自 API 响应还是页面状态。
- `normalized` 只冻结双平台共同字段；小红书 richer media 信息保留在 `raw` 或 adapter 自定义扩展中。
