# CHORE-0322 FR-0025 parent closeout evidence

## 目的

本文档汇总 `FR-0025` 父事项 closeout 所需的 GitHub provenance、主干事实、子 Work Item 状态、验证证据、风险和后续消费边界。它不定义新的 Provider offer 字段，不实现 `FR-0026`，也不把 Provider offer 的 `declared` 语义改写为 `matched`。

## 父 FR

- FR Issue：`#297`
- item_key：`FR-0025-provider-capability-offer-contract`
- release：`v0.8.0`
- sprint：`2026-S21`
- Parent Phase：`#293`

## 子 Work Item closeout 状态

| Issue | item_key | 结果 |
| --- | --- | --- |
| `#319` | `CHORE-0319-fr-0025-formal-spec-closeout` | closed completed |
| `#320` | `CHORE-0320-fr-0025-offer-manifest-validator` | closed completed |
| `#321` | `CHORE-0321-fr-0025-sdk-docs-evidence` | closed completed |
| `#322` | `CHORE-0322-fr-0025-parent-closeout` | current closeout Work Item |

## PR / Main 对账

可复验入口：

- PR truth：`gh api repos/:owner/:repo/pulls/<pr> --jq '{number,state,html_url,merged,merged_at,head:{ref:.head.ref,sha:.head.sha},base:{ref:.base.ref,sha:.base.sha},merge_commit_sha}'`
- Issue truth：`gh api repos/:owner/:repo/issues/<issue> --jq '{number,state,state_reason,title,html_url,labels:[.labels[].name],body}'`
- Main truth：`git rev-parse origin/main` 与 `git merge-base --is-ancestor <merge_commit_sha> origin/main`
- Path truth：`git cat-file -e origin/main:<path>`

| Work Item | PR | PR head | main merge commit | merged_at |
| --- | --- | --- | --- | --- |
| `#319` | `#328` | `2a6f725fd02aef1bc2f101d63f569de937cdd3cf` | `5cc4a6c4b12bfb74e852472705e8c3fb5d98ed93` | `2026-04-30T11:17:25Z` |
| `#320` | `#335` | `22b5338715225555090b3d9fcc296fe71958a8ca` | `22a3db23be36b702c6d0aed358ede7cf90a68d93` | `2026-05-02T06:26:23Z` |
| `#321` | `#338` | `0ec777f7a1fbda820028ea85b7292fba62f88500` | `107a9fb3b93864ee01ef5ea21ad4d782761fc61e` | `2026-05-03T13:39:27Z` |

对账结论：

- `#319/#320/#321` 的 PR 均已 merged，且对应 Work Item 均为 `closed completed`。
- 当前 worktree 已快进到 `origin/main=c0dc5bc77bca97a738549ef43f6fab6d560c9653`，已包含 `#319/#320/#321` 与后续 `#327` 的 main truth。
- `#328/#335/#338` 的 merge commit 均为 `origin/main` ancestor。
- `#322` 是唯一剩余的 `FR-0025` closeout Work Item，合入后即可关闭父 FR `#297`。

## GitHub 状态对账

- 父 FR `#297` 当前仍 open；它必须等待 `#322` closeout PR 合入后再 close。
- Phase `#293` 当前仍 open；本 closeout 只为 Phase closeout 提供 `FR-0025` 完成输入，不关闭 Phase。
- `#319/#320/#321` 已关闭；`#322` 当前 open，作为本轮唯一执行入口。

## Post-Merge GitHub Closeout 协议

本节固定 `#343` 合入后的 GitHub 状态对账动作。合入前不得执行 `#297` close / Phase closeout，以免 GitHub truth 早于主干 truth。

1. 快进本地主干并确认 PR truth：
   - `git -C /Users/mc/dev/Syvert status --short --branch`
   - 期望：主仓 worktree 干净；若存在无关本地改动，先停止并人工确认，不得覆盖。
   - `git -C /Users/mc/dev/Syvert switch main`
   - `git -C /Users/mc/dev/Syvert fetch origin main --prune`
   - `git -C /Users/mc/dev/Syvert merge --ff-only origin/main`
   - `gh api repos/:owner/:repo/pulls/343 --jq '{number,state,merged,merged_at,merge_commit_sha,head:.head.sha}'`
   - 期望：`merged=true`，`state=closed`，`merge_commit_sha` 为新的 `origin/main` ancestor。
2. 确认 Work Item truth：
   - `gh api repos/:owner/:repo/issues/322 --jq '{number,state,state_reason,closed_at}'`
   - 期望：`state=closed`，`state_reason=completed`。若未自动关闭，使用 `gh api repos/:owner/:repo/issues/322 -X PATCH -f state=closed -f state_reason=completed` 补齐。
