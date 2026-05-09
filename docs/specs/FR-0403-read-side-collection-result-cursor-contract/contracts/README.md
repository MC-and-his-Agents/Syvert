# FR-0403 contracts

## Contract name

`ReadSideCollectionResultContract` / `v1.3.0`

## Contract purpose

本 contract 定义 `content_search_by_keyword` 与 `content_list_by_creator` 的首个公共 read-side collection result contract。它冻结 collection target、continuation、item envelope、dedup key、source trace、raw/normalized 双轨与平台中立错误分类，不新增 runtime implementation、comment hierarchy、creator profile shape 或 media download contract。

## Core ownership rules

- Core 拥有 public operation、collection target、continuation token、result envelope、dedup key、source trace 与 collection-level 错误分类。
- Core 只能消费 normalized item envelope、continuation token 与公共错误分类，不得消费平台私有 query object、item object、cursor object 或 search-session object。
- Core 必须区分 `empty_result`、`target_not_found`、`cursor_invalid_or_expired`、`rate_limited`、`permission_denied`、`platform_failed`、`parse_failed` 与 `partial_result`。
- Core 必须把 `credential_invalid` 与 `verification_required` 视为 fail-closed read-side boundary，并与 `v1.2.0` resource governance 保持一致。

## Adapter consumer rules

- Adapter 负责平台 query/sort/filter 语义、平台 continuation shape、平台 item shape 与 normalized projection。
- Adapter 可以把 page/offset/search-session 等平台 continuation 组合编码成公共 continuation token；该 token 只能由同一 Adapter family 解码。
- Adapter 必须保留 raw payload reference，但不得把 raw 平台字段提升为 Core 公共字段。
- Adapter 必须保证 dedup key 来自稳定公共语义，而不是要求 Core 理解平台私有 ID 体系。

## Provider and metadata rules

- Provider 负责 HTTP、浏览器、第三方签名或执行路径，不定义 collection vocabulary。
- Provider metadata 不得把平台 raw payload schema、query object schema、session object 或 provider routing policy 暴露给 Core。
- Provider/provider-path failure 可以被分类为 `platform_failed` 或 `provider_or_network_blocked`，但不得污染 continuation 或 normalized item contract。

## Consumer rules

- `TaskRecord` 后续只能记录 collection target、continuation token、result status、error classification、dedup key 与 source trace，不得记录平台私有 continuation 字段。
- result query consumer 后续只能消费公共 item envelope 与 normalized item，不得依赖 raw payload shape 才能完成 collection workflow。
- compatibility decision 与 future consumer migration 必须把本 contract 视为 read-side collection foundation，而不是平台字段透传协议。

## Forbidden carrier fields

以下字段或语义不得进入 Core public metadata、collection result envelope 或 consumer-visible public contract：

- 平台私有 query object / request body
- page object / cursor object / search session object
- 平台 item object name
- raw platform author/session/signature fields
- provider selector / routing / fallback / priority / ranking / marketplace
- 外部项目名、本地路径或未脱敏来源标识

## Compatibility rule

`v1.3.0` collection contract 不改写 `content_detail_by_url + url + hybrid` stable baseline，不改写 `v1.1.0` taxonomy foundation 与 `v1.2.0` resource governance health contract。comment hierarchy、creator profile、media download boundary 必须由后续 `#404/#405` formal spec 承接。
