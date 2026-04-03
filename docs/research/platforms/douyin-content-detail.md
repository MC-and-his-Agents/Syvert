# 抖音 `content_detail_by_url` 平台知识

## 研究边界

- 只服务 `v0.1.0` 的 `content_detail_by_url` 能力。
- 不覆盖评论抓取扩展、搜索、创作者、账号池、代理池、checkpoint 或持久化设计。
- 参考来源仅用于提炼平台事实，不用于迁移实现。

## 参考来源

- API 采集路线：`/Users/claw/dev/reference/MediaCrawlerPro/Python-main`
  - 重点文件：
    - `/Users/claw/dev/reference/MediaCrawlerPro/Python-main/media_platform/douyin/client.py`
    - `/Users/claw/dev/reference/MediaCrawlerPro/Python-main/media_platform/douyin/extractor.py`
    - `/Users/claw/dev/reference/MediaCrawlerPro/Python-main/media_platform/douyin/help.py`
- 插件 / 浏览器内路线：`/Users/claw/dev/hotcp`
  - 重点文件：
    - `/Users/claw/dev/hotcp/src/app/extension/entrypoints/injected/platforms/douyin.ts`
    - `/Users/claw/dev/hotcp/src/app/extension/entrypoints/injected/platforms/douyin_interceptor.ts`
    - `/Users/claw/dev/hotcp/src/shared/parsers/dy/parser.ts`
    - `/Users/claw/dev/hotcp/docs/research/douyin/api_inventory.md`

## 采集主路径

### MediaCrawlerPro API 路线

- 主 detail 接口为 `/aweme/v1/web/aweme/detail/`，请求依赖 `aweme_id` 而不是直接接受用户态 URL。
- detail 请求前需要准备 `verifyFp`、`msToken`、`webid`，并进一步生成 `a_bogus` 参数。
- 评论接口 `/aweme/v1/web/comment/list/` 与 `/aweme/v1/web/comment/list/reply/` 存在，但不进入本轮实现范围。

### hotcp 插件 / 浏览器内路线

- 通过注入脚本分析多种抖音页面包体与全局变量，而不是只依赖一个 detail API 路径。
- 插件会扫描 `SSR_RENDER_DATA`、`RENDER_DATA`、`SIGI_STATE` 等页面态来源，并结合网络拦截识别 `aweme_detail`、`aweme_list`、评论或包装后的单视频包体。
- 这条路线适合浏览器内观察和资产保存，但对 Syvert 的参考价值主要是“raw 来源与 richer parser 结构”，不是直接迁移插件架构。

## URL / ID 规则

- 用户态 URL 需要先解析出内部内容标识，最终 detail API 仍以 `aweme_id` 为主。
- 这意味着 `content_detail_by_url` 的“URL-first 输入”必须在 adapter 内部转成 `aweme_id` 驱动调用。
- Core 不应为抖音单独增加 URL 预解析语义；`adapter_key=douyin` 下的 URL 解析完全属于 adapter。

## 运行前置

- Cookie / 登录态：detail 能力依赖浏览器会话。
- 指纹 / token：`verifyFp`、`msToken`、`webid` 是 detail 调用前置。
- 签名：detail 请求还需要 `a_bogus`。
- 插件路线：依赖注入脚本、网络拦截、页面全局状态读取与用户真实浏览器环境。
- 上述依赖全部属于 adapter 内部实现环境，不进入 Core 契约。

## Raw payload 来源

- API detail 响应：`/aweme/v1/web/aweme/detail/` 返回的 `aweme_detail`。
- 页面态全局变量：`SSR_RENDER_DATA`、`RENDER_DATA`、`SIGI_STATE` 等。
- 插件拦截包体：网络请求捕获到的 `aweme_list`、wrapped detail、comment payload。

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

- `verifyFp`
- `msToken`
- `webid`
- `a_bogus`
- 多码率视频流与水印相关底层字段
- `music`、`keywords`、`relatedQueries`、商业化标识等 richer payload
- 各类页面态包装字段，如 `SSR_RENDER_DATA` / `SIGI_STATE`

## 失败语义

- 未登录 / Cookie 失效：接口不可访问或返回受限内容。
- 指纹参数失效：`verifyFp`、`msToken`、`webid` 准备失败。
- 签名失效：`a_bogus` 无效导致 detail 请求失败。
- 内容不存在 / 已删除 / 风险内容：`aweme_id` 存在但 detail 被平台过滤。
- URL 解析失败：用户输入 URL 无法提取内部内容标识。

## 对 Syvert 的直接设计结论

- 抖音适配器必须自己承担 URL -> `aweme_id` 的转换、指纹参数准备和签名准备。
- adapter 可以内部组合“detail API + 页面态 / 全局变量 fallback”，但 Core 不应感知这些策略分支。
- `normalized` 只能冻结双平台共有字段；抖音 richer media、音乐、关键词和商业化信息留在 `raw`。
- 与小红书相比，抖音更强地要求 adapter 内部有“URL-first 输入 -> API-ready 输入”的转换层，这一层不能被误放进 Core。
