# GOV-0364 v1 Core stable release closeout evidence

## 目的

本文档记录 `v1.0.0` Core stable release closeout 的可复验 GitHub、Git、主干路径和 gate evidence。它不新增 runtime、formal spec、Adapter 或 Provider 语义。

## Work Item

- Issue：`#364`
- item_key：`GOV-0364-v1-core-stable-release-closeout`
- item_type：`GOV`
- release：`v1.0.0`
- sprint：`2026-S22`
- Parent Phase：`#363`
- Gate source of truth：`docs/specs/FR-0351-v1-core-stable-release-gate/spec.md`

## 可复验入口

- Phase truth：`gh api repos/MC-and-his-Agents/Syvert/issues/363 --jq '{number,title,state,state_reason,closed_at}'`
- FR truth：`gh api repos/MC-and-his-Agents/Syvert/issues/351 --jq '{number,title,state,state_reason,closed_at}'`
- Work Item truth：`gh api repos/MC-and-his-Agents/Syvert/issues/364 --jq '{number,title,state,state_reason,closed_at}'`
- PR truth：`gh api repos/MC-and-his-Agents/Syvert/pulls/<pr> --jq '{number,state,merged,merged_at,merge_commit_sha,head:.head.ref,head_sha:.head.sha}'`
- Main truth：`git rev-parse HEAD && git rev-parse origin/main`
- Tag truth：`git tag --list 'v1.0.0*'`、`git rev-parse v1.0.0`、`git rev-parse v1.0.0^{}`、`git ls-remote --tags origin 'v1.0.0*'`
- GitHub Release truth：`gh release view v1.0.0 --repo MC-and-his-Agents/Syvert --json tagName,name,url,isDraft,isPrerelease,publishedAt,targetCommitish`
- Open PR truth：`gh api 'repos/MC-and-his-Agents/Syvert/pulls?state=open&per_page=100'`

## Gate summary

发布前 gate 汇总结论：

- 除 `release_truth_alignment` 外，`FR-0351` 的 required gate items 已具备当前主干可复验证据。
- 依据 `FR-0351` 场景 8，阶段 A 合入前只允许进入 artifact creation step，不得返回最终 `pass`。
- 最终 `overall_status=pass` 只在 `v1.0.0` release index、annotated tag、GitHub Release 与 published truth carrier 对齐后成立。

## Gate item matrix

| gate_id | required | status | 结论 | evidence refs |
| --- | ---: | --- | --- | --- |
| `core_adapter_provider_boundary` | yes | pass | Core / Adapter / Provider 边界无漂移。 | `docs/roadmap-v0-to-v1.md`、`docs/specs/FR-0351-v1-core-stable-release-gate/spec.md`、`docs/exec-plans/artifacts/GOV-0360-v0-9-0-release-closeout-evidence.md` |
| `dual_reference_baseline` | yes | pass | 双参考 `content_detail_by_url` 回归在当前主干通过。 | `tests.runtime.test_real_adapter_regression`、本工件“验证摘要” |
| `third_party_adapter_entry` | yes | pass | 第三方 Adapter-only 入口仍可独立解释。 | `tests.runtime.test_third_party_adapter_contract_entry`、`adapter-sdk.md` |
| `provider_compatibility_sample` | yes | pass | `v0.9.0` real provider sample evidence 可被消费。 | `docs/releases/v0.9.0.md`、`docs/exec-plans/artifacts/GOV-0360-v0-9-0-release-closeout-evidence.md` |
| `provider_no_leakage` | yes | pass | provider 字段未进入 Core-facing surface。 | `tests.runtime.test_provider_no_leakage_guard`、`docs/exec-plans/artifacts/GOV-0360-v0-9-0-release-closeout-evidence.md` |
| `api_cli_same_core_path` | yes | pass | API / CLI 仍共享 Core path。 | `tests.runtime.test_cli_http_same_path`、本工件“验证摘要” |
| `release_truth_alignment` | yes | fail | 当前尚未创建 `v1.0.0` tag / GitHub Release，也未回写 published truth。 | `docs/releases/v1.0.0.md`、`git tag --list 'v1.0.0*'`、`gh release view v1.0.0 ...` |
| `application_boundary` | yes | pass | `v1.0.0` 仍只声明 Core stable，不把上层应用写成 gate。 | `vision.md`、`docs/roadmap-v0-to-v1.md`、`docs/releases/v1.0.0.md` |
| `packaging_boundary` | yes | pass | Python package publish 不是默认 gate。 | `docs/process/python-packaging.md`、`docs/releases/v1.0.0.md` |

