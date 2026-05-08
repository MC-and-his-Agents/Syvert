# GOV-0360 v0.9.0 release closeout evidence

## 目的

本文档记录 `v0.9.0` release closeout 的可复验 GitHub、Git、主干路径和验证证据。它不新增 runtime、formal spec、Adapter 或 Provider 语义。

## Work Item

- Issue：`#360`
- item_key：`GOV-0360-v0-9-0-release-closeout-record`
- item_type：`GOV`
- release：`v0.9.0`
- sprint：`2026-S22`
- Parent Phase：`#354`
- Parent FR：`#355`

## 可复验入口

- Issue truth：`gh api repos/MC-and-his-Agents/Syvert/issues/<issue> --jq '{number,title,state,state_reason,closed_at}'`
- PR truth：`gh api repos/MC-and-his-Agents/Syvert/pulls/<pr> --jq '{number,state,merged,merged_at,merge_commit_sha,head:.head.ref,head_sha:.head.sha}'`
- Main truth：`git rev-parse HEAD && git rev-parse origin/main`
- Tag truth：`git tag --list 'v0.9.0*'`、`git rev-parse v0.9.0`、`git rev-parse v0.9.0^{}`、`git ls-remote --tags origin 'v0.9.0*'`
- GitHub Release truth：`gh release view v0.9.0 --repo MC-and-his-Agents/Syvert --json tagName,name,url,isDraft,isPrerelease,publishedAt,targetCommitish`
- Worktree truth：`git worktree list --porcelain`
- Retired branch truth：`git ls-remote origin refs/heads/issue-358-v0-9-0-external-provider-sample-evidence refs/tags/archive/branches/issue-358-v0-9-0-external-provider-sample-evidence`

## GitHub issue 状态

| Issue | Role | State | Closed at |
| --- | --- | --- | --- |
| `#354` | Phase `v0.9.0` | open | pending |
| `#355` | FR `v0.9.0 real provider compatibility evidence` | open | pending |
| `#356` | formal spec Work Item | closed completed | `2026-05-08T02:07:05Z` |
| `#358` | implementation evidence Work Item | closed completed | `2026-05-08T06:30:34Z` |
| `#360` | release closeout Work Item | open | pending |

## PR / main 对账

| PR | Work Item | Head branch | Merge commit | Merged at |
| --- | --- | --- | --- | --- |
| `#357` | `#356` | `issue-356-v0-9-0-provider-compatibility-formal-spec` | `5d505179f3ea4d0508e913e407f39b4c73ba8874` | `2026-05-08T02:07:04Z` |
| `#359` | `#358` | `issue-358-v0-9-0-external-provider-sample-evidence` | `ecfc3bf53299191e42c13c5b1c6578fd90aa84b6` | `2026-05-08T06:30:33Z` |

对账结论：

- 阶段 A 前 main truth 为 `ecfc3bf53299191e42c13c5b1c6578fd90aa84b6`。
- Work Item `#356/#358` 已关闭为 `closed completed`。
- PR `#357/#359` 已合入 main。
- Work Item `#358` 的分支与 worktree 已退役，archive tag 为 `archive/branches/issue-358-v0-9-0-external-provider-sample-evidence`。
- 阶段 A carrier PR `#361` 已合入，merge commit `870899ac4d8d4cb1713f52a3a98180a6787ec0f9`。
- 阶段 B published truth 回写 PR `#362` 已创建，当前回写本 published truth carrier。
- `v0.9.0` annotated tag 已创建并推送，tag object `d08d5884edb26c5a0112028f4e8a48adcac241eb`，tag target `870899ac4d8d4cb1713f52a3a98180a6787ec0f9`。
- GitHub Release `v0.9.0` 已创建：`https://github.com/MC-and-his-Agents/Syvert/releases/tag/v0.9.0`。

`#358` 分支 / worktree 退役复验：

- `git ls-remote origin refs/heads/issue-358-v0-9-0-external-provider-sample-evidence refs/tags/archive/branches/issue-358-v0-9-0-external-provider-sample-evidence`
  - 结果：远端分支无输出；archive tag 为 `93be68d81ddcfff3de867a1b7210c54a855c033b refs/tags/archive/branches/issue-358-v0-9-0-external-provider-sample-evidence`。
- `git worktree list --porcelain`
  - 结果：仅主仓 `main` worktree 与当前 `#360` release closeout worktree；不存在 `issue-358-v0-9-0-external-provider-sample-evidence` worktree。

## 主干路径证明

`origin/main` 包含以下 v0.9.0 关键路径：

- `docs/specs/FR-0355-v0-9-real-provider-compatibility-evidence/spec.md`
- `docs/specs/FR-0351-v1-core-stable-release-gate/spec.md`
- `docs/exec-plans/CHORE-0356-v0-9-provider-compatibility-spec.md`
- `docs/exec-plans/CHORE-0358-v0-9-external-provider-sample-evidence.md`
- `docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md`
- `docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-validation.json`
- `syvert/real_provider_sample_evidence.py`
- `syvert/fixtures/v0_9_external_provider_sample_manifest.json`
- `syvert/fixtures/v0_9_external_provider_sample_provenance.json`
- `tests/runtime/test_real_provider_sample_evidence.py`

## 验证摘要

- `python3 -m py_compile syvert/real_provider_sample_evidence.py tests/runtime/test_real_provider_sample_evidence.py`
  - 结果：通过。
- `python3 -m unittest tests.runtime.test_real_provider_sample_evidence`
  - 结果：通过，`Ran 21 tests`。
- `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard tests.runtime.test_real_provider_sample_evidence`
  - 结果：通过，`Ran 72 tests`。
- `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_cli_http_same_path`
  - 结果：通过，`Ran 79 tests`。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/version_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`docs`，变更类别=`docs`。
- `git rev-parse v0.9.0 && git rev-parse v0.9.0^{}`
  - 结果：tag object `d08d5884edb26c5a0112028f4e8a48adcac241eb`，target commit `870899ac4d8d4cb1713f52a3a98180a6787ec0f9`。
- `git ls-remote --tags origin 'v0.9.0*'`
  - 结果：远端存在 `v0.9.0` annotated tag 与 dereferenced target。
- `gh release view v0.9.0 --repo MC-and-his-Agents/Syvert --json tagName,name,url,isDraft,isPrerelease,publishedAt,targetCommitish`
  - 结果：`tagName=v0.9.0`，`name=v0.9.0`，`isDraft=false`，`isPrerelease=false`，`publishedAt=2026-05-08T06:55:31Z`，`targetCommitish=870899ac4d8d4cb1713f52a3a98180a6787ec0f9`，URL `https://github.com/MC-and-his-Agents/Syvert/releases/tag/v0.9.0`。

## 完成语义

`v0.9.0` 已在 implementation truth 中完成：

- `FR-0355` formal spec。
- external provider sample manifest / provenance fixture。
- Adapter-bound execution evidence。
- provider no-leakage evidence。
- validation evidence carrier，可被 `FR-0351:provider_compatibility_sample` 消费。

## 明确不完成

- 不正式支持任何指定 provider 产品。
- 不引入 provider selector、fallback、priority、ranking、marketplace 或 Core provider registry。
- 不扩展 search / list / comment / batch / dataset 或发布能力。
- 不发布 Python package artifact。

## 后续消费

- `v1.0.0` Core stable release gate 可消费本 release 的 provider compatibility sample evidence。
- 后续真实 provider 产品支持、写操作发布能力或 batch / dataset 能力必须通过独立 FR 批准。
