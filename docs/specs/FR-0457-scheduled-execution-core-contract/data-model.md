# FR-0457 Scheduled Execution Data Model

## TriggerRule

Core-owned schedule trigger vocabulary. It is intentionally smaller than product workflow scheduling.

### DelayedTriggerRule

- `trigger_type`: `delayed`.
- `run_at`: due timestamp for a single occurrence.
- `timezone`: optional timezone identifier for interpreting caller-supplied wall time.

### RecurringTriggerRule

- `trigger_type`: `recurring`.
- `start_at`: first eligible due timestamp.
- `interval`: Core-owned interval descriptor, such as `hourly`, `daily`, `weekly`, or an explicit duration.
- `timezone`: optional timezone identifier for wall-clock recurrence.
- `max_occurrences`: optional upper bound for finite recurrence.
- `end_at`: optional terminal timestamp.

Recurring rules define occurrence generation only. They do not carry business strategy, campaign logic, content selection, provider routing, or UI state.

## ScheduledTaskAdmission

Minimum Core admission carrier for a delayed or recurring schedule request.

- `schedule_id`: stable public schedule identifier.
- `target_request`: existing single-task request or `FR-0445` batch request.
- `trigger_rule`: `DelayedTriggerRule` or `RecurringTriggerRule`.
- `execution_policy`: timeout, retry, concurrency, and missed-run policy references.
- `created_at`: creation timestamp.

## ScheduleRecord

Durable schedule truth carrier owned by Core.

- `schedule_id`
- `status`: `active`, `paused`, `completed`, `cancelled`, or `invalid`.
- `trigger_rule`
- `target_request_ref`
- `execution_policy_ref`
- `last_observation_ref`

Allowed status transitions:

- `active` -> `paused`, `completed`, `cancelled`, `invalid`
- `paused` -> `active`, `cancelled`, `invalid`
- `completed`, `cancelled`, and `invalid` are terminal for the schedule record.

## TriggerOccurrence

A single due trigger derived from a schedule record.

- `occurrence_id`
- `schedule_id`
- `due_at`
- `claim_state`: `unclaimed`, `claimed`, `claim_lease_expired`, or `expired`.
- `task_record_ref`: populated after Core task admission.
- `result_state`: `pending`, `succeeded`, `failed`, `retry_exhausted`, `unknown_outcome`, or `manual_recovery_required`.

Allowed claim transitions:

- `unclaimed` -> `claimed`, `expired`
- `claimed` -> `claim_lease_expired`, or terminal execution observation through `result_state`
- `claim_lease_expired` -> `unclaimed` only when no `task_record_ref` exists and scheduler evidence proves Core task handoff did not start.
- `claim_lease_expired` -> `unknown_outcome` when handoff may have started but no terminal TaskRecord truth can be proven.
- `expired` does not start target task execution.
- Losing claim attempts do not mutate the shared occurrence into a duplicate terminal state; they record `duplicate_claim` on `ClaimLease.claim_result` and scheduler evidence.

Allowed result transitions:

- `pending` -> `succeeded`, `failed`, `retry_exhausted`, `unknown_outcome`, `manual_recovery_required`
- `failed` may transition to `retry_exhausted` only when retry policy is exhausted.
- `unknown_outcome` may transition to `manual_recovery_required`.
- `succeeded`, `retry_exhausted`, and `manual_recovery_required` are terminal until a separate remediation Work Item defines recovery behavior.

## ClaimLease

Core-owned lease used to prevent duplicate execution.

- `claim_id`
- `occurrence_id`
- `worker_ref`
- `claimed_at`
- `expires_at`
- `claim_result`: `claim_acquired`, `duplicate_claim`, `lease_expired`, or `invalid_occurrence`.

`claim_acquired` is the only result that allows Core task admission for the occurrence.

## MissedRunPolicy

Explicit behavior when one or more occurrences are missed.

- `policy`: `skip`, `coalesce`, or `catch_up`.
- `window_ref`: optional runtime window reference.
- `decision_evidence_ref`: scheduler observation proving which policy was applied.

## SchedulerObservation

Auditable scheduler evidence. It is not a product analytics record.

- `observation_id`
- `schedule_id`
- `occurrence_id`
- `task_record_ref`
- `dataset_record_ref`
- `resource_trace_ref`
- `status`: `observed_pending`, `observed_claim_lease_expired`, `observed_succeeded`, `observed_failed`, `observed_retry_exhausted`, `observed_unknown_outcome`, or `observed_manual_recovery_required`.
- `evidence_ref`

Observation status must mirror the occurrence `result_state` for execution outcomes. Claim-only observations such as `observed_claim_lease_expired` may explain why an occurrence returned to `unclaimed` or moved to `unknown_outcome`, but must not invent a separate success/failure truth.