## GitHub issue 状态

| Issue | Role | State | Closed at |
| --- | --- | --- | --- |
| `#363` | Phase `v1.0.0 release closeout` | open | pending |
| `#351` | `FR-0351` gate truth | closed completed | `2026-05-08T01:41:32Z` |
| `#364` | `v1.0.0` release closeout Work Item | open | pending |

## PR / main 对账

对账结论：

- 阶段 A 前 `HEAD == origin/main == 21b30c347c11fc3e576db444cfc073108f512a35`。
- 阶段 A 前 open PR 为空。
- 当前不存在 `v1.0.0` tag 或 GitHub Release。
- `FR-0351` 与 `v0.9.0` provider sample evidence 都已在 main 上，可被 `#364` 直接消费。

## 主干路径证明

`origin/main` 包含以下 `v1.0.0` gate 关键路径：

- `docs/specs/FR-0351-v1-core-stable-release-gate/spec.md`
- `docs/specs/FR-0351-v1-core-stable-release-gate/data-model.md`
- `docs/specs/FR-0355-v0-9-real-provider-compatibility-evidence/spec.md`
- `docs/releases/v0.9.0.md`
- `docs/exec-plans/artifacts/GOV-0360-v0-9-0-release-closeout-evidence.md`
- `tests/runtime/test_real_adapter_regression.py`
- `tests/runtime/test_third_party_adapter_contract_entry.py`
- `tests/runtime/test_cli_http_same_path.py`
- `tests/runtime/test_provider_no_leakage_guard.py`
- `tests/runtime/test_real_provider_sample_evidence.py`
- `tests/runtime/test_adapter_provider_compatibility_decision.py`
- `docs/process/python-packaging.md`

## 验证摘要

- `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard tests.runtime.test_real_provider_sample_evidence`
  - 结果：通过，`Ran 72 tests`。
- `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_cli_http_same_path`
  - 结果：通过，`Ran 79 tests`。
- `python3 scripts/version_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `git rev-parse HEAD && git rev-parse origin/main`
  - 结果：均为 `21b30c347c11fc3e576db444cfc073108f512a35`。
- `git tag --list 'v1.0.0*'`
  - 结果：无输出。
- `gh release view v1.0.0 --repo MC-and-his-Agents/Syvert --json tagName,name,url,isDraft,isPrerelease,publishedAt,targetCommitish`
  - 结果：`release not found`。
- `gh api 'repos/MC-and-his-Agents/Syvert/pulls?state=open&per_page=100'`
  - 结果：`[]`。

## 完成语义

阶段 A 前，`v1.0.0` 已满足：

- Core stable release gate 的发布前 required evidence 汇总。
- `v0.9.0` provider compatibility sample evidence 的消费入口。
- 双参考回归、第三方 Adapter-only 入口、provider no-leakage 与 API / CLI same-path 的当前主干复验。
- 上层应用与 Python package publish 不属于 `v1.0.0` 默认完成条件的边界确认。

阶段 A 前，`v1.0.0` 尚未完成：

- `v1.0.0` annotated tag。
- GitHub Release `v1.0.0`。
- published truth carrier 回写。
- Phase `#363` 与 Work Item `#364` 的 final closeout。

## 后续消费

- 阶段 A PR 合入后，在其 merge commit 上创建 `v1.0.0` annotated tag 与 GitHub Release。
- 阶段 B follow-up 将把 `release_truth_alignment` 从 `fail` 回写为 `pass`，并关闭 `#363/#364`。
