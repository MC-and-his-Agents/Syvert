# FR-0445 Spec Review

## Review context

- FR：`#445 / FR-0445-batch-dataset-core-contract`
- Work Item：`#446 / CHORE-0446-v1-6-batch-dataset-spec`
- Release：`v1.6.0`
- Sprint：`2026-S25`

## Rubric result

- Scope separation：pass
- Public contract clarity：pass
- Read-side envelope reuse：pass
- Resource boundary：pass
- Evidence sanitization：pass
- Release planning truth：pass

## Findings

- Guardian review on PR `#451` returned `REQUEST_CHANGES` for three issues: `#381` completed truth drift, missing batch-id dataset readback surface, and undefined `duplicate_skipped` batch aggregation semantics.
- This follow-up resolves those blockers by aligning upstream truth with published read-side release slices, adding `read_by_batch(batch_id)`, and defining `duplicate_skipped` as a neutral terminal outcome for batch aggregation.
- Guardian follow-up review returned two contract closure issues: missing sanitized adapter identity and incomplete `resumable` outcome cardinality semantics.
- This follow-up resolves them by adding `adapter_key` / `source_trace` as sanitized Core carriers and defining `resumable` item outcomes as the processed target-set prefix with remaining work identified by `resume_token.next_item_index`.
- Guardian third review returned two closure issues: dataset identity lifecycle and post-resume terminal envelope semantics.
- This follow-up resolves them by defining `dataset_id` ownership/visibility and separating interrupted `resumable` envelopes from resumed terminal envelopes with canonical combined outcomes.
- Guardian merge-time review returned one coverage issue: frozen fail-closed boundaries lacked fixture/error/evidence entries.
- This follow-up resolves it by adding planned verification entries for invalid operation, resume mismatch, dataset write failure, non-JSON normalized payload, and carrier validation failure.

## Notes

- Runtime implementation must keep item execution on the existing Core task path.
- If later implementation reveals a defect in `FR-0403`、`FR-0404` or `FR-0405`, it must become a separate remediation Work Item.
