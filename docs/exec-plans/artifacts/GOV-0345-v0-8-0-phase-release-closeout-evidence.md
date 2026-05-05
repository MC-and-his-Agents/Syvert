# GOV-0345 v0.8.0 phase and release closeout evidence

## 目的

本文档记录 `v0.8.0` final Phase / release closeout 的可复验 GitHub、Git、主干路径和验证证据。它不新增 runtime、formal spec、Adapter 或 Provider 语义。

## Work Item

- Issue：`#345`
- item_key：`GOV-0345-v0-8-0-phase-release-closeout-record`
- item_type：`GOV`
- release：`v0.8.0`
- sprint：`2026-S21`
- Parent Phase：`#293`

## 可复验入口

- Issue truth：`gh api repos/MC-and-his-Agents/Syvert/issues/<issue> --jq '{number,title,state,state_reason,closed_at}'`
- PR truth：`gh api repos/MC-and-his-Agents/Syvert/pulls/<pr> --jq '{number,state,merged,merged_at,merge_commit_sha,head:.head.ref,base:.base.ref}'`
- Open PR truth：`gh api 'repos/MC-and-his-Agents/Syvert/pulls?state=open&per_page=100'`
- Main truth：`git rev-parse HEAD && git rev-parse origin/main`
- Remote branch truth：`git ls-remote --heads origin 'issue-312*' 'issue-322*' 'issue-327*'`
- Worktree truth：`git worktree list --porcelain`
- Tag truth：`git tag --list 'v0.8.0*'`、`git rev-parse v0.8.0`、`git rev-parse v0.8.0^{}` and `git ls-remote --tags origin 'v0.8.0*'`
- GitHub Release truth：`gh release view v0.8.0 --repo MC-and-his-Agents/Syvert --json tagName,name,url,isDraft,isPrerelease,publishedAt,targetCommitish`

## GitHub issue 状态

| Issue | Role | State | Closed at |
| --- | --- | --- | --- |
| `#293` | Phase `v0.8.0` | closed completed | `2026-05-05T10:22:32Z` |
| `#294` | `FR-0027` | closed completed | `2026-04-30T09:06:01Z` |
| `#295` | `FR-0023` | closed completed | `2026-05-05T10:11:10Z` |
| `#296` | `FR-0024` | closed completed | `2026-05-03T13:02:59Z` |
| `#297` | `FR-0025` | closed completed | `2026-05-05T09:10:50Z` |
| `#298` | `FR-0026` | closed completed | `2026-05-05T08:05:29Z` |
| `#312` | `FR-0023` parent closeout | closed completed | `2026-05-05T10:05:15Z` |
| `#322` | `FR-0025` parent closeout | closed completed | `2026-05-05T09:07:54Z` |
| `#327` | `FR-0026` parent closeout | closed completed | `2026-05-05T08:04:24Z` |

## PR / main 对账

| PR | Work Item | Head branch | Merge commit | Merged at |
| --- | --- | --- | --- | --- |
| `#342` | `#327` | `issue-327-fr-0026` | `c0dc5bc77bca97a738549ef43f6fab6d560c9653` | `2026-05-05T08:04:23Z` |
| `#343` | `#322` | `issue-322-fr-0025` | `c154f414428cc4a198b24e9c79fa32131d88b3d9` | `2026-05-05T09:07:53Z` |
| `#344` | `#312` | `issue-312-fr-0023` | `594231b9f18a459bc64b771c486b73808ecaf764` | `2026-05-05T10:05:14Z` |

对账结论：

- 阶段 A 前 `HEAD == origin/main == 594231b9f18a459bc64b771c486b73808ecaf764`。
- 阶段 A PR `#346` 已合入，merge commit `741dd02e51940a80bdc8bc298422296bd5c4d4d0`。
- 当前 published anchor 为 `v0.8.0` tag target `741dd02e51940a80bdc8bc298422296bd5c4d4d0`；阶段 B 回写本 published truth。
- `issue-312-fr-0023`、`issue-322-fr-0025`、`issue-327-fr-0026` 远端分支查询无输出；REST branch lookup 为 404。
- `git fetch --prune origin` 后本地 remote-tracking refs 已清理。
- `v0.8.0` annotated tag 已创建并推送，tag object `8e58f12d371a97c0d75deeba6f3e403a067ba08e`，tag target `741dd02e51940a80bdc8bc298422296bd5c4d4d0`。
- GitHub Release `v0.8.0` 已创建：`https://github.com/MC-and-his-Agents/Syvert/releases/tag/v0.8.0`。
- `git worktree list --porcelain` 只剩主仓 `main` worktree。

