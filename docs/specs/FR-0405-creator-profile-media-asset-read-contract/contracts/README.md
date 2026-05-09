# FR-0405 contracts

## Contract name

`CreatorProfileMediaAssetReadContract` / `v1.5.0`

## Contract purpose

本 contract 定义 `creator_profile_by_id` 与 `media_asset_fetch_by_ref` 的公共 read-side single-target result contract。它冻结 creator target、public profile result、media asset ref、content type、media-only fetch policy、media-only fetch outcome、source trace、raw/normalized 双轨与平台中立错误分类，不新增 runtime implementation、comment hierarchy、batch/dataset behavior 或 media storage product semantics。

## Core ownership rules

- Core 拥有 public operation、target、result envelope、source trace 与错误分类；`fetch_policy` 与 `fetch_outcome` 只属于 `media_asset_fetch_by_ref`。
- Core 只能消费 normalized public profile、normalized media result、source trace 与公共错误分类，不得消费平台私有 creator object、profile schema、media URL list、signature fields、download implementation 或 storage policy。
- Core 必须区分 `target_not_found`、`profile_unavailable`、`media_unavailable`、`unsupported_content_type`、`permission_denied`、`rate_limited`、`platform_failed`、`provider_or_network_blocked`、`parse_failed`、`signature_or_request_invalid` 与 `fetch_policy_denied`。
- Core 必须按 data model 固定 `error_classification -> result_status` 映射；success 使用 `error_classification=null`，availability/access absence 使用 `unavailable`，execution/projection/policy failure 使用 `failed`。
- Core 必须把 `credential_invalid` 与 `verification_required` 视为 fail-closed read-side boundary，并与 `v1.2.0` resource governance 保持一致。
- Core 不拥有 media bytes storage、asset lifecycle、thumbnail generation、media transcoding、content library 或 asset library semantics。

## Adapter consumer rules

- Adapter 负责平台 creator id/profile field、平台 media ref/URL/content type、平台 fetch/download result 与 normalized projection。
- Adapter 必须保留 raw payload reference，但不得把 raw 平台字段提升为 Core 公共字段。
- `media_asset_fetch_by_ref` Adapter 必须先把 raw media shape 投影到公共 content type，再执行 request policy；无法投影公共 content type 时返回 `unsupported_content_type`，已投影但不在 `allowed_content_types` 内时返回 `fetch_policy_denied`。
- `media_asset_fetch_by_ref` Adapter 必须按照 fetch policy 决定是否允许 download outcome；不允许时必须返回 allowed non-download outcome 或 `fetch_policy_denied`。
- `media_asset_fetch_by_ref` Adapter 必须遵守 fetch policy 优先级：`download_required` 不满足下载条件时返回 `fetch_policy_denied`；`download_if_allowed` 允许但不强制 bytes transfer，未下载且可保留 source ref lineage 时只能降级为 `source_ref_preserved`。
- `media_asset_fetch_by_ref` Adapter 必须遵守 source-ref preservation policy：成功结果必须保留脱敏且可审计的 source ref lineage；无法保留时返回 `fetch_policy_denied`，不得降级为仅 metadata-only 的成功结果。
- Adapter 返回 `unavailable` 或 `failed` result status 时，必须把 `profile` / `media` 填为 `null`，无稳定 raw payload 时 `raw_payload_ref` 也必须为 `null`。
- `media_asset_fetch_by_ref` Adapter 返回 envelope `fetch_outcome=downloaded_bytes` 时，public metadata 必须提供 `byte_size`、`checksum_digest` 与 `checksum_family`；下载证明只能进入 audit evidence，不得成为 normalized media descriptor 或 consumer-visible bytes handle。
- `media_asset_fetch_by_ref` Adapter 返回 `metadata_only` 或 `source_ref_preserved` 时，不得提供 `byte_size`、`checksum_digest`、`checksum_family`、storage handle 或任何下载证明字段。
- `media_asset_fetch_by_ref` Adapter 的 public metadata 只能使用 `PublicMediaMetadata` 白名单字段；平台 media schema、provider routing、storage handle、raw headers/body、signed URL、session 或 credential 字段不得进入 public metadata。
- Adapter 暴露的 `source_media_ref` 必须是脱敏 opaque reference，不得携带 signed URL、session fields、credential material、bucket URL、本地路径或平台私有签名参数。
- `metadata_only` success 仍必须返回 `source_media_ref` 与 preserved `source_ref_lineage`；无法保留脱敏 source ref lineage 时必须返回 `fetch_policy_denied`。
- Adapter 暴露的 `source_ref_lineage` 必须是公共审计 carrier，只记录脱敏 `input_ref`、`source_media_ref`、`resolved_ref`、`canonical_ref` 与 preservation status；不得把 raw URL、签名字段、download handle 或 storage handle 塞入 lineage。
- Adapter 不得在本 FR 下返回 `content_type=mixed_media`；live-photo-like、component media 或无法投影为 `image` / `video` 的 shape 必须 fail-closed 到 `unsupported_content_type`。
- Adapter 可以保留 platform-specific metadata in adapter-managed extension area，但该 extension area 不属于 Core public result，Core public result 顶层不得依赖该扩展才能判定成功/失败、下载证明或 content type。

