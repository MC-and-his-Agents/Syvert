# Plan

## Implementation Goal

- Deliver Syvert's official Loom adoption carrier on PR #259.
- Keep Syvert guardian, integration contract, release/sprint/item_key semantics, and product-specific governance as repo-owned residue.
- Defer external-runtime / de-vendor support to a later Loom/Syvert migration issue.

## Phases

### Phase 1

- Objective: Add `.loom` carrier and companion contracts.
- Deliverable: `.loom/bootstrap`, `.loom/bin`, `.loom/companion`, `.loom/shadow`, work item, progress, status, review, and spec surfaces.
- Exit condition: `loom_init verify`, governance status, runtime parity, shadow parity, and flow resume pass in the Syvert worktree.

### Phase 2

- Objective: Align Syvert docs and repo-native governance boundary.
- Deliverable: AGENTS/WORKFLOW/process docs and ADR-GOV-0038 describe Loom as upstream runtime while preserving Syvert residue.
- Exit condition: docs guard and workflow guard pass.

### Phase 3

- Objective: Harden merge-readiness of the carrier itself.
- Deliverable: `.loom/**` structural gate coverage, formal spec/review/status consistency, GitHub parser hardening, and self-contained vendored bootstrap fallback.
- Exit condition: governance gate, spec guard, repo-local `loom_check`, guardian review, and CI pass.

## Constraints

- Architectural or governance constraints:
  - Loom provides generic runtime/governance semantics; Syvert retains repo-native guardian and integration contract authority.
  - `.loom/bin` is vendored for Loom v1.3 compatibility and must not assume `/Users/mc/dev/Loom` or an installed skills root for exposed repo-local commands.
- Workspace / rollout constraints:
  - Work is isolated on `issue-258-loom-official-adoption` and merged through PR #259.
  - GitHub issue closeout happens only after controlled merge and main-truth verification.
- Purity or scope constraints:
  - Gate checks must not write reviewed-tree artifacts such as `__pycache__`.
  - `.loom/**` is governance scope and must be structurally validated when changed.

## Validation

- Automated checks:
  - `python3 -m py_compile .loom/bin/*.py scripts/*.py scripts/policy/*.py`
  - `python3.11 scripts/docs_guard.py --mode ci`
  - `python3.11 scripts/workflow_guard.py --mode ci`
  - `python3.11 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - `python3.11 scripts/spec_guard.py --mode ci --base-sha $(git merge-base origin/main HEAD) --head-sha HEAD`
  - `python3.11 -m unittest discover -s tests/governance -p 'test_*.py'`
- Manual checks:
  - Guardian review on PR #259 with `--post-review`.
  - Controlled merge through Syvert merge entrypoint.
- Runtime evidence:
  - `python3 .loom/bin/loom_check.py .`
  - `python3 .loom/bin/loom_init.py verify --target .`
  - `python3 .loom/bin/loom_flow.py governance-profile status --target .`
  - `python3 .loom/bin/loom_flow.py runtime-parity validate --target .`
  - `python3 .loom/bin/loom_flow.py shadow-parity --target . --blocking`
  - `python3 .loom/bin/loom_flow.py flow resume --target . --item INIT-0001`

## Test Strategy

- TDD or test-first expectation:
  - Add regression coverage for dotted GitHub repo names, slash default branch encoding, and `.loom/**` structural guard behavior.
- Regression coverage to add or preserve:
  - Existing governance gate, docs guard, workflow guard, spec guard, guardian unit tests.
- Cases that are intentionally not automated:
  - Full GitHub issue tree closeout is verified by REST reads and issue comments after merge.

## Dependencies

- Blocking inputs:
  - CI checks for PR #259.
  - Guardian approval.
- Required coordination:
  - Work Item #258, FR #257, and Phase #256 closeout after merge.
- Rollback boundary:
  - If vendored runtime becomes too costly, a later PR may replace it with external-runtime companion; Syvert residue remains intact.

## Ready For Implementation

- [x] Spec is stable enough to implement
- [x] Scope and non-goals are clear
- [x] Validation path is defined
- [x] Risks and dependencies are explicit
