# CHORE-0458 Scheduled Execution Fixture / Error / Evidence Inventory

## 关联信息

- item_key：`CHORE-0458-scheduled-execution-spec`
- Issue：`#458`
- item_type：`CHORE`
- release：`unbound`
- sprint：`unbound`
- Parent FR：`#457`
- Parent Phase：`#456`

## Fixture inventory

All fixture names are sanitized aliases. They do not represent real providers, account names, local paths, storage handles, or platform-private schedule fields.

| fixture | target | trigger | expected boundary |
|---|---|---|---|
| `scheduled-delayed-single-task` | existing single-task request | `DelayedTriggerRule` | due occurrence claims once and hands off to Core task path |
| `scheduled-recurring-single-task` | existing single-task request | `RecurringTriggerRule` | each occurrence has stable occurrence identity and TaskRecord ref |
| `scheduled-delayed-batch` | `FR-0445` batch request | `DelayedTriggerRule` | batch item outcomes, resume token, and dataset sink remain `FR-0445` owned |
| `scheduled-missed-skip` | existing single-task request | recurring rule plus downtime window | missed occurrence is skipped with audit evidence |
| `scheduled-missed-coalesce` | existing single-task request | recurring rule plus downtime window | multiple missed occurrences produce one coalesced occurrence |
| `scheduled-missed-catch-up` | existing single-task request | recurring rule plus downtime window | missed occurrences are replayed within policy window |
| `scheduled-duplicate-claim` | existing single-task request | due occurrence visible to two workers | one claim succeeds, the second records duplicate claim |
| `scheduled-retry-exhausted` | existing single-task request | delayed rule with retry policy | final state is `retry_exhausted` |
| `scheduled-unknown-outcome` | existing single-task request | delayed rule with interrupted handoff | final state is `unknown_outcome` and requires recovery decision |
| `scheduled-manual-recovery` | existing single-task request | delayed rule after unknown outcome | observation records `manual_recovery_required` |

## Error inventory

| error alias | meaning | owner |
|---|---|---|
| `invalid_trigger_rule` | trigger rule is not a supported delayed or recurring shape | Core schedule admission |
| `invalid_target_request` | schedule target is not an existing single-task or `FR-0445` batch request | Core schedule admission |
| `duplicate_claim` | due occurrence was already claimed by another lease | Core due claiming |
| `claim_lease_expired` | claim lease expired before handoff completion | Core due claiming |
| `missed_run_policy_required` | downtime produced missed occurrence without explicit policy | Core schedule admission |
| `retry_exhausted` | configured retry policy reached terminal failure | Core execution observation |
| `unknown_outcome` | handoff or execution state cannot be proven | Core execution observation |
| `manual_recovery_required` | runtime cannot safely continue without operator decision | Core execution observation |

## Evidence expectations

- Every occurrence must carry `schedule_id`, `occurrence_id`, due time, claim state, and scheduler observation ref.
- Every successful handoff must reference an existing TaskRecord; batch targets additionally reference `FR-0445` dataset / batch evidence where applicable.
- Missed run evidence must record the selected policy: `skip`, `coalesce`, or `catch_up`.
- Duplicate claim evidence must include the losing claim result without starting a second task execution.
- Unknown outcome and manual recovery evidence must avoid guessing success or failure.
- Evidence must not include raw payload files, platform names, account identifiers, local paths, storage handles, or private provider fields.