3. 在父 FR `#297` 写入 closeout comment：
   - `gh api repos/:owner/:repo/issues/297/comments -f body='<FR-0025 closeout comment>'`
   - Comment body：

```text
FR-0025 closeout 已完成。

对账范围：
- #319 / PR #328：Provider capability offer formal spec 已合入主干。
- #320 / PR #335：Provider offer manifest / validator 已合入主干。
- #321 / PR #338：SDK docs / evidence 已合入主干。
- #322 / PR #343：父事项 closeout evidence 已合入主干。

主干 truth：origin/main 已包含 FR-0025 formal spec、Provider offer validator、runtime tests、SDK docs 与 evidence，以及 parent closeout artifact。

本 FR 只冻结 ProviderCapabilityOffer 的 declared offer truth；是否 matched / compatible 由 FR-0026 decision contract 判定。本 FR 不关闭 Phase #293，Phase closeout 仍等待剩余父项最终对账完成。
```

4. 关闭父 FR `#297`：
   - `gh api repos/:owner/:repo/issues/297 -X PATCH -f state=closed -f state_reason=completed --jq '{number,state,state_reason,closed_at}'`
5. 在 Phase `#293` 写入 progress comment：
   - `gh api repos/:owner/:repo/issues/293/comments -f body='<FR-0025 phase progress comment>'`
   - Comment body：

```text
v0.8.0 Phase progress：FR-0025 / #297 已完成并关闭。

已完成链路：#319/#320/#321/#322 均为 closed completed；对应 PR #328/#335/#338/#343 已合入主干。

Phase #293 继续保持 open，后续还需收口 FR-0023 / #295（#312）等剩余父项对账。
```
6. 清理执行现场：
   - `git worktree remove /Users/mc/code/worktrees/syvert/issue-322-fr-0025`
   - `python3 scripts/retire_branch.py --branch issue-322-fr-0025 --strategy superseded --replaced-by origin/main --reason "PR #343 squash merged into main"`

## 主干事实

- Formal spec：`docs/specs/FR-0025-provider-capability-offer-contract/`
- Formal spec exec-plan：`docs/exec-plans/CHORE-0319-fr-0025-formal-spec-closeout.md`
- Provider offer validator：`syvert/provider_capability_offer.py`
- Provider offer fixtures：`tests/runtime/provider_capability_offer_fixtures.py`
- Provider offer tests：`tests/runtime/test_provider_capability_offer.py`
- SDK docs：`adapter-sdk.md`
- SDK docs exec-plan：`docs/exec-plans/CHORE-0321-fr-0025-sdk-docs-evidence.md`
- Docs evidence：`docs/exec-plans/artifacts/CHORE-0321-fr-0025-provider-offer-sdk-evidence.md`

## 完成语义

`FR-0025` 已完成以下 v0.8.0 范围：

- 冻结 `ProviderCapabilityOffer` canonical carrier。
- 明确 Adapter-bound provider identity、capability offer、resource support、error carrier、version、evidence、lifecycle、observability 与 fail-closed 字段边界。
- Validator 能稳定区分合法 offer、invalid contract 与 scope drift。
- SDK docs 和 evidence 已解释 Adapter 作者声明 Provider offer 的合法路径、fixture refs、validator 结果与后续 `FR-0026` 消费关系。
- 合法 Provider offer 只表示 `declared`；是否满足某个 Adapter requirement 必须交给 `FR-0026` 的 `AdapterProviderCompatibilityDecision` 判定。

## 明确不完成

- 不实现 `FR-0026` compatibility decision。
- 不把 `declared` 推导为 `matched`、selected provider、fallback candidate 或真实 provider 产品支持。
- 不引入 provider selector、priority、score、fallback、ranking 或 marketplace。
- 不声明任何真实 provider 产品正式支持。
- 不让 Core discovery / routing 感知 provider。
- 不关闭 Phase `#293`；Phase closeout 等 `FR-0023`、`FR-0025`、`FR-0026` 等父项一起收口。

## 后续消费

- `FR-0026` 只能消费本 FR 已合入的 `ProviderCapabilityOffer` truth，不得在 decision Work Item 中重写 offer carrier。
- `v0.9.0` 真实 provider sample 可以消费本 FR 的 offer contract，但必须以独立 Work Item 进入。
- Phase `#293` closeout 可引用本 closeout evidence 说明 `FR-0025` 已完成。
- 若后续要改变 Provider offer 语义，必须回到 formal spec Work Item，不在 parent closeout 中改写。