## Phase closeout comment

Phase `#293` 已有 final closeout comment，创建时间 `2026-05-05T10:20:23Z`。评论记录：

- `#291` 开放 Adapter 与 provider 兼容性路线校准已完成。
- `#294 / FR-0027` 多模式资源依赖声明与匹配契约已完成。
- `#295 / FR-0023` 第三方 Adapter 稳定接入路径已完成。
- `#296 / FR-0024` Adapter capability requirement 声明契约已完成。
- `#297 / FR-0025` Provider capability offer 声明契约已完成。
- `#298 / FR-0026` Adapter x Provider compatibility decision 与 fail-closed 边界已完成。
- 主干 truth 为 `594231b9f18a459bc64b771c486b73808ecaf764`。
- 边界确认：不声明真实 provider 产品正式支持，不引入 Core provider discovery / routing / selector / marketplace。

Phase `#293` 随后于 `2026-05-05T10:22:32Z` 关闭为 `completed`。

## FR-0026 Post-Merge GitHub Closeout 协议补录

本节补录 `#327 / PR #342` 合入后的 GitHub 状态对账动作，作为 `CHORE-0327` historical closeout carrier 的补充证据。同一协议已同步补入 `docs/exec-plans/artifacts/CHORE-0327-fr-0026-parent-closeout-evidence.md`；`GOV-0345` 不回写 `docs/exec-plans/CHORE-0327-fr-0026-parent-closeout.md`，因为当前执行回合绑定 `#345`，跨 Work Item 改写 `#327` exec-plan 会违反事项 ownership。

1. 快进本地主干并确认 PR truth：
   - `git -C /Users/mc/dev/Syvert status --short --branch`
   - 期望：主仓 worktree 干净；若存在无关本地改动，先停止并人工确认，不得覆盖。
   - `git -C /Users/mc/dev/Syvert switch main`
   - `git -C /Users/mc/dev/Syvert fetch origin main --prune`
   - `git -C /Users/mc/dev/Syvert merge --ff-only origin/main`
   - `gh api repos/MC-and-his-Agents/Syvert/pulls/342 --jq '{number,state,merged,merged_at,merge_commit_sha,head:.head.sha}'`
   - 实际结果：`merged=true`，`state=closed`，`merge_commit_sha=c0dc5bc77bca97a738549ef43f6fab6d560c9653`，`merged_at=2026-05-05T08:04:23Z`。
2. 确认 Work Item truth：
   - `gh api repos/MC-and-his-Agents/Syvert/issues/327 --jq '{number,state,state_reason,closed_at,title}'`
   - 实际结果：`state=closed`，`state_reason=completed`，`closed_at=2026-05-05T08:04:24Z`。
3. 在父 FR `#298` 写入 closeout comment：
   - `gh api repos/MC-and-his-Agents/Syvert/issues/298/comments -f body='<FR-0026 closeout comment>'`
   - 实际写入时间：`2026-05-05T08:05:15Z`
   - Comment body：

```text
FR-0026 closeout 已完成。

对账范围：
- #323 / PR #333：formal spec 已合入主干。
- #324 / PR #339：compatibility decision runtime 已合入主干。
- #325 / PR #340：provider no-leakage guards 已合入主干。
- #326 / PR #341：SDK docs / evidence 已合入主干。
- #327 / PR #342：父事项 closeout evidence 已合入主干。

主干 truth：origin/main 已快进到 c0dc5bc77bca97a738549ef43f6fab6d560c9653，包含 FR-0026 formal spec、runtime decision、no-leakage guard、SDK docs 与 evidence，以及 parent closeout artifact。

本 FR 不关闭 Phase #293；Phase closeout 仍等待 FR-0023 / FR-0025 等父项最终对账完成。
```

4. 关闭父 FR `#298`：
   - `gh api repos/MC-and-his-Agents/Syvert/issues/298 -X PATCH -f state=closed -f state_reason=completed --jq '{number,state,state_reason,closed_at}'`
   - 实际结果：`state=closed`，`state_reason=completed`，`closed_at=2026-05-05T08:05:29Z`。
5. 在 Phase `#293` 写入 progress comment：
   - `gh api repos/MC-and-his-Agents/Syvert/issues/293/comments -f body='<FR-0026 phase progress comment>'`
   - 实际写入时间：`2026-05-05T08:05:49Z`
   - Comment body：

