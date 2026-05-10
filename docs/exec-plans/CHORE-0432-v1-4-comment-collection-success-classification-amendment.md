# CHORE-0432 v1.4 comment success carrier spec migration

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

## 目标

- Work Item: #432
- Parent FR: #404
- Scope: formal spec and decision truth for the `comment_collection` non-empty success page carrier.
- Out of scope: executable validator changes, evidence artifact implementation, release tag, GitHub Release, #420 closeout, and #405 creator/media contracts.

## 改动记录

- `FR-0404` now defines `error_classification=success` as a comment-specific success sentinel.
- `success` is valid only for non-empty `result_status=complete` comment pages.
- `success` is explicitly excluded from the `FR-0403` shared read-side collection vocabulary.
- This exec-plan records the staged migration rule: #432 spec truth -> #434 executable contract -> #419 evidence -> #420 release closeout.

## 验证记录

- `git diff --check`：通过。
- `python3 scripts/spec_guard.py --mode ci --base-sha 918cff01a8fa3b8488cfee747d79f07233c84691 --head-sha HEAD`：通过。
- `python3 scripts/docs_guard.py --mode ci`：通过。
- `python3 scripts/workflow_guard.py --mode ci`：通过。
- `python3 scripts/version_guard.py --mode ci`：通过。
- `python3 scripts/governance_gate.py --mode ci --base-sha 918cff01a8fa3b8488cfee747d79f07233c84691 --head-sha HEAD --head-ref issue-432-404-v1-4-0-comment-collection-success-classification-amendment`：通过。
- sanitized external source-name/path scan over changed spec, exec-plan, release index, and sprint index：no matches。

## Review finding 处理记录

- Prior #419 guardian findings correctly rejected both `partial_result + parse_failed` success evidence and `platform_failed + items` runtime exceptions.
- This Work Item resolves the underlying contract gap by adding a comment-specific success sentinel without weakening fail-closed rules.
- #436 guardian finding: formal plan did not include #432/#434 staged order; sprint truth marked #434 active without a repo-local locator; validation records lacked outcomes.
- Resolution: updated `FR-0404` plan, moved #434 to planned-next status until its own implementation worktree creates the repo-local exec-plan, and recorded concrete validation outcomes.

## 未决风险

- #419 remains blocked until #434 executable contract support is merged.

## 回滚方式

- Use a revert PR for #432 only. #417/#418 remain independently merged.

## 最近一次 checkpoint 对应的 head SHA

- `918cff01a8fa3b8488cfee747d79f07233c84691`
