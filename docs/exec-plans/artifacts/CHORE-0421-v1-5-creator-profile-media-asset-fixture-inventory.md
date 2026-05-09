# CHORE-0421 v1.5.0 creator profile / media asset fixture inventory

## Purpose

This artifact records the sanitized fixture and error inventory consumed by `FR-0405` Batch 0. It prepares reviewable evidence for creator profile and media asset read contracts without introducing runtime behavior, raw fixture payload files, source names, repository names, or local filesystem paths.

## Inventory Summary

- release：`v1.5.0`
- fr_ref：`FR-0405`
- work_item_ref：`#421 / CHORE-0421-v1-5-creator-profile-media-asset-spec`
- phase_ref：`#381`
- status：`prepared`
- source aliases：
  - `raw-page-sample-a`
  - `raw-page-sample-b`
  - `reference-crawler-model-c`
- guarded constraints：
  - repository and GitHub truth must not record external project names
  - repository and GitHub truth must not record local filesystem paths
  - synthetic fixtures must be derived from recorded raw shape family, not invented from scratch
  - Core contract must not become a media library, creator profile product model, or asset storage schema

## Source Alias Notes

- `raw-page-sample-a`
  - Current value: one reference platform render-state sample set with page-state and render-boundary evidence.
  - Current use: profile page availability, missing-target, verification, and rendered-media boundary hints.
  - Current gap: raw payload files and source mapping remain intentionally out of repo; runtime Work Items must consume only sanitized descriptors or separately approved test fixtures.
- `raw-page-sample-b`
  - Current value: one reference platform initial-state sample set with content detail, author snippets, image-like media, video-like media, live-photo-like hints, cursors, and media references.
  - Current use: public profile field boundary hints, media ref shape, content type boundary, and source-ref preservation examples.
  - Current gap: evidence Work Item must convert these descriptors into fake/reference contract fixtures without committing raw payload.
- `reference-crawler-model-c`
  - Current value: mature cross-platform crawler model with creator model projections, content media URL fields, image/video list fields, and storage schema contrast for at least two reference platforms.
  - Current use: two-reference normalization contrast for public creator fields, media ref/content type semantics, metadata-only vs download boundary, and no-storage guardrails.
  - Current gap: repository truth must treat it as research input only, not as contract, source code, or raw payload source.

## Evidence Status Vocabulary

- `acquired_sanitized_descriptor`：已从私有工作上下文取得脱敏字段族/状态族描述，可支撑 formal spec vocabulary；不表示 raw payload 入仓。
- `derived_from_acquired_descriptor`：由已取得脱敏字段族/状态族派生的 fail-closed 或 policy 边界，可支撑 spec 场景；后续 runtime evidence 仍需 fake/reference contract fixture。
- `planned_for_runtime_fixture`：当前 Work Item 只记录需求，必须由后续 runtime/evidence Work Item 转成可执行 fixture。
- `missing`：当前没有足够脱敏输入支撑，不得用于冻结 public contract。

## Fixture Matrix

