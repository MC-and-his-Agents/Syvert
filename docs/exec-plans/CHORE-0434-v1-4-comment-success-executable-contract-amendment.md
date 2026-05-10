# CHORE-0434 v1.4 comment success executable contract amendment

## 关联信息

- item_key：`CHORE-0434-v1-4-comment-success-executable-contract-amendment`
- Issue：`#434`
- item_type：`CHORE`
- release：`v1.4.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#404`
- 关联 spec：`docs/specs/FR-0404-comment-collection-contract/`
- 关联 PR：
- 状态：`active`
- active 收口事项：`CHORE-0434-v1-4-comment-success-executable-contract-amendment`

## 目标

- Work Item: #434
- Parent FR: #404
- Scope: minimal executable contract support for non-empty `comment_collection` success pages.
- Out of scope: formal spec text changes, #419 evidence artifact implementation, release tag, GitHub Release, #420 closeout, and #405 creator/media contracts.

## 改动记录

- `comment_collection` validator accepts `error_classification=success` only when `result_status=complete` and `items` is non-empty.
- `success` remains comment-specific and is not added to the shared read-side collection vocabulary.
- Non-empty `complete` comment pages using failure classifications still fail closed.
- Focused carrier tests cover valid success pages and invalid `success` combinations.

## 验证记录

- `git diff --check`
- `python3 -m unittest tests.runtime.test_comment_collection`
- `python3 -m unittest tests.runtime.test_read_side_collection`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/version_guard.py --mode ci`
- `python3 scripts/governance_gate.py --mode ci --base-sha 5ee1b6408459aae4c499ba03c29fb9bda9b6c8d2 --head-sha HEAD --head-ref issue-434-404-v1-4-0-comment-success-executable-contract-amendment`
- sanitized external source-name/path scan over the changed implementation, tests, and exec-plan（no matches）

## Review finding 处理记录

- #433 guardian identified that the `FR-0404` success-page spec amendment needs matching executable contract support before the spec PR can merge.
- Resolution: split implementation support into this Work Item so #432 can remain spec-only.
- #435 guardian P1: `success` was initially added to shared collection vocabulary, which could widen `FR-0403`.
- Resolution: keep `success` comment-specific and add a read-side collection regression test.

## 未决风险

- #432 has merged and is the formal spec truth consumed by this Work Item.
- #419 must update evidence artifacts to emit `success`.

## 回滚方式

- Use a revert PR for this Work Item only. #417/#418 remain independently merged.

## 最近一次 checkpoint 对应的 head SHA

- `5ee1b6408459aae4c499ba03c29fb9bda9b6c8d2`
