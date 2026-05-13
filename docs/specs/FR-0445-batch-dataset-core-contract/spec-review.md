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

## Notes

- Runtime implementation must keep item execution on the existing Core task path.
- If later implementation reveals a defect in `FR-0403`、`FR-0404` or `FR-0405`, it must become a separate remediation Work Item.
