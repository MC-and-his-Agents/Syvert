# FR-0404 Comment collection contract

## 关联信息

- item_key：`FR-0404-comment-collection-contract`
- Issue：`#404`
- item_type：`FR`
- release：`v1.4.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#404`

## 背景与目标

- 背景：`v1.3.0` 已冻结 `content_search_by_keyword` 与 `content_list_by_creator` 的 collection result contract，但评论读取仍停留在 proposed taxonomy candidate，尚未统一表达 comment target、reply hierarchy、reply cursor、deleted/invisible visibility、raw/normalized 双轨与 comment-level collection failure boundary。
- 目标：冻结 `v1.4.0` 首个 comment collection formal spec，定义 `comment_list_by_content` 的公共 target、result envelope、page continuation、reply cursor、comment item envelope、visibility status、root/parent/target linkage、source trace 与平台中立错误分类，为后续 runtime carrier、consumer migration、evidence 与 release closeout 提供 formal spec 输入。

## 范围

- 本次纳入：
  - `comment_list_by_content` 的公共 operation contract。
  - comment target、page continuation、comment result envelope、comment item envelope、reply cursor、raw payload reference、normalized comment item、dedup key、source trace、audit fields。
  - first page、next page、empty result、target not found、reply hierarchy、deleted/invisible/unavailable comments、duplicate comment item、continuation invalidation、permission denied、rate limited、platform/provider failure、parse failure、partial result、credential invalid、verification required 的公共边界。
  - Adapter 对平台 comment identity、parent/reply identifiers、cursor fields与 visibility flags 的投影边界。
- 本次不纳入：
  - runtime carrier implementation。
  - fake/reference/raw fixture payload files。
  - creator profile shape、media download/no-download boundary。
  - batch execution、dataset sink、scheduled execution、provider selector、fallback、marketplace、上层内容库或分析产品。
  - `content_detail_by_url` stable baseline 改写。
  - `FR-0403` collection public behavior 改写。

## 需求说明

- 功能需求：
  - Core 必须能表达 `comment_list_by_content` 的 comment target 与 page continuation input，而不理解平台私有 comment page object、reply cursor object、moderation object 或 platform-private thread model。
  - comment result 必须包含 `items`、`has_more`、`next_continuation`、`result_status`、`error_classification`、`raw_payload_ref`、`source_trace` 与审计字段，并复用 `FR-0403` 的 collection envelope 基础语义。
  - 每个 comment item 必须可同时保留 raw payload reference 与 normalized comment projection；Core 只能消费 normalized envelope，不消费平台私有 raw 字段。
  - 每个 comment item 必须能表达 `visibility_status`、`root_comment_ref`、`parent_comment_ref`、`target_comment_ref` 与可选 `reply_cursor`。
  - comment contract 必须能表达 `complete`、`empty`、`partial_result` 三种结果状态。
  - top-level page continuation 与 item-level reply cursor 既可以来自 opaque cursor，也可以来自 page/offset/thread-session 等平台私有组合，但 Core 只接收平台中立 token carrier。
- 契约需求：
  - `comment_list_by_content` 投影到 `comment_collection + content + single + paginated`。
  - comment result envelope 复用 `FR-0403` 的 `result_status` 与 `error_classification` vocabulary；deleted/invisible/unavailable 作为 item-level visibility 状态，而不是新的 collection-level error classification。
  - `visibility_status` 至少支持：`visible`、`deleted`、`invisible`、`unavailable`。
  - collection-level错误分类必须至少覆盖：`empty_result`、`target_not_found`、`rate_limited`、`permission_denied`、`platform_failed`、`provider_or_network_blocked`、`cursor_invalid_or_expired`、`parse_failed`、`partial_result`、`credential_invalid`、`verification_required`、`signature_or_request_invalid`。
  - `credential_invalid` 与 `verification_required` 必须保持 fail-closed，并与 `v1.2.0` resource governance 边界一致，不得被降级成普通 `platform_failed`。
  - `reply_cursor` 只能恢复同一 comment item 的 replies；跨 comment 复用必须视为 invalid/expired。
  - `content_detail_by_url` baseline 与 `FR-0403` collection public behavior 不得因 comment contract 引入新的 Core 分支或平台私有字段。
