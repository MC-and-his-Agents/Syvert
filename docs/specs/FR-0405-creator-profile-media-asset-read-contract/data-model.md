# FR-0405 数据模型

## CreatorProfileTarget

- 用途：表达 `creator_profile_by_id` 的公共 target。
- 最小字段：
  - `operation`
  - `target_type`
  - `creator_ref`
  - `target_display_hint`（可选）
  - `policy_ref`（可选）
- 约束：
  - `creator_ref` 必须能表达 creator public identifier，而不暴露平台 creator page object、user object 或 raw profile schema。
  - target 可绑定 resource profile requirement，但不得包含 credential material 或私有账号字段。

## CreatorProfileResultEnvelope

- 用途：表达 creator public profile read 的公共结果。
- 最小字段：
  - `operation`
  - `target`
  - `result_status`
  - `error_classification`
  - `profile`
  - `raw_payload_ref`
  - `source_trace`
  - `audit`
- 约束：
  - `result_status` 至少支持 `complete`、`unavailable`、`failed`。
  - 成功结果必须使用 `result_status=complete` 且 `error_classification=null`。
  - creator profile 合法错误分类子集：`target_not_found`、`profile_unavailable`、`permission_denied`、`rate_limited`、`platform_failed`、`provider_or_network_blocked`、`parse_failed`、`credential_invalid`、`verification_required`、`signature_or_request_invalid`。
  - `target_not_found`、`profile_unavailable`、`permission_denied` 必须映射为 `result_status=unavailable`。
  - `rate_limited`、`platform_failed`、`provider_or_network_blocked`、`parse_failed`、`credential_invalid`、`verification_required`、`signature_or_request_invalid` 必须映射为 `result_status=failed`。
  - creator profile result 不得返回 media-only 分类：`media_unavailable`、`unsupported_content_type`、`fetch_policy_denied`。
  - `profile` 只承载 public normalized profile；平台私有画像字段不得进入 Core public result。
  - `result_status=complete` 时 `profile` 必须是 `NormalizedCreatorProfile`。
  - `result_status=unavailable` 或 `failed` 时 `profile` 必须存在且为 `null`。
  - `raw_payload_ref` 只能引用原始载荷，不承载 raw payload 内联内容。
  - 无稳定 raw payload 时 `raw_payload_ref` 必须存在且为 `null`。

## NormalizedCreatorProfile

- 用途：表达跨平台最小稳定 public creator profile 字段集合。
- 最小字段：
  - `creator_ref`
  - `canonical_ref`
  - `display_name`
  - `avatar_ref`（可选）
  - `description`（可选）
  - `public_counts`（可选）
  - `profile_url_hint`（可选）
- 约束：
  - `creator_ref` 与 `display_name` 是最小 public profile 投影要求。
  - `creator_ref` 必须是脱敏 public creator reference，不得包含平台名、source name、raw id namespace、profile URL、账号池名或本地路径。
  - normalized profile 不得携带 source/platform identity；来源追溯只能通过脱敏 `source_trace` 表达。
  - public counters 是可选字段；缺失不会使 profile invalid。
  - 平台私有扩展只能进入 Adapter-managed extension area 或 raw payload，不进入 Core 判定字段。

## MediaAssetTarget

- 用途：表达 `media_asset_fetch_by_ref` 的公共 target。
- 最小字段：
  - `operation`
  - `target_type`
  - `media_ref`
  - `origin_ref`（可选）
  - `policy_ref`（可选）
- 约束：
  - `media_ref` 必须保留 source ref 语义，但不得把平台签名参数、session fields 或 request body 提升为 Core fields。
  - `origin_ref` 可引用关联 content/profile context，但 Core 不得要求理解平台 content object。

## MediaFetchPolicy

- 用途：表达 media fetch 的公共执行边界。
- 最小字段：
  - `fetch_mode`
  - `allowed_content_types`
  - `allow_download`
  - `max_bytes`（可选）
