# CHORE-0327 FR-0026 parent closeout evidence

## 目的

本文档汇总 `FR-0026` 父事项 closeout 所需的主干事实、子 Work Item 状态、验证证据、风险和后续消费边界。它不定义新的 compatibility decision 语义。

## 父 FR

- FR Issue：`#298`
- item_key：`FR-0026-adapter-provider-compatibility-decision`
- release：`v0.8.0`
- sprint：`2026-S21`
- Parent Phase：`#293`

## 子 Work Item closeout 状态

| Issue | item_key | 结果 |
| --- | --- | --- |
| `#323` | `CHORE-0323-fr-0026-formal-spec-closeout` | closed completed |
| `#324` | `CHORE-0324-fr-0026-compatibility-decision-runtime` | closed completed |
| `#325` | `CHORE-0325-fr-0026-provider-no-leakage-guards` | closed completed |
| `#326` | `CHORE-0326-fr-0026-docs-evidence-migration` | closed completed |
| `#327` | `CHORE-0327-fr-0026-parent-closeout` | current closeout Work Item |

## PR / Main 对账

可复验入口：

- PR truth：`gh api repos/:owner/:repo/pulls/<pr> --jq '{number,merged,merged_at,merge_commit_sha,head:.head.sha,state}'`
- Issue truth：`gh api repos/:owner/:repo/issues/<issue> --jq '{number,state,state_reason,closed_at,title}'`
- Main truth：`git rev-parse origin/main` 与 `git merge-base --is-ancestor <merge_commit_sha> origin/main`
- Path truth：`git cat-file -e origin/main:<path>`

| Work Item | PR | PR head | main merge commit | merged_at |
| --- | --- | --- | --- | --- |
| `#323` | `#333` | `068a0de4198b4c223da14425f71f9da46cc23087` | `22aae087cbf7fba790d85485259d0af278f22375` | `2026-05-03T10:38:00Z` |
| `#324` | `#339` | `d39a94fa46b4f34fcfa4987657dc3e602049f49a` | `b3850cd588d557d2a97ce7d1526863eccbb1ac4e` | `2026-05-04T11:34:43Z` |
| `#325` | `#340` | `65c95969d2702df32155a5037a07da80fb3556db` | `d1577d6e620a43010c40e81f3a8c05b413dbc04f` | `2026-05-05T03:27:37Z` |
| `#326` | `#341` | `1c6d9bff9e4c696ad623aa989ee25d5f6bb3ba17` | `24ae582447165596a54edacb35568ab4c73a55cb` | `2026-05-05T07:15:42Z` |

对账结论：

- `#323/#324/#325/#326` 的 PR 均已 merged，且对应 Work Item 均为 `closed completed`。
- 当前 worktree 基线为 `24ae582447165596a54edacb35568ab4c73a55cb`，已包含 `#323/#324/#325/#326` 的 main truth。
- `origin/main` 当前为 `24ae582447165596a54edacb35568ab4c73a55cb`；上表四个 merge commit 均为 `origin/main` ancestor。
- `#327` 是唯一剩余的 `FR-0026` closeout Work Item，合入后即可关闭父 FR `#298`。

## Merge Gate 边界

- `#333/#339/#340/#341` 的可复验 closeout 输入是 GitHub PR 已合入、对应 Work Item 已关闭、merge commit 已进入 `origin/main`、主干包含对应路径。
- 本 artifact 不把未保存的历史 guardian/check 详情重新声明为 closeout truth；它只消费已合入 PR 与主干路径事实。
- `#342` 是当前 parent closeout PR，合入前仍必须以当前 head 取得 guardian `APPROVE`、`safe_to_merge=true` 与 GitHub checks 全绿。

## GitHub 状态对账

- 父 FR `#298` 当前仍 open；它必须等待 `#342` 合入后再 close。
- Phase `#293` 当前仍 open；本 closeout 只为 Phase closeout 提供 `FR-0026` 完成输入，不关闭 Phase。
- `#323/#324/#325/#326` 已关闭；`#327` 当前 open，作为本轮唯一执行入口。

## 主干事实

- Formal spec：`docs/specs/FR-0026-adapter-provider-compatibility-decision/`
- Runtime decision：`syvert/adapter_provider_compatibility_decision.py`
- Runtime tests：`tests/runtime/test_adapter_provider_compatibility_decision.py`
- No-leakage guard：`syvert/provider_no_leakage_guard.py`
- No-leakage tests：`tests/runtime/test_provider_no_leakage_guard.py`
- SDK docs：`adapter-sdk.md`
- Docs evidence：`docs/exec-plans/artifacts/CHORE-0326-fr-0026-compatibility-decision-evidence.md`

## 完成语义

`FR-0026` 已完成以下 v0.8.0 范围：

- 冻结 `AdapterCapabilityRequirement x ProviderCapabilityOffer -> AdapterProviderCompatibilityDecision` 的 canonical decision contract。
- 明确 `matched`、`unmatched`、`invalid_contract` 与 fail-closed 边界。
- Runtime decision 消费 `FR-0024`、`FR-0025` 与 `FR-0027` truth，不重写输入 carrier。
- No-leakage guard 证明 provider identity 不进入 Core projection / routing、registry discovery、TaskRecord、resource lifecycle 或 runtime provider category。
- SDK docs 和 evidence 已解释 Adapter 作者迁移路径、fail-closed 示例与禁止边界。

## 明确不完成

- 不引入 provider selector、priority、score、fallback、ranking 或 marketplace。
- 不声明任何真实 provider 产品正式支持。
- 不让 Core discovery / routing 感知 provider。
- 不关闭 Phase `#293`；Phase closeout 等 `FR-0023`、`FR-0025` 等父项一起收口。

## 后续消费

- `v0.9.0` 真实 provider sample 可以消费本 FR 的 decision contract，但必须以独立 Work Item 进入。
- Phase `#293` closeout 可引用本 closeout evidence 说明 `FR-0026` 已完成。
- 若后续要改变 compatibility decision 语义，必须回到 formal spec Work Item，不在 parent closeout 中改写。

## Post-Merge GitHub Closeout 协议补录

本节由 `#345 / GOV-0345-v0-8-0-phase-release-closeout-record` 补录，用于保存 `#327 / PR #342` 合入后的 GitHub 状态对账动作。它不改变 `FR-0026` compatibility decision 语义，也不改写 `#327` exec-plan checkpoint。

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
