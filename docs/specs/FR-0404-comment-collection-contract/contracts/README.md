# FR-0404 contracts

## Contract name

`CommentCollectionContract` / `v1.4.0`

## Contract purpose

本 contract 定义 `comment_list_by_content` 的首个公共 comment collection contract。它冻结 comment target、page continuation、reply cursor、comment item envelope、visibility status、root/parent/target linkage、source trace、raw/normalized 双轨与平台中立错误分类，不新增 runtime implementation、creator profile shape 或 media download contract。

## Core ownership rules

- Core 拥有 public operation、comment target、page continuation、reply cursor、result envelope、visibility status、dedup key、source trace 与 collection-level 错误分类。
- Core 只能消费 normalized comment item、continuation token、reply cursor token 与公共错误分类，不得消费平台私有 comment page object、reply object、moderation object 或 thread-session object。
- Core 必须区分 `empty_result`、`target_not_found`、`cursor_invalid_or_expired`、`rate_limited`、`permission_denied`、`platform_failed`、`parse_failed` 与 `partial_result`。
- Core 必须把 `credential_invalid` 与 `verification_required` 视为 fail-closed comment boundary，并与 `v1.2.0` resource governance 保持一致。
- Core 必须把 `deleted`、`invisible`、`unavailable` 视为 item-level visibility，而不是 collection-level error 替代物。

## Adapter consumer rules

- Adapter 负责平台 comment identifiers、parent/reply semantics、page continuation shape、reply continuation shape、visibility flags 与 normalized projection。
- Adapter 可以把 page/offset/thread-session 等平台 continuation 组合编码成公共 continuation token；该 token 只能由同一 Adapter family 解码。
- Adapter 可以把 comment-id/reply-offset/thread-session 等平台 reply state 编码成公共 reply cursor；该 cursor 只能恢复同一 comment item 的 replies。
- Adapter 必须保留 raw payload reference，但不得把 raw 平台字段提升为 Core 公共字段。
- Adapter 必须保证 dedup key 来自稳定公共语义，而不是要求 Core 理解平台私有 comment ID 体系。

## Provider and metadata rules

- Provider 负责 HTTP、浏览器、第三方签名或执行路径，不定义 comment vocabulary。
- Provider metadata 不得把平台 raw payload schema、reply object schema、moderation object 或 provider routing policy 暴露给 Core。
- Provider/provider-path failure 可以被分类为 `platform_failed` 或 `provider_or_network_blocked`，但不得污染 continuation、reply cursor 或 normalized comment contract。

## Consumer rules

- `TaskRecord` 后续只能记录 comment target、page continuation、reply cursor、result status、error classification、visibility status、dedup key 与 source trace，不得记录平台私有 cursor fields。
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
