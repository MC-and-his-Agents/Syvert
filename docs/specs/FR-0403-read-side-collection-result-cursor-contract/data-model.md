# FR-0403 数据模型

## CollectionTarget

- 用途：表达 `content_search_by_keyword` 与 `content_list_by_creator` 的公共 target。
- 最小字段：
  - `operation`
  - `target_type`
  - `target_ref`
  - `target_display_hint`（可选）
  - `policy_ref`（可选）
- 约束：
  - `content_search_by_keyword` 的 target 必须能表达 keyword，而不暴露平台 query object。
  - `content_list_by_creator` 的 target 必须能表达 creator public identifier，而不暴露平台 creator page object。

## CollectionContinuation

- 用途：表达公共 continuation input/output。
- 最小字段：
  - `continuation_token`
  - `continuation_family`
  - `resume_target_ref`
  - `issued_at`（可选）
- 约束：
  - 可以承载 opaque cursor，也可以承载 page/offset/search-session 等平台私有组合的 Adapter-encoded token。
  - Core 不得直接理解平台私有 continuation 字段。
  - continuation 与 target 必须绑定；跨 target 复用必须视为 invalid/expired。

## CollectionResultEnvelope

- 用途：表达 read-side collection 的公共结果。
- 最小字段：
  - `operation`
  - `target`
  - `items`
  - `has_more`
  - `next_continuation`
  - `result_status`
  - `error_classification`
  - `raw_payload_ref`
  - `source_trace`
  - `audit`
- 约束：
  - `result_status` 至少支持 `complete`、`empty`、`partial_result`。
  - `error_classification` 用于表达 collection-level failure/admission classification；成功且无错误时允许为空。
  - `empty` 不等于 `target_not_found`。
  - `has_more=false` 时允许 `next_continuation` 为空。
  - `raw_payload_ref` 只能引用原始载荷，不承载 raw payload 内联内容。

## CollectionItemEnvelope

- 用途：表达 collection 内每个 item 的公共封装。
- 最小字段：
  - `item_type`
  - `dedup_key`
  - `source_id`
  - `source_ref`
  - `normalized`
  - `raw_payload_ref`
  - `source_trace`
- 约束：
  - `dedup_key` 必须稳定，且不要求两个平台使用相同原始 ID 字段。
  - `normalized` 是 Core 可消费内容；平台私有字段不得直接进入 item envelope 顶层。
  - `raw_payload_ref` 与 `normalized` 必须并存，供审计/调试与公共消费分离。

## NormalizedCollectionItem

- 用途：表达跨平台最小稳定 item 字段集合。
- 最小字段：
  - `source_platform`
  - `source_type`
  - `source_id`
  - `canonical_ref`
  - `title_or_text_hint`
  - `creator_ref`（可选）
  - `published_at`（可选）
  - `media_refs`（可选）
- 约束：
  - 缺少可选字段不会使 item invalid。
  - 平台私有扩展只能进入 Adapter-managed extension area 或 raw payload，不进入 Core 判定字段。

## SourceTrace

- 用途：表达 item 与 collection 的来源追溯信息。
- 最小字段：
  - `adapter_key`
  - `provider_path`
  - `resource_profile_ref`（可选）
  - `fetched_at`
  - `evidence_alias`
- 约束：
  - 只能记录脱敏 alias，不得记录外部项目名或本地路径。
  - 必须足以追溯到本次 collection result 所属的 raw payload family。

## CollectionErrorClassification

- 用途：表达 collection-level 公共错误分类。
- 最小分类：
  - `empty_result`
  - `target_not_found`
  - `rate_limited`
  - `permission_denied`
  - `platform_failed`
  - `provider_or_network_blocked`
  - `cursor_invalid_or_expired`
  - `parse_failed`
  - `partial_result`
  - `credential_invalid`
  - `verification_required`
  - `signature_or_request_invalid`
- 约束：
  - `credential_invalid` 与 `verification_required` 必须与 `v1.2.0` resource governance 边界兼容。
  - `partial_result` 不是错误替代品，而是 collection result status 与 item-level failure 的组合语义。

## 生命周期

- 创建：
  - `CollectionTarget` 由 task admission 输入创建。
  - `CollectionResultEnvelope` 由 Adapter 完成 raw-to-normalized projection 后返回。
  - `CollectionContinuation` 在 `has_more=true` 时由 Adapter 生成平台中立 token。
- 更新：
  - 新页面结果使用新的 `next_continuation`；不得原地篡改历史 continuation 以伪造跨页稳定性。
  - `partial_result` 允许追加 item-level parse-failure evidence，但不得改写成功 normalized items 的公共字段。
- 失效/归档：
  - invalid/expired continuation 只能导向 `cursor_invalid_or_expired`，不应被当作普通 platform failure。
  - raw payload refs 的持久化/归档策略不在本 FR 范围内。