| scenario_id | operation | source_kind | raw_shape_signal | expected_normalized_assertion | status |
| --- | --- | --- | --- | --- | --- |
| `creator_profile_success_platform_a` | `creator_profile_by_id` | `recorded` | public creator profile response with id, display name, avatar, description, and public counters | normalized profile contains public fields only, source trace, and raw payload ref | `acquired_sanitized_descriptor` |
| `creator_profile_success_platform_b` | `creator_profile_by_id` | `recorded` | second reference public creator model with different field names and optional counters | same normalized public profile envelope can represent both references | `acquired_sanitized_descriptor` |
| `creator_profile_not_found` | `creator_profile_by_id` | `synthetic` | creator id is absent, deleted, or not resolvable | result classification is `target_not_found`, not `empty_result` or `platform_failed` | `derived_from_acquired_descriptor` |
| `creator_profile_unavailable` | `creator_profile_by_id` | `synthetic` | creator exists but profile is unavailable for all public reads | result classification is `profile_unavailable`, not `permission_denied` | `derived_from_acquired_descriptor` |
| `creator_profile_permission_denied` | `creator_profile_by_id` | `synthetic` | creator exists but current requester/resource has no permission to view profile | result classification is `permission_denied`, not `profile_unavailable`, and private fields are not exposed | `derived_from_acquired_descriptor` |
| `creator_profile_rate_limited` | `creator_profile_by_id` | `synthetic` | profile read returns access-frequency / anti-abuse signal | result classification is `rate_limited`, not generic platform failure | `derived_from_acquired_descriptor` |
| `creator_profile_platform_failed` | `creator_profile_by_id` | `synthetic` | upstream platform failure without stronger creator-profile category | result classification is `platform_failed` and normalized profile is `null` | `derived_from_acquired_descriptor` |
| `creator_profile_provider_or_network_blocked` | `creator_profile_by_id` | `synthetic` | provider/browser/network path blocked before stable profile payload | result classification is `provider_or_network_blocked` and raw payload ref is `null` when no payload exists | `derived_from_acquired_descriptor` |
| `creator_profile_parse_failed` | `creator_profile_by_id` | `synthetic` | raw payload is present but public profile projection cannot satisfy minimum field rules | result classification is `parse_failed` with raw payload ref preserved | `derived_from_acquired_descriptor` |
| `creator_profile_credential_invalid` | `creator_profile_by_id` | `synthetic` | resource/session health input is invalid before profile read completes | result classification is `credential_invalid` and remains aligned with resource governance | `derived_from_acquired_descriptor` |
| `creator_profile_verification_required` | `creator_profile_by_id` | `synthetic` | platform requires verification/captcha/security challenge before profile read | result classification is `verification_required` and remains fail-closed | `derived_from_acquired_descriptor` |
| `creator_profile_signature_or_request_invalid` | `creator_profile_by_id` | `synthetic` | signed request or request contract is invalid before stable profile read | result classification is `signature_or_request_invalid`, not generic platform failure | `derived_from_acquired_descriptor` |
| `image_media_ref` | `media_asset_fetch_by_ref` | `recorded` | content/media object exposes image-like media reference | normalized media ref preserves source ref and `content_type=image` | `acquired_sanitized_descriptor` |
| `video_media_ref` | `media_asset_fetch_by_ref` | `recorded` | content/media object exposes video-like media reference | normalized media ref preserves source ref and `content_type=video` | `acquired_sanitized_descriptor` |
| `live_photo_like_media_unsupported` | `media_asset_fetch_by_ref` | `recorded` | content/media object exposes live-photo-like or component media hints | current FR treats this shape as `unsupported_content_type` unless a later FR defines component carrier semantics | `acquired_sanitized_descriptor` |
| `media_metadata_only` | `media_asset_fetch_by_ref` | `synthetic` | media ref is resolved without downloading bytes while sanitized source ref lineage is preserved | fetch result records `fetch_outcome=metadata_only`, `source_ref_lineage.preservation_status=preserved`, no download handle, and no-storage semantics | `derived_from_acquired_descriptor` |
| `media_source_ref_preserved` | `media_asset_fetch_by_ref` | `synthetic` | media ref is preserved as source URL/ref with metadata | fetch result records `fetch_outcome=source_ref_preserved`, no download handle, and does not claim downloaded bytes | `derived_from_acquired_descriptor` |
| `media_source_ref_lineage_preserved` | `media_asset_fetch_by_ref` | `synthetic` | request media ref can be traced to sanitized source ref and canonical ref | result records `source_ref_lineage.preservation_status=preserved` without leaking raw URL/signature/session fields | `derived_from_acquired_descriptor` |
| `media_downloaded_bytes_boundary` | `media_asset_fetch_by_ref` | `synthetic` | adapter/provider downloads bytes for a media ref | public result records `byte_size`, `checksum_digest`, and `checksum_family`; any download proof is audit-only and does not expose storage handle or Core asset storage semantics | `derived_from_acquired_descriptor` |
| `media_unavailable` | `media_asset_fetch_by_ref` | `synthetic` | referenced media no longer exists or cannot be resolved | result classification is `media_unavailable`, not `permission_denied` or `platform_failed` | `derived_from_acquired_descriptor` |
| `media_unsupported_content_type` | `media_asset_fetch_by_ref` | `synthetic` | media content type is unsupported by public contract | result classification is `unsupported_content_type` and remains fail-closed | `derived_from_acquired_descriptor` |
| `media_policy_content_type_denied` | `media_asset_fetch_by_ref` | `synthetic` | media content type is recognized and supported but excluded by `allowed_content_types` | result classification is `fetch_policy_denied`, not `unsupported_content_type` | `derived_from_acquired_descriptor` |
| `media_source_ref_lineage_denied` | `media_asset_fetch_by_ref` | `synthetic` | sanitized source ref lineage cannot be preserved | result classification is `fetch_policy_denied`, not metadata-only success | `derived_from_acquired_descriptor` |
| `media_permission_denied` | `media_asset_fetch_by_ref` | `synthetic` | media ref exists but cannot be accessed by current resources | result classification is `permission_denied` without leaking credential/session details | `derived_from_acquired_descriptor` |
| `media_rate_limited` | `media_asset_fetch_by_ref` | `synthetic` | media fetch returns access-frequency / anti-abuse signal | result classification is `rate_limited` | `derived_from_acquired_descriptor` |
| `media_platform_failed` | `media_asset_fetch_by_ref` | `synthetic` | upstream platform failure without stronger media category | result classification is `platform_failed` and normalized media is `null` | `derived_from_acquired_descriptor` |
| `media_provider_or_network_blocked` | `media_asset_fetch_by_ref` | `synthetic` | provider/network path is blocked before stable media result | result classification is `provider_or_network_blocked` | `derived_from_acquired_descriptor` |
| `media_large_asset_download_required_denied` | `media_asset_fetch_by_ref` | `synthetic` | `download_required` request exceeds policy/cost boundary | fetch is classified as `fetch_policy_denied`, without implicit metadata downgrade | `derived_from_acquired_descriptor` |
| `media_large_asset_download_if_allowed_downgrade` | `media_asset_fetch_by_ref` | `synthetic` | `download_if_allowed` request exceeds policy/cost boundary but source ref lineage is available | fetch downgrades to `source_ref_preserved`, without implicit bytes download | `derived_from_acquired_descriptor` |
| `media_parse_failed` | `media_asset_fetch_by_ref` | `synthetic` | raw media payload/ref is present but projection cannot satisfy result rules | result classification is `parse_failed` | `derived_from_acquired_descriptor` |
| `media_credential_invalid` | `media_asset_fetch_by_ref` | `synthetic` | resource/session health input is invalid before media fetch completes | result classification is `credential_invalid` and remains aligned with resource governance | `derived_from_acquired_descriptor` |
| `media_verification_required` | `media_asset_fetch_by_ref` | `synthetic` | platform requires verification/captcha/security challenge before media fetch | result classification is `verification_required` and remains fail-closed | `derived_from_acquired_descriptor` |
| `media_signature_or_request_invalid` | `media_asset_fetch_by_ref` | `synthetic` | signed request or request contract is invalid before stable media fetch | result classification is `signature_or_request_invalid`, not generic platform/provider failure | `derived_from_acquired_descriptor` |

