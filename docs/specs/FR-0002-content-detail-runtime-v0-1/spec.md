# FR-0002 v0.1.0 content detail runtime

## 关联信息

- item_key：`FR-0002-content-detail-runtime-v0-1`
- Issue：`#38`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S15`

## 背景与目标

- 背景：`v0.1.0` 已完成治理基线与版本主轴收口，下一阶段需要启动首个业务主事项，证明 Syvert Core 能否在统一运行时契约下承载两个真实参考适配器，而不把平台语义侵入 Core。
- 目标：冻结 `content_detail_by_url` 的最小 Core/Adapter 契约，限定本地单进程与 CLI 场景，为后续小红书、抖音双参考适配器验证提供 `implementation-ready` 的 formal spec 输入。

## 范围

- 本次纳入：
  - 本地单进程运行时
  - CLI 入口
  - 最小任务模型
  - 最小执行引擎
  - 最小适配器接口
  - `content_detail_by_url` 单一能力
  - 标准化任务输入/输出
  - `raw + normalized` 结果契约
- 本次不纳入：
  - HTTP API
  - 后台队列
  - 重试、取消、并发调度
  - 浏览器资源提供方与高级资源调度器
  - 搜索、评论、创作者等其他能力
  - `v0.2.0+` 的错误模型、注册表、假适配器与契约测试框架

## 需求说明

- 功能需求：
  - CLI 必须能够提交一个 `content_detail_by_url` 任务，并在同一进程内完成执行和结果返回。
  - Core 必须基于显式 `adapter_key` 与 `capability` 路由到适配器，不在 Core 主路径中写平台特定分支。
  - 适配器必须接收统一的任务输入对象，并返回统一的结果 envelope。
  - 成功结果必须同时包含 `raw payload` 与 `normalized result`。
  - 首批验证目标固定为小红书与抖音两个真实参考适配器。
- 契约需求：
  - 任务输入最小字段固定为：`adapter_key`、`capability`、`input.url`。
  - `capability` 在 `v0.1.0` 固定为 `content_detail_by_url`。
  - `task_id` 由 Core 在接收任务输入后、进入 adapter 执行前生成；类型固定为非空字符串，并在成功态与失败态 envelope 中始终存在。
  - 成功结果 envelope 最小字段固定为：`task_id`、`adapter_key`、`capability`、`status`、`raw`、`normalized`，其中 `status` 固定为 `success`。
  - 失败结果 envelope 最小字段固定为：`task_id`、`adapter_key`、`capability`、`status`、`error`，其中 `status` 固定为 `failed`。
  - `error` 最小字段固定为：`category`、`code`、`message`、`details`；`details` 允许为空对象，`category` 仅允许 `runtime_contract` 或 `platform`。
  - `normalized` 最小公共字段固定为：`platform`、`content_id`、`content_type`、`canonical_url`、`title`、`body_text`、`published_at`、`author`、`stats`、`media`。
  - `platform`、`content_id`、`content_type`、`canonical_url` 四个字段在成功结果中必须为非空字符串。
  - `content_type` 允许值固定为：`video`、`image_post`、`mixed_media`、`unknown`。
  - `canonical_url` 表示同一内容的稳定用户态 URL；若 adapter 无法构造去除瞬时请求参数后的稳定 URL，则回填用户提交的 `input.url`。
  - `title` 与 `body_text` 两个字段必须始终存在；若平台没有独立标题或正文，可返回空字符串，但不得缺席。
  - `published_at` 必须为 RFC 3339 UTC 时间字符串，若平台无法稳定提供发布时间则返回 `null`。
  - `author`、`stats`、`media` 三个对象在成功结果中必须始终存在，不允许缺席。
  - `author` 最小字段固定为：`author_id`、`display_name`、`avatar_url`；`author_id` 与 `display_name` 在平台可提供时应为非空字符串，否则返回 `null`；`avatar_url` 类型固定为字符串或 `null`。
  - `stats` 最小字段固定为：`like_count`、`comment_count`、`share_count`、`collect_count`；四个字段的类型固定为整数或 `null`。
  - `media` 最小字段固定为：`cover_url`、`video_url`、`image_urls`；`cover_url` 与 `video_url` 类型固定为字符串或 `null`，`image_urls` 类型固定为字符串数组，缺失时返回空数组。
  - 对于成功任务，`raw` 与 `normalized` 任一缺失都视为契约不成立。
  - 对于失败任务，Core 只承载统一失败 envelope，不解释平台内部错误语义；平台特定错误细节由 adapter 通过结构化 `error.details` 附带。
- 非功能需求：
  - Core 与 Adapter 的责任边界必须可从 formal spec 直接判定。
  - Core 主执行路径必须与平台无关，只依赖统一 adapter contract。
  - spec 必须能支撑后续实现拆分，不依赖 reviewer 脑补输入/输出和边界语义。
  - 成功态与失败态的 envelope 语义都必须可被测试与脚本直接判定。

## 约束

- 阶段约束：
  - 当前事项服务于 `v0.1.0`，只证明“同一 Core 契约可运行两个真实参考适配器”。
  - 不得为了适配具体平台提前引入 `v0.2.0+` 的系统面能力。
- 架构约束：
  - Core 负责运行时语义，Adapter 负责平台语义。
  - 平台 URL 解析、签名、Cookie/请求头、平台错误形态都属于 Adapter 责任，不得渗入 Core。
  - CLI 是当前唯一对外入口，但 CLI 与执行引擎之间必须通过统一任务对象交互。

## GWT 验收场景

### 场景 1

Given 用户通过 CLI 提交 `adapter_key=xhs`、`capability=content_detail_by_url`、`input.url=<xhs-detail-url>`  
When Core 在本地单进程执行该任务  
Then Core 通过统一 adapter contract 返回包含 `raw` 与 `normalized` 的成功结果 envelope

### 场景 2

Given 用户通过同一 CLI 提交 `adapter_key=douyin`、`capability=content_detail_by_url`、`input.url=<douyin-detail-url>`  
When Core 在不增加平台分支的前提下执行该任务  
Then 返回的顶层结果 envelope 与小红书任务保持同一结构，只允许 `raw` 与 `normalized` 内部内容不同

### 场景 3

Given 用户提交的 `adapter_key` 不存在、或 adapter 不支持 `content_detail_by_url`  
When Core 尝试创建执行任务  
Then Core 在进入平台执行前返回统一失败 envelope，并说明是运行时契约级失败而非平台级失败

## 异常与边界场景

- 异常场景：
  - adapter 无法从传入 URL 中解析出有效平台输入时，任务必须失败，且失败归因于 adapter 输入校验而非 Core 平台分发。
  - adapter 拿到原始平台响应但无法构造完整 `normalized` 时，任务必须失败，不允许以“只有 raw”的成功结果返回。
  - 平台触发验证码、未登录、签名失效、内容不存在等情况时，Core 只返回统一失败 envelope，并保留 adapter 给出的结构化错误详情。
- 边界场景：
  - `v0.1.0` 只支持一次提交一个 URL 的同步执行，不定义批量任务。
  - Core 不负责推断 URL 属于哪个平台；用户必须显式提供 `adapter_key`。
  - `normalized` 只冻结双平台共同必需的最小字段，平台特有字段保留在 `raw` 或 adapter 扩展字段中，不提升为 Core 必需契约。
  - `normalized.author`、`normalized.stats`、`normalized.media` 必须始终存在；字段值可以为空或 `null`，但对象本身不得缺席。

## 验收标准

- [ ] `content_detail_by_url` 的任务输入、执行路径与结果 envelope 已冻结为 formal contract
- [ ] `raw + normalized` 成功结果要求明确，且缺一不可
- [ ] 失败 envelope 的 `status`、`error.category` 与最小错误字段已冻结为可测试语义
- [ ] `normalized` 关键字段的取值域、空值规则与时间格式已冻结为可实现语义
- [ ] Core / Adapter 责任边界明确，不要求 Core 解析平台 URL 或处理平台签名细节
- [ ] spec 可同时支撑小红书与抖音两个参考适配器，不新增平台特定 Core 分支
- [ ] 明确不在范围内容已写清，不把 HTTP API、队列、资源系统提前混入本事项

## 依赖与外部前提

- 外部依赖：
  - GitHub Issue `#38` 作为当前事项真相源入口
  - 小红书、抖音 detail 能力的研究输入以 `research.md` 记录
- 上下游影响：
  - 后续 implementation PR 需要围绕本 spec 拆分 runtime、adapter contract 与双参考适配器验证
  - 若后续实现需要修改 `content_detail_by_url` 的正式契约语义，必须回到 spec review 链路
