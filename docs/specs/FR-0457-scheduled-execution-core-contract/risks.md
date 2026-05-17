# FR-0457 Scheduled Execution Risks

## Hidden workflow product creep

Risk: schedule policy expands into business workflow strategy, campaign logic, or UI behavior.

Guardrail: schedule record only carries trigger rule, target task request, and execution policy. Product strategy remains outside Syvert Core.

## Duplicate execution

Risk: multiple workers claim the same due occurrence and run the same task twice.

Guardrail: due claiming semantics must define a single winner and stable duplicate-claim evidence.

## Missed-run ambiguity

Risk: scheduler downtime produces unclear catch-up behavior.

Guardrail: missed run policy must explicitly choose skip, coalesce, or catch-up and record the decision.

## Durable truth drift

Risk: schedule state and TaskRecord result truth diverge.

Guardrail: occurrence execution must write through existing TaskRecord / dataset / resource trace carriers and keep scheduler observation referential.

## Resource lease bypass

Risk: scheduler execution bypasses resource governance.

Guardrail: target task execution must reuse Core resource admission, lease, trace, and release behavior.

## Retry amplification

Risk: recurring schedules and retry policy multiply failures or resource pressure.

Guardrail: retry exhausted and unknown outcome states must be explicit before runtime implementation.

## Premature write-side coupling

Risk: scheduled execution is used to introduce write-side behavior before safety gates exist.

Guardrail: write-side operation and safety gate implementation remain out of scope for this admission.