- 约束：
  - `fetch_mode` 至少支持 `metadata_only`、`preserve_source_ref`、`download_if_allowed`、`download_required`。
  - `allowed_content_types` 必须是非空集合，且只能包含公共 content type；本 FR 至少可表达 `image`、`video`。
  - Adapter 必须先把 raw media shape 投影到公共 content type，再应用 `allowed_content_types`。
  - raw media shape 无法投影到公共 content type 时必须返回 `unsupported_content_type`。
  - raw media shape 可投影到公共 content type 但不在 `allowed_content_types` 内时必须返回 `fetch_policy_denied`。
  - 所有成功结果必须返回可审计且脱敏的 source ref lineage；无法保留时必须返回 `fetch_policy_denied`。
  - `allow_download=false` 时不得返回 `downloaded_bytes` outcome。
  - `download_required` 在 `allow_download=false`、`max_bytes` 超限或 cost boundary 不满足时必须返回 `fetch_policy_denied`。
  - `download_if_allowed` 表示允许 Adapter/Provider 在 policy 内执行 bytes transfer，但不强制下载；未执行 bytes transfer 且可安全保留脱敏 source ref lineage 时必须降级为 `source_ref_preserved`，无法保留时必须返回 `fetch_policy_denied`。
  - `max_bytes` 或等价 policy boundary 只能用于 admission/fail-closed，不引入 billing 或 asset product semantics。

## MediaFetchPolicy Decision Matrix

| condition | required result |
| --- | --- |
| raw media shape cannot be projected to public content type | `result_status=failed`, `error_classification=unsupported_content_type` |
| projected content type is supported by contract but absent from `allowed_content_types` | `result_status=failed`, `error_classification=fetch_policy_denied` |
| `fetch_mode=metadata_only`, content type allowed, and sanitized source ref lineage can be preserved | `fetch_outcome=metadata_only` |
| `fetch_mode=metadata_only`, content type allowed, and sanitized source ref lineage cannot be preserved | `result_status=failed`, `error_classification=fetch_policy_denied` |
| `fetch_mode=preserve_source_ref` and sanitized source ref lineage can be preserved | `fetch_outcome=source_ref_preserved` |
| `fetch_mode=preserve_source_ref` and sanitized source ref lineage cannot be preserved | `result_status=failed`, `error_classification=fetch_policy_denied` |
| `fetch_mode=download_if_allowed`, `allow_download=true`, size/cost policy is satisfied, and bytes transfer is performed | `fetch_outcome=downloaded_bytes` |
| `fetch_mode=download_if_allowed`, bytes transfer is not performed or is not allowed, and source ref can be preserved | `fetch_outcome=source_ref_preserved` |
| `fetch_mode=download_if_allowed`, bytes transfer is not performed or is not allowed, and sanitized source ref lineage cannot be preserved | `result_status=failed`, `error_classification=fetch_policy_denied` |
| `fetch_mode=download_required`, `allow_download=true`, and size/cost policy is satisfied | `fetch_outcome=downloaded_bytes` |
| `fetch_mode=download_required`, download is disallowed or exceeds size/cost policy | `result_status=failed`, `error_classification=fetch_policy_denied` |

## MediaFetchResultEnvelope

- 用途：表达 media asset fetch 的公共结果。
- 最小字段：
  - `operation`
  - `target`
  - `fetch_policy`
  - `fetch_outcome`
  - `result_status`
  - `error_classification`
  - `media`
  - `raw_payload_ref`
  - `source_trace`
  - `audit`
- 约束：
  - `result_status` 至少支持 `complete`、`unavailable`、`failed`。
  - 成功结果必须使用 `result_status=complete` 且 `error_classification=null`。
  - `fetch_outcome` 是 media result envelope 顶层字段，至少支持 `metadata_only`、`source_ref_preserved`、`downloaded_bytes`。
  - `result_status=complete` 时 `fetch_outcome` 必须非空，并表达本次 media request 的实际 outcome。
  - `result_status=unavailable` 或 `failed` 时 `fetch_outcome` 必须存在且为 `null`，不得伪造成功 outcome。
  - media fetch 合法错误分类子集：`media_unavailable`、`unsupported_content_type`、`permission_denied`、`rate_limited`、`platform_failed`、`provider_or_network_blocked`、`parse_failed`、`credential_invalid`、`verification_required`、`signature_or_request_invalid`、`fetch_policy_denied`。
  - `media_unavailable`、`permission_denied` 必须映射为 `result_status=unavailable`。
  - `unsupported_content_type`、`rate_limited`、`platform_failed`、`provider_or_network_blocked`、`parse_failed`、`credential_invalid`、`verification_required`、`signature_or_request_invalid`、`fetch_policy_denied` 必须映射为 `result_status=failed`。
  - media fetch result 不得返回 creator-only 分类：`target_not_found`、`profile_unavailable`。
  - `media` 只承载 normalized media fetch result；平台私有 URL list、signature fields 或 storage implementation 不得进入 Core public result。
  - `result_status=complete` 时 `media` 必须是 `NormalizedMediaAsset`。
  - `result_status=unavailable` 或 `failed` 时 `media` 必须存在且为 `null`。
  - 无稳定 raw payload 时 `raw_payload_ref` 必须存在且为 `null`。

