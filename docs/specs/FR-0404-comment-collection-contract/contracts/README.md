# FR-0404 contracts

## Contract name

`CommentCollectionContract` / `v1.4.0`

## Contract purpose

本 contract 定义 `comment_collection` 的首个公共 comment collection contract。它冻结 comment target、page continuation、reply cursor、comment item envelope、visibility status、root/parent/target linkage、source trace、raw/normalized 双轨与平台中立错误分类，不新增 runtime implementation、creator profile shape 或 media download contract。

`comment_collection` 沿用当前 canonical taxonomy candidate 的 public operation 名称与 adapter-facing capability family。后续若要拆分为更具体的 operation 名，必须另走 taxonomy promotion / compatibility migration，不在本 Work Item 中完成。

## Core ownership rules

- Core 拥有 public operation、comment target、continuation、reply cursor、result envelope、visibility status、dedup key、source trace 与 collection-level 错误分类。
- Core 拥有请求侧 `CommentRequestCursor` 的组合/互斥规则。
- Core 拥有 result `next_continuation` 到下一次 request `CommentRequestCursor.page_continuation` 的字段映射；consumer 不得把该 carrier 重命名成平台私有 cursor。
- Core 拥有 `NormalizedCommentItem.canonical_ref` 作为唯一公共 comment ref 的规则。
- Core 继续要求 comment item 提供 `source_id`，以保持 `FR-0403` collection item identity 基线；placeholder `source_id` 必须使用 public placeholder namespace，不能伪装成平台原生 id。
- Core 只能消费 normalized comment item、continuation token、reply cursor token 与公共错误分类，不得消费平台私有 comment page object、reply object、moderation object 或 thread-session object。
- Core 必须区分继承 vocabulary 中的 `empty_result`、`target_not_found`、`rate_limited`、`permission_denied`、`platform_failed`、`provider_or_network_blocked`、`cursor_invalid_or_expired`、`parse_failed`、`partial_result`、`credential_invalid`、`verification_required` 与 `signature_or_request_invalid`。
- Core 必须把 `credential_invalid` 与 `verification_required` 视为 fail-closed comment boundary，并与 `v1.2.0` resource governance 保持一致。
- Core 必须把 collection-level failure 统一消费为 `items=[]`、`has_more=false`、无 `next_continuation` 的 fail-closed envelope；`raw_payload_ref` 与 `source_trace` 只作为审计证据载体。
- Core 必须把 `deleted`、`invisible`、`unavailable` 视为 item-level visibility，而不是 collection-level error 替代物。
- 对至少保留一个成功 normalized comment 的 partial page，Core 固定消费 `result_status=partial_result` 与 `error_classification=parse_failed` 的组合语义；`partial_result` 继续保留为继承词表的兼容 entry，但不是本 FR 允许单独 emitted 的 error classification。
- 对零成功投影的整页 parse failure，Core 消费 `result_status=complete`、`error_classification=parse_failed`、`items=[]`、`has_more=false` 且无 `next_continuation` 的 fail-closed envelope。

## Adapter consumer rules

- Adapter 负责平台 comment identifiers、parent/reply semantics、page continuation shape、reply continuation shape、visibility flags 与 normalized projection。
- Adapter 可以把 page/offset/thread-session 等平台 continuation 组合编码成公共 continuation token；该 token 只能由同一 Adapter family 解码。
- Adapter 可以把 comment-id/reply-offset/thread-session 等平台 reply-entry state 编码成公共 reply cursor；该 cursor 只用于进入某条 comment 的首个 reply window。
- 若 reply window 还有更多数据，Adapter 必须返回绑定同一 `resume_target_ref` / `resume_comment_ref` 的 `next_continuation`，而不是要求 consumer 继续复用旧的 item-level `reply_cursor`。
- Adapter 必须把 `reply_cursor.resume_comment_ref`、reply-window continuation 的 `resume_comment_ref`、`root_comment_ref`、`parent_comment_ref` 与 `target_comment_ref` 投影到对应 comment 的 `canonical_ref`；`source_ref` 只能用于追溯，不能作为这些绑定对象。
- Adapter 不得为 deleted/invisible/unavailable placeholder 伪造平台原生 `source_id`；缺少稳定平台 id 时，必须用 operation、target、visibility 与独立稳定 placeholder marker 派生可复验的 public placeholder `source_id` 与 `canonical_ref`。
- Placeholder identity 不得依赖 continuation token、window slot、`raw_payload_ref`、`source_trace`、`fetched_at` 或一次抓取内临时 ordinal；无法构造稳定 placeholder identity 时必须 fail-closed 到 `parse_failed`。
- Adapter 必须保留 raw payload reference，但不得把 raw 平台字段提升为 Core 公共字段。
- Adapter 必须保证 dedup key 来自稳定公共语义，而不是要求 Core 理解平台私有 comment ID 体系。

## Provider and metadata rules

- Provider 负责 HTTP、浏览器、第三方签名或执行路径，不定义 comment vocabulary。
- Provider metadata 不得把平台 raw payload schema、reply object schema、moderation object 或 provider routing policy 暴露给 Core。
- Provider/provider-path failure 可以被分类为 `platform_failed` 或 `provider_or_network_blocked`，但不得污染 continuation、reply cursor 或 normalized comment contract。

## Consumer rules

- `TaskRecord` 后续只能记录 content-scoped comment target、continuation、reply cursor、result status、error classification、visibility status、dedup key 与 source trace，不得记录平台私有 cursor fields。
- 请求侧如需继续 top-level page 或某条 comment 的 replies，后续只能记录 `CommentRequestCursor` 的公共 carrier，不得记录平台私有 thread-session 或 reply object。
- result query consumer 继续翻页时，必须把 result `next_continuation` 写入下一次 request 的 `page_continuation`；进入首个 reply window 时才使用 item-level `reply_cursor`。
- result query consumer 后续只能消费公共 comment item envelope 与 normalized comment item，不得依赖 raw payload shape 才能完成 comment workflow。
- compatibility decision 与 future consumer migration 必须把本 contract 视为 `FR-0403` collection foundation 之上的 comment-specialized surface，而不是平台字段透传协议。

## Forbidden carrier fields

以下字段或语义不得进入 Core public metadata、comment result envelope 或 consumer-visible public contract：

- 平台私有 comment page object / reply object / moderation object
- page object / cursor object / thread session object
- 平台 comment item object name
- raw platform author/session/signature fields
- provider selector / routing / fallback / priority / ranking / marketplace
- 外部项目名、本地路径或未脱敏来源标识

## Compatibility rule

`v1.4.0` comment contract 复用 `FR-0403` 的 collection envelope、result status、error classification、source trace 与 raw/normalized 基础边界，但不改写 `content_search_by_keyword`、`content_list_by_creator` 或 `content_detail_by_url + url + hybrid` stable baseline。creator profile、media download boundary 与 Phase `#381` closeout 必须由后续 `#405` 或单独 closeout Work Item 承接。
