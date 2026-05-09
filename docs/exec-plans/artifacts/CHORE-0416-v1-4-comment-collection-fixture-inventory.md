# CHORE-0416 v1.4 comment collection fixture inventory

## Purpose

This artifact records the sanitized fixture and error inventory consumed by `FR-0404` Batch 0. It prepares reviewable evidence for the first comment-collection contract batch without introducing runtime behavior, raw fixture payload files, or source names that would pollute repository or GitHub truth.

## Inventory Summary

- release：`v1.4.0`
- fr_ref：`FR-0404`
- work_item_ref：`#416 / CHORE-0416-v1-4-comment-collection-spec`
- phase_ref：`#381`
- status：`prepared`
- source aliases：
  - `raw-page-sample-b`
  - `reference-crawler-model-c`
- guarded constraints：
  - repository and GitHub truth must not record external project names
  - repository and GitHub truth must not record local filesystem paths
  - synthetic fixtures must be derived from recorded raw shape, not invented from scratch

## Source Alias Notes

- `raw-page-sample-b`
  - Current value: one reference platform initial-state sample set with top-level comments, sub-comments, target-comment linkage, per-comment cursor, sub-comment cursor, status signals, engagement fields, and `has_more`-style fields.
  - Current use: comment target hierarchy, reply cursor family, visibility hints, and normalized comment item minimum fields.
  - Current gap: second reference platform raw comment response coverage is still incomplete.
- `reference-crawler-model-c`
  - Current value: mature cross-platform crawler model with comment flow, checkpoint-backed continuation, and two different comment identity/hierarchy models across at least two reference platforms.
  - Current use: root/parent/reply linkage contrast, cursor family contrast, and visibility/error classification hints.
  - Current gap: repository truth must treat it as research input only, not as contract or source of code reuse.

## Fixture Matrix

| scenario_id | operation | source_kind | raw_shape_signal | expected_normalized_assertion | status |
| --- | --- | --- | --- | --- | --- |
| `comment_first_page_platform_a` | `comment_collection` | `recorded` | first-page top-level comment response with item array and continuation signal | result contains comment item envelope list, `has_more`, and next continuation input | `recorded_covered` |
| `comment_next_page_platform_a` | `comment_collection` | `recorded` | second-page top-level comment response using same continuation family | previous result `next_continuation` can round-trip through request `page_continuation` without changing comment public envelope shape | `recorded_covered` |
| `reply_page_platform_a` | `comment_collection` | `recorded` | reply page for one root comment with reply cursor signal | comment item can carry a stable reply cursor without leaking platform cursor object | `recorded_covered` |
| `comment_first_page_platform_b` | `comment_collection` | `modeled` | first-page response from second reference platform with different parent/reply identifiers | comment target, root/parent linkage, and source trace can project into same public surface | `model_covered_raw_gap` |
| `comment_next_page_platform_b` | `comment_collection` | `modeled` | second-page response from second reference platform with page/offset-like continuation | public continuation remains platform-neutral and uses the same result-to-request field mapping | `model_covered_raw_gap` |
| `empty_comment_result` | `comment_collection` | `synthetic` | valid content target with zero visible comments | result returns `items=[]`, `result_status=empty`, and no false not-found classification | `synthetic_derivable` |
| `comment_target_not_found` | `comment_collection` | `synthetic` | content target is unavailable or not resolvable on the platform | result classification is `target_not_found`, not `empty_result` | `synthetic_derivable` |
| `deleted_comment_item` | `comment_collection` | `synthetic` | one comment is returned with deleted marker but the page is otherwise valid | item visibility is `deleted` and the page can still remain `complete` | `semantic_freeze_recording_pending` |
| `invisible_comment_item` | `comment_collection` | `synthetic` | one comment is hidden or blocked by platform visibility control | item visibility is `invisible` without leaking platform moderation flags | `semantic_freeze_recording_pending` |
| `unavailable_comment_item` | `comment_collection` | `synthetic` | one comment placeholder is returned with stable unavailable marker but without full body payload or stable platform comment id | item visibility is `unavailable`; `source_id` uses a public placeholder namespace derived from target/visibility/stable placeholder marker inputs, while `canonical_ref` binds to that identity | `synthetic_derivable` |
| `target_comment_linkage` | `comment_collection` | `synthetic` | reply references both root comment and target comment | normalized item preserves root/parent/target linkage through `canonical_ref` bindings | `recorded_covered` |
| `reply_cursor_resume` | `comment_collection` | `synthetic` | one comment exposes a reply cursor that can resume nested replies | `reply_cursor.resume_comment_ref` stays bound to the same comment item `canonical_ref` | `recorded_covered` |
| `duplicate_comment_item` | `comment_collection` | `synthetic` | same logical comment appears across pages or reply windows | dedup key remains stable across pages without relying on platform-private object name | `synthetic_derivable` |
| `permission_denied_comment_collection` | `comment_collection` | `synthetic` | platform denies access to comments or target visibility | result classification is `permission_denied` with fail-closed boundary | `semantic_freeze_recording_pending` |
| `rate_limited_comment_collection` | `comment_collection` | `synthetic` | platform response signals rate-limit control while loading comments | result classification is `rate_limited` | `semantic_freeze_recording_pending` |
| `platform_failed_comment_collection` | `comment_collection` | `synthetic` | upstream platform failure without stronger category | result classification is `platform_failed` | `synthetic_derivable` |
| `provider_or_network_blocked_comment_collection` | `comment_collection` | `synthetic` | provider path is blocked before stable comment response can be returned | result classification is `provider_or_network_blocked` | `synthetic_derivable` |
| `signature_or_request_invalid_comment_collection` | `comment_collection` | `synthetic` | signed request or request-contract is malformed before comments can load | result classification is `signature_or_request_invalid` | `synthetic_derivable` |
| `parse_failed_comment_item` | `comment_collection` | `synthetic` | raw payload is present but one comment cannot be projected | malformed comment item can force `partial_result` without discarding valid comments | `synthetic_derivable` |
| `partial_result_comment_page` | `comment_collection` | `synthetic` | one page mixes valid comments and parse-failed comments | result returns `partial_result` with valid normalized comments preserved | `synthetic_derivable` |
| `total_parse_failed_comment_page` | `comment_collection` | `synthetic` | raw payload is present but zero comments can be projected | result returns fail-closed `complete + parse_failed`, `items=[]`, `has_more=false`, and no continuation | `synthetic_derivable` |
| `cursor_invalid_or_expired_comment_collection` | `comment_collection` | `synthetic` | next-page continuation or reply cursor expires or becomes invalid | failure is classified as continuation invalid/expired | `synthetic_derivable` |
| `credential_invalid_comment_collection` | `comment_collection` | `synthetic` | resource/session health input is invalid before platform query completes | boundary aligns with `v1.2.0` resource governance | `synthetic_derivable` |
| `verification_required_comment_collection` | `comment_collection` | `synthetic` | platform requires verification or captcha before comments can load | result classification is `verification_required` and remains fail-closed | `synthetic_derivable` |

