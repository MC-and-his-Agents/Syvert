# CHORE-0432 v1.4 comment collection success classification amendment

## 关联信息

- item_key：`CHORE-0432-v1-4-comment-collection-success-classification-amendment`
- Issue：`#432`
- item_type：`CHORE`
- release：`v1.4.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#404`
- 关联 spec：`docs/specs/FR-0404-comment-collection-contract/`
- 关联 PR：
- 状态：`active`
- active 收口事项：`CHORE-0432-v1-4-comment-collection-success-classification-amendment`

## 目标

- Work Item: #432
- Parent FR: #404
- Scope: formal spec plus minimal executable contract amendment for non-empty `comment_collection` success pages.
- Out of scope: adapter execution behavior, #419 evidence artifact implementation, release tag, GitHub Release, #420 closeout, and #405 creator/media contracts.

## 改动记录

- `FR-0404` now freezes `error_classification=success` as the only success sentinel for non-empty `result_status=complete` comment pages.
- `comment_collection` validator now accepts `success` only for non-empty `complete` pages and continues to reject failure classifications carrying items.
- #419 fixture inventory now requires `success` for non-empty success-page evidence.
- Collection-level failures remain fail-closed and must not carry `items`, `has_more=true`, or executable continuation.
- `partial_result` remains a compatibility vocabulary entry and is not emitted as a standalone comment error classification.

## 验证记录

- `git diff --check`
- `python3 scripts/spec_guard.py --mode ci --base-sha 918cff01a8fa3b8488cfee747d79f07233c84691 --head-sha HEAD`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/version_guard.py --mode ci`
- `python3 scripts/governance_gate.py --mode ci --base-sha 918cff01a8fa3b8488cfee747d79f07233c84691 --head-sha HEAD --head-ref issue-432-404-v1-4-0-comment-collection-success-classification-amendment`
- `python3 -m unittest tests.runtime.test_comment_collection`
- sanitized external source-name/path scan over the changed `FR-0404` spec, exec-plan, release index, and sprint index（no matches）

## Review finding 处理记录

- #433 guardian P1/P2: formal spec introduced `success` while executable contract and #419 fixture inventory remained on old success-page semantics.
- Resolution: added minimal validator/test support for `success` and updated #419 fixture inventory prerequisites.

## 未决风险

- #419 must update evidence artifacts to emit `success`; this Work Item only updates the shared validator and focused carrier tests required to prevent spec/contract drift.

## 回滚方式

- Use a revert PR for this Work Item only. #417/#418 remain independently merged.

## 最近一次 checkpoint 对应的 head SHA

- `918cff01a8fa3b8488cfee747d79f07233c84691`