## Error Classification Mapping

| public classification | input source hint | intended use in `FR-0405` |
| --- | --- | --- |
| `target_not_found` | absent/deleted creator id or unresolved creator target | distinguish missing target from private/unavailable profile |
| `profile_unavailable` | creator exists but profile is unavailable or not publicly viewable | preserve creator-specific public availability boundary |
| `media_unavailable` | media ref no longer exists or cannot be resolved | preserve media-specific availability boundary |
| `unsupported_content_type` | media type is outside accepted public content type set | keep unsupported content separate from parse failure |
| `permission_denied` | forbidden/private/unauthorized profile or media read | stable access boundary |
| `rate_limited` | access-frequency / anti-abuse signal | distinguish throttling from generic failure |
| `platform_failed` | upstream platform failure without stronger category | generic platform failure |
| `provider_or_network_blocked` | blocked response / IP/network/provider path | preserve provider/network boundary |
| `parse_failed` | raw payload present, projection unavailable | profile or media projection failure |
| `credential_invalid` | resource-governance failure from session/credential health | align with `v1.2.0` health contract |
| `verification_required` | captcha / security challenge | fail-closed creator/media access |
| `signature_or_request_invalid` | malformed signed request or request-contract failure | adapter/provider execution boundary |
| `fetch_policy_denied` | requested download or fetch mode violates policy/cost boundary | preserve download/no-download boundary without media storage semantics |

## Acquisition Plan

1. Record or summarize sanitized happy-path creator profile shapes for two reference platforms:
   - public profile success
   - optional public counters
   - avatar/image public ref
   - creator not found or unavailable boundary
2. Record or summarize sanitized media reference and fetch outcome shapes:
   - image media ref
   - video media ref
   - metadata-only fetch
   - source-ref-preserved fetch
   - downloaded-bytes outcome metadata
3. Convert derived scenarios from recorded response families into executable fake/reference fixtures:
   - permission denied
   - rate limited
   - platform/provider failure
   - unavailable media
   - unsupported content type
   - large asset/cost boundary
   - parse failure
   - credential invalid
   - verification required
   - signature/request invalid
4. Keep source alias to private working context mapping off-repo and out of GitHub truth.

## Acceptance For Batch 0

- The creator/profile/media contract has a reviewable fixture matrix with scenario ids, expected assertions, acquisition status, and enough sanitized descriptor evidence to support formal spec vocabulary.
- Error boundaries are grouped into public classifications suitable for `FR-0405` spec writing.
- No external project names or local paths appear in this artifact.
- The artifact can be consumed by `spec.md`, `plan.md`, and `risks.md` without introducing runtime decisions.
