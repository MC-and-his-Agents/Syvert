# CHORE-0406 v1.3.0 read-side collection fixture inventory

## Purpose

This artifact records the sanitized fixture and error inventory consumed by `FR-0403` Batch 0. It prepares reviewable evidence for the first collection-contract batch without introducing runtime behavior, raw fixture payload files, or source names that would pollute repository or GitHub truth.

## Inventory Summary

- release：`v1.3.0`
- fr_ref：`FR-0403`
- work_item_ref：`#406 / CHORE-0406-v1-3-read-side-collection-spec`
- phase_ref：`#381`
- status：`prepared`
- source aliases：
  - `raw-page-sample-a`
  - `raw-page-sample-b`
  - `reference-crawler-model-c`
- guarded constraints：
  - repository and GitHub truth must not record external project names
  - repository and GitHub truth must not record local filesystem paths
  - synthetic fixtures must be derived from recorded raw shape, not invented from scratch

## Source Alias Notes

- `raw-page-sample-a`
  - Current value: one reference platform render-state sample set with page-state and render-boundary evidence.
  - Current use: shape hints for collection response context and failure envelope design.
  - Current gap: collection item and next-page evidence still need more direct raw response capture.
- `raw-page-sample-b`
  - Current value: one reference platform initial-state sample set with content detail, comments, sub-comments, image-like media, video-like media, live-photo-like media, cursors, and `has_more`-style fields.
  - Current use: item envelope design, media ref hints, comment hierarchy hints, and cursor field shape.
  - Current gap: direct search/list raw response coverage is still incomplete.
- `reference-crawler-model-c`
  - Current value: mature cross-platform crawler model with search flow, creator flow, comment flow, checkpoint-backed continuation, and content/comment/creator model projections for at least two reference platforms.
  - Current use: cross-platform normalization contrast, continuation semantics, comment cursor semantics, and error-classification hints.
  - Current gap: repository truth must treat it as research input only, not as contract or source of code reuse.

## Fixture Matrix

| scenario_id | operation | source_kind | raw_shape_signal | expected_normalized_assertion | status |
| --- | --- | --- | --- | --- | --- |
| `search_first_page_platform_a` | `content_search_by_keyword` | `recorded` | first-page collection response with item array and continuation signal | collection result contains item envelope list, `has_more`, and next continuation input | `missing` |
| `search_next_page_platform_a` | `content_search_by_keyword` | `recorded` | second-page response using same continuation family as first page | next-page continuation is stable and does not change public item envelope shape | `missing` |
| `search_first_page_platform_b` | `content_search_by_keyword` | `recorded` | first-page response with page/offset plus search-session-like continuation | collection result can project non-cursor continuation into public continuation token | `missing` |
| `search_next_page_platform_b` | `content_search_by_keyword` | `recorded` | second-page response reusing page/offset plus search-session-like signal | public continuation token remains platform-neutral | `missing` |
| `list_first_page_platform_a` | `content_list_by_creator` | `recorded` | creator content list first page | item envelope for creator list reuses shared collection result shape | `missing` |
| `list_next_page_platform_a` | `content_list_by_creator` | `recorded` | creator content list next page with continuation | creator list continuation reuses shared collection continuation semantics | `missing` |
| `empty_result_collection` | `content_search_by_keyword` | `synthetic` | zero-item collection response derived from recorded response envelope | collection result returns empty `items`, stable target context, and no false partial-result flag | `missing` |
| `duplicate_item_across_pages` | `content_search_by_keyword` | `synthetic` | same logical item appears in page 1 and page 2 | dedup key remains stable across pages without relying on platform-private object name | `missing` |
| `cursor_or_session_expired` | `content_search_by_keyword` | `synthetic` | continuation token or search-session signal expires or becomes invalid | failure is classified as continuation invalid/expired, not parse failure | `missing` |
| `permission_denied_collection` | `content_search_by_keyword` | `synthetic` | platform response denies access to collection or target | result classification is `permission_denied` with fail-closed boundary | `missing` |
| `rate_limited_collection` | `content_search_by_keyword` | `synthetic` | platform response signals access-frequency or rate-limit control | result classification is `rate_limited`, not generic platform failure | `missing` |
| `platform_failed_collection` | `content_search_by_keyword` | `synthetic` | upstream platform failure response without stronger category | result classification is `platform_failed` | `missing` |
| `provider_or_network_blocked_collection` | `content_search_by_keyword` | `synthetic` | upstream provider or network path is blocked before stable collection response can be returned | result classification is `provider_or_network_blocked` | `missing` |
| `parse_failed_item` | `content_search_by_keyword` | `synthetic` | raw payload is present but one item cannot be projected | item-level parse failure can produce collection-level `partial_result` without leaking raw platform fields into Core | `missing` |
| `partial_result_page` | `content_search_by_keyword` | `synthetic` | one page mixes valid items and parse-failed items | collection result returns `partial_result` with valid normalized items preserved | `missing` |
| `credential_invalid_collection` | `content_search_by_keyword` | `synthetic` | resource/session health input is invalid before platform query completes | result boundary aligns with Phase 2 resource governance and does not masquerade as platform failure | `missing` |
| `verification_required_collection` | `content_search_by_keyword` | `synthetic` | platform requires verification/captcha/security challenge | result classification is `verification_required` and remains fail-closed | `missing` |

## Error Classification Mapping

| public classification | input source hint | intended use in `FR-0403` |
| --- | --- | --- |
| `rate_limited` | access-frequency / anti-abuse signal | distinguish platform throttling from generic failure |
| `permission_denied` | forbidden / private / unauthorized collection | stable access boundary |
| `target_not_found` | empty target or unavailable target signal | distinguish missing target from empty search result |
| `platform_failed` | upstream platform failure without stronger category | generic provider/platform failure |
| `provider_or_network_blocked` | blocked response / IP/network block signal | preserve provider/network boundary |
| `cursor_invalid_or_expired` | invalid continuation token or expired search-session-like signal | continuation-specific failure |
| `parse_failed` | raw payload present, projection unavailable | item or page projection failure |
| `partial_result` | mixed projection success and failure | preserve usable normalized output |
| `credential_invalid` | resource-governance failure from session/credential health | align with `v1.2.0` health contract |
| `verification_required` | captcha / security challenge | fail-closed collection access |
| `signature_or_request_invalid` | malformed signed request or request-contract failure | adapter/provider execution boundary |

## Acquisition Plan

1. Record happy-path collection responses for two reference platforms:
   - `content_search_by_keyword` first page
   - `content_search_by_keyword` next page
   - `content_list_by_creator` first page
   - `content_list_by_creator` next page
2. Normalize recorded metadata into the sanitized matrix only; do not commit raw payload files in this batch.
3. Derive synthetic scenarios from recorded response family:
   - empty result
   - duplicate item across pages
   - continuation invalid/expired
   - permission denied
   - rate limited
   - platform/provider failure
   - parse-failed item
   - partial-result page
   - credential-invalid
   - verification-required
4. Keep source alias to private working context mapping off-repo and out of GitHub truth.

## Acceptance For Batch 0

- The collection contract has a reviewable fixture matrix with scenario ids, expected assertions, and acquisition status.
- Error boundaries are grouped into public classifications suitable for `FR-0403` spec writing.
- No external project names or local paths appear in this artifact.
- The artifact can be consumed by `spec.md`, `plan.md`, and `risks.md` without introducing runtime decisions.