- 非功能需求：
  - comment contract 必须 fail-closed；无法证明 hierarchy、continuation、reply cursor、visibility 或 raw/normalized 投影合法时，不得返回伪稳定结果。
  - malformed comment response 不得引入新的未定义公共错误分类；本 FR 中此类 fail-closed 路径统一收敛到已定义的 `parse_failed`。
  - repository 与 GitHub truth 不得记录外部样本项目名或本地路径；所有 evidence source 只能使用脱敏 alias。
  - synthetic fixture 只能从 recorded raw shape family 派生，不得凭空发明平台字段。

## 约束

- 阶段约束：
  - `v1.4.0` 当前只绑定 `#404` 的 comment-collection slice，不绑定整个 Phase 3。
  - 本 Work Item 只交付 Batch 0 inventory 与 Batch 1 formal spec；runtime、consumer migration、evidence、release closeout 必须另建 Work Item。
- 架构约束：
  - Core 只理解 public operation、comment target、page continuation、reply cursor、result envelope、visibility status、dedup key、source trace 与 error classification。
  - Adapter 负责平台 comment identifiers、parent/reply semantics、platform cursor shape、platform visibility shape 与 normalized comment projection。
  - Provider 负责实际 HTTP、浏览器、签名或第三方执行路径，不定义 Syvert 的 comment vocabulary。
  - raw payload 只能作为审计/调试引用存在，不能成为 Core public decision fields。

## GWT 验收场景

### 场景 1：评论第一页返回完整 collection result

Given `comment_list_by_content` 使用合法 content target，且 Adapter 可以从 reference platform A 投影 recorded first-page comment response
When Core 执行 comment collection request
Then result 返回 `items`、`has_more=true`、`next_continuation`、`result_status=complete`、`raw_payload_ref` 与 normalized comment list，且不暴露平台私有 thread 或 moderation object

### 场景 2：下一页 continuation 保持公共语义稳定

Given `comment_list_by_content` 已返回第一页并生成 `next_continuation`
When Core 使用该 continuation 请求下一页，且平台实际需要 page/offset/thread-session 组合
Then Adapter 负责还原平台 continuation，Core 仍只接收平台中立 continuation token，且 comment item envelope 与错误边界保持不变

### 场景 3：reply cursor 只恢复同一 comment 的 replies

Given 某个 top-level comment item 返回 `reply_cursor`
When Core 继续拉取该 comment 的 replies
Then Adapter 只允许在同一 comment 上恢复 nested reply window，且 `reply_cursor.resume_comment_ref` 与当前 comment public ref 保持一致

### 场景 4：空评论结果不会伪装成错误

Given `comment_list_by_content` 命中合法 content target，但当前无评论
When Core 执行 comment collection request
Then result 返回 `items=[]`、`result_status=empty`、`error_classification=empty_result`，且不得被分类为 `target_not_found` 或 `platform_failed`

### 场景 5：目标不存在必须独立分类

Given `comment_list_by_content` 使用的 content target 在平台上不存在或已不可解析
When Core 执行 comment collection request
Then result 必须返回 `error_classification=target_not_found`，且不得被降级成 `empty_result`

### 场景 6：deleted/invisible comment 作为 item-level visibility 保留

Given 一页评论中同时包含正常 comment item 与 deleted/invisible placeholder
When Core 处理该页 comment result
Then deleted/invisible item 通过 `visibility_status` 表达，且合法页面仍可返回 `result_status=complete`

### 场景 6B：unavailable comment 保留为 item-level visibility

Given 一页评论中出现 comment placeholder，当前 payload 无法提供完整 body projection，但仍保留稳定 unavailable marker 与最小 placeholder text
When Adapter 仍能证明该 comment slot 属于同一合法页面
Then item 必须返回 `visibility_status=unavailable` 与最小 normalized placeholder projection，且不得默认降级成 collection-level `parse_failed`

### 场景 7：reply hierarchy 保留 root/parent/target linkage

Given 一条 reply 同时能识别 root comment、直接 parent comment 与 target comment
When Adapter 投影 normalized comment item
Then public item 必须保留 `root_comment_ref`、`parent_comment_ref` 与 `target_comment_ref`，而不要求 Core 理解平台私有 reply object

### 场景 8：部分 comment 解析失败时返回 partial result

Given 一页 raw response 中部分 comment 可投影，部分 comment 因 shape drift 解析失败
When Core 处理该页 comment result
Then result 返回 `result_status=partial_result`，保留成功 normalized comments，并将失败归类为 `parse_failed`

### 场景 9：continuation 或 reply cursor 失效有独立错误边界

Given next-page continuation token 或 reply cursor 已失效
When Adapter 还原 continuation 并请求后续页面
Then result 必须归类为 `cursor_invalid_or_expired`，而不是 generic `platform_failed`