```text
v0.8.0 Phase progress：FR-0026 / #298 已完成并关闭。

已完成链路：#323/#324/#325/#326/#327 均为 closed completed；对应 PR #333/#339/#340/#341/#342 已合入主干。当前 main truth 为 c0dc5bc77bca97a738549ef43f6fab6d560c9653。

Phase #293 继续保持 open，后续还需收口 FR-0023 / #295（#312）与 FR-0025 / #297（#322）等剩余父项对账。
```

6. 清理执行现场：
   - `git worktree remove /Users/mc/code/worktrees/syvert/issue-327-fr-0026`
   - `python3 scripts/retire_branch.py --branch issue-327-fr-0026 --strategy superseded --replaced-by origin/main --reason "PR #342 squash merged into main"`
   - 实际结果：当前 `git worktree list --porcelain` 只剩主仓 `main` worktree；`git ls-remote --heads origin 'issue-327*'` 无输出，REST branch lookup 为 404。

## 主干路径证明

`origin/main` 包含以下 v0.8.0 关键路径：

- `docs/specs/FR-0023-third-party-adapter-entry-path/spec.md`
- `docs/specs/FR-0024-adapter-capability-requirement-contract/spec.md`
- `docs/specs/FR-0025-provider-capability-offer-contract/spec.md`
- `docs/specs/FR-0026-adapter-provider-compatibility-decision/spec.md`
- `docs/specs/FR-0027-multi-profile-resource-requirement-contract/spec.md`
- `syvert/adapter_capability_requirement.py`
- `syvert/provider_capability_offer.py`
- `syvert/adapter_provider_compatibility_decision.py`
- `syvert/provider_no_leakage_guard.py`
- `tests/runtime/contract_harness/third_party_entry.py`
- `adapter-sdk.md`
- `docs/exec-plans/artifacts/CHORE-0312-fr-0023-parent-closeout-evidence.md`
- `docs/exec-plans/artifacts/CHORE-0322-fr-0025-parent-closeout-evidence.md`
- `docs/exec-plans/artifacts/CHORE-0327-fr-0026-parent-closeout-evidence.md`

## 验证摘要

- `python3 -m unittest tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_adapter_capability_requirement tests.runtime.test_reference_adapter_capability_requirement_baseline tests.runtime.test_provider_capability_offer tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard`
  - 结果：通过，`Ran 145 tests`。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `git tag --list 'v0.8.0*'`
  - 阶段 A 前结果：无输出。
- `gh release view v0.8.0 --repo MC-and-his-Agents/Syvert --json tagName,name,url,isDraft,isPrerelease,publishedAt,targetCommitish`
  - 阶段 A 前结果：无 GitHub Release `v0.8.0`。
- `git rev-parse v0.8.0 && git rev-parse v0.8.0^{}`
  - 结果：tag object `8e58f12d371a97c0d75deeba6f3e403a067ba08e`，target commit `741dd02e51940a80bdc8bc298422296bd5c4d4d0`。
- `gh release view v0.8.0 --repo MC-and-his-Agents/Syvert --json tagName,name,url,isDraft,isPrerelease,publishedAt,targetCommitish`
  - 结果：`tagName=v0.8.0`，`isDraft=false`，`isPrerelease=false`，`publishedAt=2026-05-05T14:42:01Z`，`targetCommitish=741dd02e51940a80bdc8bc298422296bd5c4d4d0`，URL `https://github.com/MC-and-his-Agents/Syvert/releases/tag/v0.8.0`。

## 完成语义

`v0.8.0` 已完成：

- 开放 Adapter 接入路径的 formal spec、contract test entry、SDK docs 与 parent closeout。
- Adapter capability requirement 与 Provider capability offer 的声明契约、validator、SDK docs 与 evidence。
- Adapter requirement x Provider offer 的 compatibility decision、runtime decision、fail-closed、no-leakage guard、SDK docs 与 evidence。
- multi-profile resource requirement contract、双参考 profile evidence、matcher runtime 与 reference adapter declaration migration。
- 父项 closeout 与 Phase closeout GitHub 状态对账。
- 阶段 A carrier 已合入，`v0.8.0` tag / GitHub Release 已建立；阶段 B 回写 published truth。

## 明确不完成

- 不正式支持任何指定外部 provider 产品。
- 不引入 Core provider registry、provider selector、provider fallback priority 或 provider marketplace。
- 不承诺某一个 provider 覆盖所有 Adapter capability。
- 不把 provider identity 写入 Core routing、TaskRecord、resource lifecycle 或 registry discovery。

## 后续消费

- `v0.9.0` 可在本版本冻结的 compatibility decision 模型上执行真实 provider sample。
- 任何真实 provider 产品支持、provider selector / fallback、provider marketplace 或跨 provider ranking 都必须通过独立 FR 批准。
