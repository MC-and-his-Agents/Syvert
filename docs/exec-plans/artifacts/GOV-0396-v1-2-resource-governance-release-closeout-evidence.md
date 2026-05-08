# GOV-0396 v1.2 Resource Governance Release Closeout Evidence

## 目的

记录 `v1.2.0` Resource Governance Foundation 的可复验 GitHub、Git、主干路径和 gate evidence。

## Work Item

- Issue：`#396`
- item_key：`GOV-0396-v1-2-resource-governance-release-closeout`
- item_type：`GOV`
- release：`v1.2.0`
- sprint：`2026-S24`
- Parent Phase：`#380`
- Parent FR：`#387`

## Gate Summary

当前阶段 A carrier 建立以下 release truth 输入：

- `#388/#390/#391/#392` 均已合入并关闭为 completed。
- `v1.1.0` taxonomy 已发布，resource governance 使用其 stable context 作为 admission 输入。
- `account` / `proxy` lifecycle regression 保持通过。
- 小红书 `content_detail_by_url` 账号会话场景证明 credential/session stale、invalid、unknown 不能继续只由 opaque material 表达。
- `v1.2.0` annotated tag 与 GitHub Release 待阶段 A carrier 合入后创建。
- `docs/releases/v1.2.0.md` 阶段 B 将回写 published truth carrier。

## Gate Item Matrix

| gate_id | required | status | 结论 | evidence refs |
| --- | ---: | --- | --- | --- |
| `formal_spec` | yes | pass | FR-0387 formal spec suite 已合入。 | PR `#389` |
| `runtime_carrier` | yes | pass | `CredentialMaterial`、`SessionHealth`、`ResourceHealthEvidence`、health admission 与 active lease invalidation helper 已合入。 | PR `#393`、`syvert/resource_health.py` |
| `consumer_boundary` | yes | pass | Requirement / Offer / Compatibility decision / no-leakage guard 禁止 credential/session/private health public metadata。 | PR `#394` |
| `evidence_artifact` | yes | pass | 健康准入、stale/unknown fail-closed、invalid_contract、pre-admission invalid、active invalidation 与 public projection redaction 可复验。 | PR `#395`、`docs/exec-plans/artifacts/CHORE-0392-v1-2-resource-governance-evidence.md` |
| `stable_baseline` | yes | pass | `content_detail_by_url` baseline 未漂移。 | `tests.runtime.test_real_adapter_regression` |
| `resource_lifecycle` | yes | pass | `account` / `proxy` lifecycle、store、trace、bootstrap 回归通过。 | `tests.runtime.test_resource_lifecycle*` |
| `platform_leakage` | yes | pass | Credential/session/private health 字段进入 provider/platform no-leakage scan coverage。 | `tests.runtime.test_provider_no_leakage_guard`、`tests.runtime.test_platform_leakage` |
| `release_truth_alignment` | yes | pending | 阶段 A 合入后创建 tag / GitHub Release；阶段 B 回写 published truth carrier。 | `docs/releases/v1.2.0.md` |

## PR / Main 对账

- PR `#389` merge commit：`fda3849dd25988993c6e2ae39a5e0a0bf479beef`
- PR `#393` merge commit：`2a7aed56d62285e9d44371061d3d768e0b04f76e`
- PR `#394` merge commit：`d1fe72019d25c7393a5eb3068162926a2b8f08bc`
- PR `#395` merge commit：`eaec42d70ed432b7334eab19ef5ec5f69544f855`
- 阶段 A carrier base：`eaec42d70ed432b7334eab19ef5ec5f69544f855`
- 阶段 A PR：TBD
- `v1.2.0` annotated tag object：TBD
- `v1.2.0` tag target：TBD
- GitHub Release：TBD

## GitHub Issue 状态

| Issue | Role | State |
| --- | --- | --- |
| `#380` | Phase | open before final closeout |
| `#387` | FR | open before final closeout |
| `#388` | Formal spec Work Item | closed completed |
| `#390` | Runtime Work Item | closed completed |
| `#391` | Consumer boundary Work Item | closed completed |
| `#392` | Evidence Work Item | closed completed |
| `#396` | Release closeout Work Item | open before final closeout |

## 完成语义

`v1.2.0` 完成后应满足：

- `v1.2.0` annotated tag 指向包含阶段 A carrier 的 main commit。
- GitHub Release `v1.2.0` 存在且非 draft / non-prerelease。
- `docs/releases/v1.2.0.md` 阶段 B 已回写 tag object、tag target、release URL 与 publish time。
- Phase `#380`、FR `#387` 与 Work Item `#396` 将在阶段 B PR 合入后关闭为 completed。