## NormalizedMediaAsset

- 用途：表达跨平台最小稳定 media asset fields。
- 最小字段：
  - `source_media_ref`
  - `source_ref_lineage`
  - `canonical_ref`
  - `content_type`
  - `metadata`（可选）
- 约束：
  - `content_type` 至少支持 `image`、`video`。
  - normalized media result 不得携带 source/platform identity；来源追溯只能通过脱敏 `source_trace` 表达。
  - `source_media_ref` 是成功结果必填的脱敏 opaque reference；它必须对应 preserved source ref lineage，不得伪造无法追溯的 ref。
  - `source_media_ref` 必须是脱敏 opaque reference，不得包含 signed URL、session-bearing URL、credential material、bucket URL、本地文件路径或平台私有签名参数。
  - `source_ref_lineage` 必须表达从 request `media_ref` 到 normalized `source_media_ref` / `canonical_ref` 的脱敏传承链；不得包含 raw URL、签名参数、session fields、credential material、bucket URL 或本地路径。
  - `result_status=complete` 时，`source_ref_lineage.preservation_status` 必须为 `preserved`。
  - `fetch_outcome=metadata_only` 时，`source_ref_lineage` 必须至少记录 `input_ref`、preserved `source_media_ref` 与 `canonical_ref` 的脱敏关系，不得声称 bytes 已下载。
  - `fetch_outcome=source_ref_preserved` 时，`source_ref_lineage` 必须记录 preserved source ref 与 canonical ref 的脱敏关系。
  - `fetch_outcome=downloaded_bytes` 时，`source_ref_lineage` 仍只记录 preserved/resolved source ref 与 canonical ref 的脱敏关系，不得记录 bytes retrieval handle。
  - `metadata` 只能承载 `PublicMediaMetadata`；平台 media schema、provider routing、storage handle、raw headers/body、signed URL、session 或 credential 字段不得进入 public metadata。
  - envelope `fetch_outcome=metadata_only` 或 `source_ref_preserved` 时，`metadata` 不得包含 `byte_size`、`checksum_digest`、`checksum_family`、storage handle 或任何下载证明字段。
  - envelope `fetch_outcome=downloaded_bytes` 时，`metadata` 必须至少包含 `byte_size`、`checksum_digest` 与 `checksum_family`。
  - `checksum_digest` 与 `checksum_family` 是下载事实字段，不表示 Core 拥有 storage lifecycle。

## PublicMediaMetadata

- 用途：表达 media result 中允许进入 Core public result 的受限 metadata。
- 允许字段：
  - `mime_type`（可选）
  - `width`（可选）
  - `height`（可选）
  - `duration_ms`（可选）
  - `byte_size`（仅 `fetch_outcome=downloaded_bytes` 必填）
  - `checksum_digest`（仅 `fetch_outcome=downloaded_bytes` 必填）
  - `checksum_family`（仅 `fetch_outcome=downloaded_bytes` 必填）
- 约束：
  - `metadata_only` 与 `source_ref_preserved` 不得包含 `byte_size`、`checksum_digest`、`checksum_family`、storage handle、download path 或 provider-local file reference。
  - `downloaded_bytes` 必须包含 `byte_size`、`checksum_digest` 与 `checksum_family`。
  - 任何平台私有 media schema、raw response fragment、raw header、signed URL、session-bearing URL、credential material、provider routing、fallback、selector、bucket URL 或本地路径都不得进入 `PublicMediaMetadata`。
  - Adapter-managed extension area 不属于 Core public result；Core consumer 不得依赖 extension area 判断成功、失败、下载证明或 content type。

## SourceRefLineage