### 场景 10：permission denied 保持独立 collection-level 错误

Given content target 存在，但当前 viewer 或 account 不具备评论访问权限
When Core 执行 comment collection request
Then result 必须返回 `error_classification=permission_denied`，且不得伪装成 `empty_result`

### 场景 11：rate limited 保持独立 collection-level 错误

Given 平台在加载评论时触发访问频率或 anti-abuse 限流
When Core 执行 comment collection request
Then result 必须返回 `error_classification=rate_limited`，且不得与 `platform_failed` 混淆

### 场景 12：platform/provider failure 保持独立 collection-level 错误

Given 平台上游失败或 provider/network path 被阻断，且不存在更强分类
When Core 执行 comment collection request
Then result 必须分别归类为 `platform_failed` 或 `provider_or_network_blocked`

### 场景 13：整页 parse failure 不得伪装成 partial_result

Given comment response 缺少 comment identity、items family 或 continuation family，导致整页无法建立最小 public projection
When Core 处理该页 comment result
Then result 必须 fail-closed 到 `parse_failed`，而不是伪造 `partial_result` 或 `complete`

### 场景 14：resource health 与 verification 保持 fail-closed

Given comment request 依赖的 account session 已 invalid，或平台要求验证码/安全验证
When Core 处理 admission 或 Adapter 返回 verification-required signal
Then result 必须分别归类为 `credential_invalid` 或 `verification_required`，并保持 fail-closed，不得继续返回伪正常 comment items

## 异常与边界场景

- 异常场景：
  - raw response 缺少 `items` family、page continuation family、reply cursor family 或 comment identity family 时，必须按 `parse_failed` fail-closed，不得伪造 `complete`。
  - page continuation 或 reply cursor 与 target/comment 上下文不匹配时，必须返回 `cursor_invalid_or_expired`。
  - rate-limit、permission-denied、provider/network-blocked、signature/request-invalid 必须保持为独立公共错误分类。
  - raw payload present 但 normalized comment 缺少最小必需字段，且无法构造最小 placeholder projection 时，必须进入 `parse_failed` 或 `partial_result` 路径。
- 边界场景：
  - `target_not_found` 与 `empty_result` 必须区分；合法 content target 没有评论不是 not found。
  - deleted/invisible/unavailable 是 item-level visibility，不等于 collection-level failure。
  - top-level page continuation 与 reply cursor 可以拥有不同 token family，但都必须保持平台中立 carrier。
  - `comment_list_by_content` 复用 `FR-0403` 的 collection envelope、source trace、raw/normalized、result status 与 error classification 语义，但不得回写或改写 `content_search_by_keyword` / `content_list_by_creator` 的 public behavior。

## 验收标准

- [ ] formal spec 冻结 `comment_list_by_content` 的 comment collection contract。
- [ ] formal spec 冻结 comment target、page continuation、reply cursor、comment item envelope、visibility status、source trace、raw payload reference 与 result status。
- [ ] formal spec 冻结 `visible`、`deleted`、`invisible`、`unavailable` 四类 item-level visibility 语义。
- [ ] formal spec 明确 `empty_result`、`target_not_found`、`rate_limited`、`permission_denied`、`platform_failed`、`provider_or_network_blocked`、`cursor_invalid_or_expired`、`parse_failed`、`partial_result`、`credential_invalid`、`verification_required`、`signature_or_request_invalid` 的公共边界。
- [ ] formal spec 明确 synthetic fixture 只能从 recorded raw shape 派生，且所有 evidence source 只能使用脱敏 alias。
- [ ] formal spec 明确 Adapter 负责平台 comment hierarchy/cursor/visibility projection，Core 不得接收平台私有对象。
- [ ] formal spec 明确 `content_detail_by_url` baseline 与 `FR-0403` collection public behavior 不受本 FR 改写。
- [ ] 本事项不修改 runtime、tests implementation、raw fixture payload files 或 release closeout truth。

## 依赖与外部前提

- 外部依赖：
  - `v1.1.0` operation taxonomy foundation 已发布。
  - `v1.2.0` resource governance foundation 已发布。
  - `v1.3.0` read-side collection foundation 已发布。
- 上下游影响：
  - 后续 runtime carrier Work Item 必须消费本 FR，而不是重新定义 comment envelope 或 visibility 语义。
  - `#405` creator/media contract 应继续复用 `FR-0403` 的 collection-level基础边界，但不复用本 FR 的 comment hierarchy surface。
