# GOV-0373 v1.1 Operation Taxonomy Release Closeout Evidence

## 目的

记录 `v1.1.0` Operation Taxonomy Foundation 的可复验 GitHub、Git、主干路径和 gate evidence。

## Work Item

- Issue：`#373`
- item_key：`GOV-0373-v1-1-operation-taxonomy-release-closeout`
- item_type：`GOV`
- release：`v1.1.0`
- sprint：`2026-S23`
- Parent Phase：`#367`
- Parent FR：`#368`

## Gate Summary

当前阶段 A carrier 建立以下 release truth 输入：

- `#369/#370/#371/#372` 均已合入并关闭为 completed。
- `content_detail_by_url` 仍是唯一 stable runtime operation。
- Proposed candidate families 未被发布为 executable runtime capability。
- `v1.1.0` tag / GitHub Release 尚未创建，需等待阶段 A carrier 合入 main。

## Gate Item Matrix

| gate_id | required | status | 结论 | evidence refs |
| --- | ---: | --- | --- | --- |
| `formal_spec` | yes | pass | FR-0368 formal spec suite 已合入。 | PR `#374` |
| `runtime_taxonomy` | yes | pass | Runtime registry、validator、stable lookup 已合入。 | PR `#375`、`syvert/operation_taxonomy.py` |
| `consumer_migration` | yes | pass | Requirement / Offer / Compatibility decision 已消费 taxonomy stable lookup。 | PR `#376` |
| `admission_evidence` | yes | pass | Proposed candidates 可表达但 fail-closed。 | PR `#377` |
| `stable_baseline` | yes | pass | `content_detail_by_url` baseline 未漂移。 | `tests.runtime.test_real_adapter_regression` |
| `platform_leakage` | yes | pass | Taxonomy field 进入 platform leakage scan coverage。 | `tests.runtime.test_platform_leakage` |
| `release_truth_alignment` | yes | pending | 阶段 A 合入后创建 tag / GitHub Release，阶段 B 回写。 | `docs/releases/v1.1.0.md` |

## PR / Main 对账

- PR `#374` merge commit：`4a4af06c7e6e6a95a11e7e3724d1acfbacb4ecd4`
- PR `#375` merge commit：`952dd7117b65f20b4df53692d03a669f0678eb7c`
- PR `#376` merge commit：`5b715296a1c5e7dd6738454bc804a79f887d3bc6`
- PR `#377` merge commit：`27712c7b416c8ff8927e79851fd3ced4ed96e845`
- 阶段 A carrier base：`27712c7b416c8ff8927e79851fd3ced4ed96e845`

## GitHub Issue 状态

| Issue | Role | State |
| --- | --- | --- |
| `#367` | Phase | open |
| `#368` | FR | open |
| `#369` | Work Item | closed completed |
| `#370` | Work Item | closed completed |
| `#371` | Work Item | closed completed |
| `#372` | Work Item | closed completed |
| `#373` | Release closeout Work Item | open |

## 完成语义

`v1.1.0` 完成后应满足：

- `v1.1.0` annotated tag 指向包含阶段 A carrier 的 main commit。
- GitHub Release `v1.1.0` 存在且非 draft / non-prerelease。
- `docs/releases/v1.1.0.md` 阶段 B 回写 tag object、tag target、release URL 与 publish time。
- Phase `#367`、FR `#368` 与 Work Item `#373` 关闭为 completed。