- 用途：表达 media ref 的脱敏来源传承链，使 source ref preservation 可验证。
- 最小字段：
  - `input_ref`
  - `source_media_ref`
  - `resolved_ref`（可选）
  - `canonical_ref`
  - `preservation_status`
- 约束：
  - `preservation_status` 至少支持 `preserved`、`unavailable`。
  - success result 不得使用 `preservation_status=unavailable`。
  - `source_ref_preserved` success 必须使用 `preservation_status=preserved`。
  - `metadata_only` success 必须使用 `preserved`。
  - `source_media_ref` 必须与 `NormalizedMediaAsset.source_media_ref` 一致。
  - `source_ref_lineage` 不得记录 download handle、storage handle、download path、provider-local file reference 或 bytes retrieval handle。

## MediaDownloadAuditEvidence

- 用途：表达 `downloaded_bytes` 的非 consumer-facing audit evidence，供 contract test、debug 与审计使用，不属于 `NormalizedMediaAsset`，不得作为 result-query workflow 的 bytes access contract。
- 最小字段：
  - `transfer_observed`
  - `byte_size`
  - `checksum_digest`
  - `checksum_family`
- 约束：
  - `fetch_outcome=downloaded_bytes` 时，audit evidence 必须能证明 bytes transfer 已发生，但不得提供可被 consumer 当作 durable asset handle 的 storage key、bucket URL、本地路径、provider-local file path、signed URL、retrieval token 或任何下载取回入口。
  - audit evidence 不能进入 `NormalizedMediaAsset` 或 public metadata，consumer 不得依赖它完成业务 workflow。
  - `metadata_only` 与 `source_ref_preserved` 不得携带 `MediaDownloadAuditEvidence`。

## SourceTrace

- 用途：表达 profile/media result 的来源追溯信息。
- 最小字段：
  - `adapter_key`
  - `provider_path`
  - `resource_profile_ref`（可选）
  - `fetched_at`
  - `evidence_alias`
- 约束：
  - 只能记录脱敏 alias，不得记录外部项目名或本地路径。
  - `adapter_key` 必须是 Syvert 内部脱敏 adapter alias，不得等同于平台名、外部项目名、账号池名或 raw source name。
  - `provider_path` 必须是 sanitized opaque execution-path alias，不得暴露 provider routing、fallback、selector、priority、账号池、代理池、真实 URL 或本地路径。
  - `provider_or_network_blocked` 结果仍必须返回 `source_trace`，但 `provider_path` 必须使用 redacted blocked-path alias，不能泄漏尝试过的 provider route。
  - 必须足以追溯到本次 profile/media result 所属的 raw payload family。

## CreatorMediaErrorClassification

- 用途：表达 creator/media read 的公共错误分类。
- 最小分类：
  - `target_not_found`
  - `profile_unavailable`
  - `media_unavailable`
  - `unsupported_content_type`
  - `permission_denied`
  - `rate_limited`
  - `platform_failed`
  - `provider_or_network_blocked`
  - `parse_failed`
  - `credential_invalid`
  - `verification_required`
  - `signature_or_request_invalid`
  - `fetch_policy_denied`
- 约束：
  - `credential_invalid` 与 `verification_required` 必须与 `v1.2.0` resource governance 边界兼容。
  - `profile_unavailable`、`media_unavailable` 与 `unsupported_content_type` 不得被降级为 generic `platform_failed`。
  - `fetch_policy_denied` 表达 policy boundary，不表达 media storage failure。

## 生命周期

- 创建：
  - `CreatorProfileTarget` 与 `MediaAssetTarget` 由 task admission 输入创建。
  - result envelope 由 Adapter 完成 raw-to-normalized projection 后返回。
  - `MediaFetchPolicy` 由 request policy 与 runtime execution control 派生，不由 Provider 私有策略决定。
- 更新：
  - creator profile result 是单目标 read result，不支持 Core-side mutable profile lifecycle。
  - media fetch result 可以从 `metadata_only` 升级到 `downloaded_bytes`，但必须通过新 task/result 表达，不得原地篡改历史 result。
- 失效/归档：
  - unavailable profile/media 只能导向对应 error classification，不应被当作普通 platform failure。
  - raw payload refs、download refs 与 bytes storage retention 策略不在本 FR 范围内。