## Provider and metadata rules

- Provider 负责 HTTP、浏览器、第三方签名、bytes transfer 或执行路径，不定义 creator/media vocabulary。
- Provider metadata 不得把平台 raw payload schema、creator object schema、signed media URL schema、resource pool policy 或 provider routing policy 暴露给 Core。
- 稳定平台响应已经存在但无更强分类时，upstream failure 才能归类为 `platform_failed`；在稳定平台响应前被 provider、browser、network 或 third-party path 阻断时，只能归类为 `provider_or_network_blocked`。`source_trace.provider_path` 必须使用脱敏 opaque blocked-path alias，不得暴露 routing、fallback 或 selector details。
- signed request、request body 或 request contract 可识别为 invalid 时，必须优先分类为 `signature_or_request_invalid`，不得折叠为 `parse_failed`、`platform_failed` 或 `provider_or_network_blocked`。

## Consumer rules

- `creator_profile_by_id` 的 `TaskRecord` 后续只能记录 public creator target、result status、error classification、source trace、raw payload reference 与 normalized public profile；不得记录 `fetch_policy` 或 `fetch_outcome`。
- `media_asset_fetch_by_ref` 的 `TaskRecord` 后续只能记录 public media target、fetch policy、fetch outcome、result status、error classification、source trace、raw payload reference 与 normalized media descriptor；不得记录平台私有 media fields，且 result-query consumer 不得依赖 audit evidence 获取 bytes。
- result query consumer 后续只能消费 public result envelope 与 normalized result，不得依赖 raw payload shape 才能完成 profile/media workflow。
- compatibility decision 只消费 Adapter requirement 与 Provider offer 的 admission inputs；它不得消费 profile/media result envelope。后续 admission migration 必须先通过 canonical taxonomy / requirement / offer contract 扩展 approved execution slice，再让 decision 匹配这些输入。
- future TaskRecord / result-query consumer migration 必须把本 contract 视为 creator/media read foundation，而不是平台字段透传协议。

## Media fetch policy matrix

| adapter-visible condition | public contract result |
| --- | --- |
| raw media shape cannot be projected to `image` / `video` public content type | `unsupported_content_type` |
| projected public content type is excluded by `allowed_content_types` | `fetch_policy_denied` |
| sanitized source ref lineage cannot be preserved | `fetch_policy_denied` |
| `metadata_only` can satisfy content type and source-ref policy | `fetch_outcome=metadata_only` |
| `preserve_source_ref` can preserve sanitized source ref lineage | `fetch_outcome=source_ref_preserved` |
| `download_if_allowed` elects to transfer bytes within policy | `fetch_outcome=downloaded_bytes` |
| `download_if_allowed` does not transfer bytes but can preserve source ref | `fetch_outcome=source_ref_preserved` |
| `download_if_allowed` does not transfer bytes and cannot preserve sanitized source ref lineage | `fetch_policy_denied` |
| `download_required` cannot download within policy | `fetch_policy_denied` |

## Forbidden carrier fields

以下字段或语义不得进入 Core public metadata、result envelope 或 consumer-visible public contract：

- 平台私有 creator object / user object / profile schema
- private creator profile fields、account-sensitive fields 或 platform risk fields
- 平台 media URL list object、signature params、session fields 或 request body
- signed media URL、session-bearing URL、bucket URL、本地文件路径或 provider-local file path
- provider selector / routing / fallback / priority / ranking / marketplace
- media storage lifecycle、asset library、thumbnail/transcode pipeline 或 content library product behavior
- 外部项目名、本地路径或未脱敏来源标识

## Compatibility rule

`v1.5.0` creator/media contract 不改写 `content_detail_by_url + url + hybrid` stable baseline，不在本 Work Item 中改写 `v1.1.0` taxonomy foundation、`v1.2.0` resource governance health contract 或 `v1.3.0` read-side collection foundation。`creator_profile` 与 `media_asset_fetch` 在 canonical taxonomy / admission contracts 更新前仍不得被 requirement、offer 或 compatibility decision 当作 approved executable slice。`#404` comment collection 由独立 release slice 负责；本 FR 只在后续 runtime Work Item 进入实现前要求 shared runtime conflict-risk clearance。batch/dataset consumption 必须由后续 formal spec 或 Work Item 承接。
