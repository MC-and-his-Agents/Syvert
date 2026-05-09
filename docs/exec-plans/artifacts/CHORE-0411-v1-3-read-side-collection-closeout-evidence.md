# CHORE-0411 v1.3.0 read-side collection closeout evidence

## 目的

记录 `v1.3.0` read-side collection batch 的 release truth、GitHub issue state、PR / merge commit 对账和 deferred boundary。

## Work Item

- Issue：`#411`
- item_key：`CHORE-0411-v1-3-read-side-collection-closeout`
- item_type：`CHORE`
- release：`v1.3.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#403`

## Gate Summary

- `#406/#408/#409/#410` 已全部合入并关闭。
- `#403` 的 formal spec、runtime、consumer 与 evidence truth 已齐备。
- `v1.3.0` annotated tag 与 GitHub Release 已创建。
- `docs/releases/v1.3.0.md` 与 `docs/sprints/2026-S25.md` 已回写 closeout truth。
- Phase `#381`、`#404`、`#405` 保持 open，不被 `v1.3.0` 隐式关闭。

## Gate Item Matrix

| gate_id | required | status | 结论 | evidence refs |
| --- | ---: | --- | --- | --- |
| `formal_spec` | yes | pass | `FR-0403` formal spec suite 已冻结。 | PR `#407` |
| `runtime_carrier` | yes | pass | collection runtime carrier 已合入。 | PR `#412` |
| `consumer_migration` | yes | pass | TaskRecord / runtime / compatibility consumers 已迁移。 | PR `#413` |
| `evidence_artifact` | yes | pass | sanitized evidence artifact 与 replay test 已合入。 | PR `#414` |
| `stable_baseline` | yes | pass | `content_detail_by_url` baseline 未漂移。 | `tests.runtime.test_cli_http_same_path`、`tests.runtime.test_real_adapter_regression` |
| `release_truth_alignment` | yes | pass | `v1.3.0` tag、GitHub Release、release index 与 sprint index 已对齐。 | `docs/releases/v1.3.0.md`、`gh release view v1.3.0` |
| `deferred_boundary` | yes | pass | Phase `#381` 与 `#404/#405` 仍 open / deferred。 | GitHub issues `#381`、`#404`、`#405` |

## PR / Main 对账

- PR `#407` merge commit：`d8abb3fe5b57c4b563d5f58ea420f7479bbf2e57`
- PR `#412` merge commit：`672e1c2d1e489089c670f0c09fe991b2924976d4`
- PR `#413` merge commit：`6565f13dac14a8bf9bb3ae7241ed9ada33b0bd20`
- PR `#414` merge commit：`3fbb7f862257e122bd323dd650abcf7457814a91`
- release tag object：`6d160896800ef46594dac4a28dcc84500628ec32`
- release tag target：`3fbb7f862257e122bd323dd650abcf7457814a91`
- GitHub Release：`https://github.com/MC-and-his-Agents/Syvert/releases/tag/v1.3.0`

## GitHub Issue 状态

| Issue | Role | State |
| --- | --- | --- |
| `#381` | Phase | open |
| `#403` | FR | closeout pending current Work Item |
| `#404` | deferred FR | open |
| `#405` | deferred FR | open |
| `#406` | spec Work Item | closed completed |
| `#408` | runtime Work Item | closed completed |
| `#409` | consumer Work Item | closed completed |
| `#410` | evidence Work Item | closed completed |
| `#411` | closeout Work Item | in progress |

## 完成语义

`v1.3.0` 完成后满足：

- `v1.3.0` annotated tag 指向 `#410` 合入后的主干提交 `3fbb7f862257e122bd323dd650abcf7457814a91`
- GitHub Release `v1.3.0` 已存在且非 draft / non-prerelease
- `docs/releases/v1.3.0.md` 已回写 published truth carrier
- `docs/sprints/2026-S25.md` 已回写 closeout truth
- `#403` 与 `#411` 可在 closeout PR 合入后关闭
- Phase `#381`、`#404`、`#405` 继续保持 open