## Coverage Status Legend

| status | meaning |
| --- | --- |
| `recorded_covered` | current sanitized alias inventory already has recorded raw-shape evidence sufficient for spec freeze |
| `model_covered_raw_gap` | cross-platform model evidence exists, but raw recorded response still needs补采 for later evidence replay |
| `synthetic_derivable` | scenario can be derived from current recorded raw shape family during runtime/evidence work |
| `semantic_freeze_recording_pending` | public semantics are frozen in this batch, but dedicated recorded/synthetic evidence still needs补采 in `#419` |

## Coverage Snapshot

- Recorded raw shape already grounds:
  - top-level first page / next page
  - reply page / reply cursor family
  - target/root/parent linkage
- Model evidence grounds, but still needs second-platform raw response capture:
  - second-platform first page / next page
- Remaining acquisition gaps for later runtime/evidence rounds:
  - dedicated deleted / invisible visibility fixture
  - dedicated permission-denied failure fixture
  - dedicated rate-limited failure fixture

## Error Classification Mapping

| public classification | input source hint | intended use in `FR-0404` |
| --- | --- | --- |
| `rate_limited` | access-frequency / anti-abuse signal | distinguish throttling from generic failure |
| `permission_denied` | private content / unauthorized comment access | stable collection access boundary |
| `target_not_found` | content target missing or unavailable | distinguish missing target from empty comment page |
| `empty_result` | valid content target with zero comments | distinguish legal zero-item page from missing target |
| `platform_failed` | upstream platform failure without stronger category | generic provider/platform failure |
| `provider_or_network_blocked` | blocked response / IP/network block signal | preserve provider/network boundary |
| `cursor_invalid_or_expired` | invalid next-page continuation or reply cursor | continuation-specific failure |
| `parse_failed` | raw payload present, comment projection unavailable | item or page projection failure |
| `credential_invalid` | resource-governance failure from session/credential health | align with `v1.2.0` health contract |
| `verification_required` | captcha / security challenge | fail-closed comment access |
| `signature_or_request_invalid` | malformed signed request or request-contract failure | adapter/provider execution boundary |

## Visibility Mapping

| visibility_status | public meaning | raw-shape trigger hint |
| --- | --- | --- |
| `visible` | comment body and minimum public fields are available | normal comment item |
| `deleted` | comment existed but platform marks it deleted | deleted placeholder or delete marker |
| `invisible` | comment exists but visibility is suppressed for the current viewer | hidden/moderated/private visibility signal |
| `unavailable` | comment slot exists but body/public projection is not currently available | placeholder or missing-body response |

## Acquisition Plan

1. Record happy-path top-level comment responses for two reference platforms:
   - first page
   - next page
   - one reply page or nested reply window
2. Normalize recorded metadata into the sanitized matrix only; do not commit raw payload files in this batch.
3. Derive synthetic scenarios from recorded response family:
   - empty result
   - target not found
   - deleted/invisible/unavailable comment item
   - target/root/parent linkage
   - reply cursor resume
   - duplicate item across pages
   - continuation invalid/expired
   - permission denied
   - rate limited
   - platform/provider failure
   - parse-failed comment item
   - partial-result page
   - credential-invalid
   - signature/request-invalid
   - verification-required
4. Keep source alias to private working context mapping off-repo and out of GitHub truth.

## Spec Freeze Consumption Rule

- `FR-0404` can freeze public semantics when a scenario is `recorded_covered`, `model_covered_raw_gap`, `synthetic_derivable`, or `semantic_freeze_recording_pending`.
- Scenarios marked `semantic_freeze_recording_pending` are explicitly carried forward into `#419` evidence scope and must not be silently treated as already recorded-proven.

## Acceptance For Batch 0

- The comment contract has a reviewable fixture matrix with scenario ids, expected assertions, and acquisition status.
- Error boundaries and item visibility states are grouped into public semantics suitable for `FR-0404` spec writing.
- No external project names or local paths appear in this artifact.
- The artifact can be consumed by `spec.md`, `plan.md`, and `risks.md` without introducing runtime decisions.
