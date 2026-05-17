# FR-0457 Scheduled Execution Contracts

## Core ownership

Core owns scheduled task admission, durable schedule record semantics, due occurrence claiming, missed run policy, scheduler observation, and handoff into the existing Core task path.

## Adapter / Provider boundary

Adapters and providers do not own public schedule vocabulary. They may execute the target task request only after Core admission and must not inject platform-private schedule fields into Core.

## TaskRecord / dataset / resource trace integration

Scheduled execution results must reference existing TaskRecord truth. Batch targets must reuse `FR-0445` batch item outcome, resume token, dataset record, and dataset sink semantics. Resource lease and release behavior remain item-operation scoped.

## Entry consistency

CLI, API, and scheduler-triggered entries must converge on the same Core admission and execution path. A scheduler trigger is not a separate runtime product path.

## Non-goals

This contract does not define UI, BI, content library, automatic operation workflow, business strategy DSL, scheduler service deployment, write-side operation, provider selector, fallback, marketplace, provider ranking, or provider SLA.
