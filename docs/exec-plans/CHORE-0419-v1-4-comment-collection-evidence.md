# CHORE-0419 v1.4 comment collection evidence

## 关联信息

- item_key：`CHORE-0419-v1-4-comment-collection-evidence`
- Issue：`#419`
- item_type：`CHORE`
- release：`v1.4.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#404`
- 关联 spec：`docs/specs/FR-0404-comment-collection-contract/`
- 关联 PR：
- 状态：`active`
- active 收口事项：`CHORE-0419-v1-4-comment-collection-evidence`

## 目标

- Work Item: #419
- Parent FR: #404
- Scope: sanitized fake/reference evidence artifact, replay test, leakage guard, and regression evidence for `comment_collection`.
- Out of scope: runtime carrier changes, consumer migration, #405 creator/media work, release tag, GitHub Release, and #420 closeout.

## 改动记录

- Added a replayable evidence artifact for `comment_collection` covering top-level pages, next page, reply hierarchy, visibility states, fail-closed boundaries, duplicate item rejection, cursor invalidation, partial result, and total parse failure.
- Added a runtime evidence test that rebuilds the artifact JSON snapshot from public comment collection contract helpers.
- Added artifact sanitization assertions to prevent raw payloads, external source names, local paths, and private sample project identifiers from entering repository truth.
- Consumed the `comment_collection` non-empty `complete` success carrier path with `error_classification=success`, so normal top-level/reply/visibility pages are not represented as parse-failure evidence.
- Derived baseline booleans from actual `content_detail_by_url` and `FR-0403` replay suites.
- Preserved `content_detail_by_url` and `FR-0403` collection behavior as regression references only.

## 验证记录

- `python3 -m unittest tests.runtime.test_comment_collection_evidence tests.runtime.test_comment_collection tests.runtime.test_read_side_collection_evidence`（31 tests）
- `python3 -m unittest tests.runtime.test_comment_collection_evidence tests.runtime.test_comment_collection`（33 tests）
- `python3 -m unittest tests.runtime.test_comment_collection tests.runtime.test_comment_collection_evidence tests.runtime.test_runtime tests.runtime.test_operation_taxonomy_admission_evidence tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_task_record tests.runtime.test_read_side_collection_evidence tests.runtime.test_platform_leakage tests.runtime.test_cli_http_same_path tests.runtime.test_real_adapter_regression`（340 tests）
- `python3 -m py_compile syvert/read_side_collection.py tests/runtime/test_comment_collection.py tests/runtime/test_comment_collection_evidence.py`
- `git diff --check`
- `python3 scripts/spec_guard.py --mode ci --base-sha ac421426eb5f5a4bce1ea5d0ed908962a05b6e5f --head-sha HEAD`
- `python3 scripts/governance_gate.py --mode ci --base-sha ac421426eb5f5a4bce1ea5d0ed908962a05b6e5f --head-sha HEAD --head-ref issue-419-404-v1-4-0-comment-collection-evidence`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/version_guard.py --mode ci`

## Review finding 处理记录

- PR #431 guardian finding：normal top-level, next-page, reply hierarchy and visibility scenarios were represented as `partial_result + parse_failed`.
- 处理结果：consumed the #432/#434 `comment_collection` non-empty complete success support with `error_classification=success`, updated evidence scenarios/artifact to use `complete + success`, and kept `partial_result + parse_failed` only in the dedicated parse-failure scenario.
- PR #431 guardian finding：baseline regression booleans were hard-coded constants.
- 处理结果：the evidence report now derives `content_detail_by_url_unchanged` and `fr_0403_collection_behavior_unchanged` from their replay suites.

## 未决风险

- The evidence artifact uses sanitized alias families and synthetic derivations; raw payload files remain intentionally out of repo scope.
- Release closeout and published truth remain owned by #420.

## 回滚方式

- Use a revert PR for this Work Item only. #417 runtime carrier and #418 consumer migration remain independently merged.

## 最近一次 checkpoint 对应的 head SHA

- `ac421426eb5f5a4bce1ea5d0ed908962a05b6e5f`
