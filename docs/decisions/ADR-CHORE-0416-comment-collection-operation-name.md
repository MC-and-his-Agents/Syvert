# ADR-CHORE-0416 Comment Collection Operation Name

## 关联信息

- Issue：`#416`
- Parent FR：`#404`
- item_key：`CHORE-0416-v1-4-comment-collection-spec`
- item_type：`CHORE`
- release：`v1.4.0`
- sprint：`2026-S25`

## Status

Accepted

## Decision

Use `comment_collection` as the `#404` public executable operation name for the first comment read-side contract.

For `v1.4.0`, the executable slice is:

- `capability_family=comment_collection`
- `operation=comment_collection`
- `target_type=content`
- `execution_mode=single`
- `collection_mode=paginated`

This replaces the roadmap placeholder name `comment_list_by_content` for the `#404` slice. Future work may introduce a more specific operation name only through a separate taxonomy promotion and compatibility migration decision.

## Rationale

The current `FR-0368` taxonomy registry and admission evidence already carry `comment_collection` as the proposed comment candidate. Freezing `comment_list_by_content` in `FR-0404` before changing taxonomy truth would create two public operation names for the same slice.

Keeping `comment_collection` for `#404` preserves a single executable operation name across formal spec, release planning, runtime promotion, consumer migration, and evidence.

## Consequences

- `FR-0404`, `#417`, `#418`, `#419`, and `#420` must use `comment_collection` for the `#404` slice.
- `docs/roadmap-v1-to-v2.md` must list `comment_collection` as the comment read-side candidate operation.
- `comment_list_by_content` remains historical planning vocabulary only and is not a stable public operation in `v1.4.0`.
