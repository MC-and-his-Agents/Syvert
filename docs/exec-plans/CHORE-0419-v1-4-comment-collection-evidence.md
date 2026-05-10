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
- Preserved `content_detail_by_url` and `FR-0403` collection behavior as regression references only.

## 验证记录

- `python3 -m unittest tests.runtime.test_comment_collection_evidence tests.runtime.test_comment_collection tests.runtime.test_read_side_collection_evidence`（31 tests）
- `python3 -m unittest tests.runtime.test_comment_collection tests.runtime.test_comment_collection_evidence tests.runtime.test_runtime tests.runtime.test_operation_taxonomy_admission_evidence tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_task_record tests.runtime.test_read_side_collection_evidence tests.runtime.test_platform_leakage tests.runtime.test_cli_http_same_path tests.runtime.test_real_adapter_regression`（338 tests）
- `python3 -m py_compile tests/runtime/test_comment_collection_evidence.py`
- `git diff --check`
- `python3 scripts/spec_guard.py --mode ci --base-sha 918cff01a8fa3b8488cfee747d79f07233c84691 --head-sha HEAD`
- `python3 scripts/governance_gate.py --mode ci --base-sha 918cff01a8fa3b8488cfee747d79f07233c84691 --head-sha HEAD --head-ref issue-419-404-v1-4-0-comment-collection-evidence`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/version_guard.py --mode ci`

## Review finding 处理记录

- 尚无 PR guardian finding。

## 未决风险

- The evidence artifact uses sanitized alias families and synthetic derivations; raw payload files remain intentionally out of repo scope.
- Release closeout and published truth remain owned by #420.

## 回滚方式

- Use a revert PR for this Work Item only. #417 runtime carrier and #418 consumer migration remain independently merged.

## 最近一次 checkpoint 对应的 head SHA

- `918cff01a8fa3b8488cfee747d79f07233c84691`
