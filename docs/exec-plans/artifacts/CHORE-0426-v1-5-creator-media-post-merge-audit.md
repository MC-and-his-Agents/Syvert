# CHORE-0426 v1.5 creator media post-merge audit

## Audit Summary

- release：`v1.5.0`
- fr_ref：`FR-0405`
- work_item_ref：`#426 / CHORE-0426-v1-5-creator-media-closeout`
- governing_spec_ref：`docs/specs/FR-0405-creator-profile-media-asset-read-contract/`
- audit_scope：`#439`、`#440`、`#441`
- merged_main_head：`508c5a5223d75169f374a7db4c15dd7a825702fd`
- verdict：`no blocker reproduced on merged main`

## Provenance

| PR | Merge commit | mergedAt (UTC) | Scope | Merge path |
| --- | --- | --- | --- | --- |
| `#439` | `e2e62f8667784d0b746a6c086f259c5268d8430c` | `2026-05-10T13:42:57Z` | media asset fetch runtime carrier | manual static review + `gh pr merge --squash --match-head-commit` |
| `#440` | `005329da83fe299ff0996099901999117c4f770d` | `2026-05-10T14:17:55Z` | creator profile runtime carrier | manual static review + `gh pr merge --squash --match-head-commit` |
| `#441` | `508c5a5223d75169f374a7db4c15dd7a825702fd` | `2026-05-10T14:30:42Z` | creator/media consumer migration proof | manual static review + `gh pr merge --squash --match-head-commit` |

## Guardian Gap

- 本地曾尝试运行 `python3 scripts/pr_guardian.py review 439`。
- 观察到 guardian 会在内部再起一层 `codex exec`，当前环境里该子进程未稳定产出结构化 verdict。
- 因此这三次 merge 未通过仓库标准的 `scripts/pr_guardian.py merge-if-safe` 完整入口。
- 本 artifact 不把上述事实重写为“标准 guardian provenance 已满足”；它只记录实际执行路径。

## Post-Merge Regression Snapshot

- first local `main` used for spot-check was stale at `05c4bfb2f57a533a637e0659e4054e21b8e86f5` and did not include `#439/#440/#441`.
- authoritative audit reran on detached worktree `/tmp/syvert-postmerge-audit.hJQM5O` at `origin/main@508c5a5223d75169f374a7db4c15dd7a825702fd`.

| command | scope | result |
| --- | --- | --- |
| `python3 -m unittest tests.runtime.test_operation_taxonomy tests.runtime.test_runtime tests.runtime.test_task_record tests.runtime.test_platform_leakage` | runtime carrier / durable truth / leakage | `311 tests OK` |
| `python3 -m unittest tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_http_api tests.runtime.test_cli` | requirement / offer / compatibility / CLI / HTTP result consumers | `177 tests OK` |

## Interpretation

- `#439`、`#440`、`#441` 在 merged `origin/main` 上没有复现 shared runtime regression。
- creator/media public carriers 没有在 merged `origin/main` 上表现出与 FR-0405 明显冲突的 runtime / TaskRecord / consumer drift。
- `#441` 证明 compatibility decision 继续只消费 requirement / offer inputs，creator/media result envelopes 没有被引入 compatibility decision consumer path。

## Rollback Thresholds

Only open a remediation / revert Work Item when at least one of the following becomes true on merged `origin/main`:

- shared runtime regression is reproducible for `creator_profile_by_id` or `media_asset_fetch_by_ref`
- creator/media public contract diverges from `FR-0405`
- CLI / HTTP / result query re-wraps creator/media terminal envelopes or drifts public fields
- compatibility decision reads result carriers instead of requirement / offer inputs

## Residual Risk

- This audit reduces code-quality uncertainty for `#439/#440/#441`, but does not prove `v1.5.0` release readiness.
- `#425` evidence and `#426` final closeout still remain open.
- `governance_gate` is not a meaningful post-merge quality signal on the detached audit worktree because it intentionally fails closed without an issue-scoped `head-ref`.
