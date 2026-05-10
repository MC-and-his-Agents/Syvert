# CHORE-0420 v1.4 comment collection closeout

## 关联信息

- item_key：`CHORE-0420-v1-4-comment-collection-closeout`
- Issue：`#420`
- item_type：`CHORE`
- release：`v1.4.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#404`
- 关联 spec：`docs/specs/FR-0404-comment-collection-contract/`
- 关联 PR：`#438`
- 状态：`active`
- active 收口事项：`CHORE-0420-v1-4-comment-collection-closeout`

## 目标

- Work Item: #420
- Parent FR: #404
- Scope: release/sprint/FR closeout truth, published truth carrier, and GitHub issue reconciliation for `v1.4.0`.
- Out of scope: runtime contract changes, evidence semantics changes, #405 creator/media execution, Phase #381 closeout.

## 改动记录

- Recorded `v1.4.0` annotated tag, tag target, GitHub Release URL, and published timestamp.
- Added closeout evidence artifact for the #404 work-item/PR/merge matrix.
- Updated sprint truth from active `v1.4.0` to published `v1.4.0`.
- Kept Phase #381 open and #405 deferred/planning-only.

## 验证记录

- `git diff --check`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/version_guard.py --mode ci`
- `python3 scripts/governance_gate.py --mode ci --base-sha 2b40b9195b08d22c84ad9cbe472ff647e118c1aa --head-sha HEAD --head-ref issue-420-404-v1-4-0-comment-collection-closeout`
- release truth checked with `git rev-parse v1.4.0^{tag}`, `git rev-parse v1.4.0^{}`, and `gh release view v1.4.0 --json tagName,url,publishedAt,targetCommitish`

## Review finding 处理记录

- PR `#438` created; guardian finding state pending.

## 未决风险

- #405 remains deferred and is not part of `v1.4.0`.
- Phase #381 remains open for later Phase 3 work.

## 回滚方式

- Release rollback must follow `docs/process/version-management.md`; do not delete published tags/releases without an explicit rollback Work Item.

## 最近一次 checkpoint 对应的 head SHA

- `2b40b9195b08d22c84ad9cbe472ff647e118c1aa`
