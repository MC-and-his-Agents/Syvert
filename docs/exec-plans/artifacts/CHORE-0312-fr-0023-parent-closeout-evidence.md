# CHORE-0312 FR-0023 parent closeout evidence

## 目的

本文档汇总 `FR-0023` 父事项 closeout 所需的 GitHub provenance、主干事实、子 Work Item 状态、当前 PR 验证入口、风险 / 回滚摘要和后续消费边界。它不定义新的 Provider offer 字段，不实现 `FR-0026`，也不把第三方 Adapter 接入扩张为 provider 产品 registry、selector 或 marketplace。

## 父 FR

- FR Issue：`#295`
- item_key：`FR-0023-third-party-adapter-entry-path`
- release：`v0.8.0`
- sprint：`2026-S21`
- Parent Phase：`#293`

## 子 Work Item closeout 状态

| Issue | item_key | 结果 |
| --- | --- | --- |
| `#309` | `CHORE-0309-fr-0023-formal-spec-closeout` | closed completed |
| `#331` | `CHORE-0331-fr-0023-third-party-resource-proof-bridge` | closed completed |
| `#310` | `CHORE-0310-fr-0023-contract-test-entry` | closed completed |
| `#311` | `CHORE-0311-fr-0023-sdk-docs-migration` | closed completed |
| `#312` | `CHORE-0312-fr-0023-parent-closeout` | current closeout Work Item |

## PR / Main 对账

可复验入口：

- PR truth：`gh api repos/:owner/:repo/pulls/<pr> --jq '{number,state,html_url,merged,merged_at,head:{ref:.head.ref,sha:.head.sha},base:{ref:.base.ref,sha:.base.sha},merge_commit_sha}'`
- Issue truth：`gh api repos/:owner/:repo/issues/<issue> --jq '{number,state,state_reason,title,html_url,labels:[.labels[].name],body}'`
- Main truth：`git rev-parse origin/main` 与 `git merge-base --is-ancestor <merge_commit_sha> origin/main`
- Path truth：`git cat-file -e origin/main:<path>`

| Work Item | PR | PR head | main merge commit | merged_at |
| --- | --- | --- | --- | --- |
| `#309` | `#318` | `dd8844b0a7b89307ebe53b0949df15928e87264c` | `ea44f9cdc863b244b7ceba5a3a70f2e23e41b7a5` | `2026-04-30T09:52:19Z` |
| `#331` | `#334` | `674ff8b50feebc051da0e23001d237aaa7b7e31f` | `15b135d3b8ded5ad0a8433639ce1df6b2f9b8da6` | `2026-05-02T06:33:53Z` |
| `#310` | `#330` | `c26e29b6abc67672ac3063ad71f0133fde150295` | `4e90953447e20b1fffaee0f8104f989bd043202e` | `2026-05-03T12:36:14Z` |
| `#311` | `#337` | `702d090484daa32ce6dbd2a6c3a1e79272dd8038` | `76926cd5fabe720681d401ea3d593c9d6290a431` | `2026-05-03T13:25:09Z` |
| `#312` | pending PR | live PR head from `gh api repos/:owner/:repo/pulls/<pr> --jq '.head.sha'` | pending merge gate | pending merge gate |

对账结论：

- `#309/#331/#310/#311` 的 PR 均已 merged，且对应 Work Item 均为 `closed completed`。
- 当前 worktree 基线为 `origin/main=c154f414428cc4a198b24e9c79fa32131d88b3d9`，已包含 `FR-0023` 子事项与后续 `FR-0025/#297`、`FR-0026/#298` closeout truth。
- `#318/#334/#330/#337` 的 merge commit 均为 `origin/main` ancestor。
- `#312` 是当前 `FR-0023` closeout Work Item，合入后即可关闭父 FR `#295`。

## 当前 PR 验证入口

- Live PR：本 artifact 不硬编码 live PR head。PR 创建后，恢复时使用 `gh api repos/:owner/:repo/pulls/<pr> --jq '{state,merged,draft,head:.head.sha,mergeable}'` 读取当前 head。
- GitHub checks：恢复时使用 `gh api repos/:owner/:repo/commits/<live-head>/check-runs --jq '{total_count,check_runs:[.check_runs[] | {name,status,conclusion}]}'` 读取当前 head 的 checks。
- Guardian：恢复时以当前 live head 对应的 latest guardian state 为准；merge gate 要求 guardian `APPROVE`、`safe_to_merge=true`、checks 全绿、PR 非 Draft 且 head 一致。

## 风险 / 回滚摘要

- 风险：合入前关闭 `#295` 会让 GitHub truth 早于主干 truth。
- 风险：把 Adapter-only 接入写成 provider 产品接入、registry、selector 或 marketplace 会越过 `FR-0023` 边界。
- 风险：漏掉 `#331` 会让真实第三方 `adapter_key` 与 `FR-0027` approved proof coverage 的 formal/evidence bridge 缺失。
- 回滚：若 closeout 文档事实有误，使用独立 revert PR 撤销本 closeout artifact 与 release / sprint 索引增量。
- GitHub 侧回滚：若 `#295` 关闭后发现事实不一致，使用 REST PATCH 重新打开并追加纠正 comment，再通过新的 Work Item 修正仓内事实。

## GitHub 状态对账

- 父 FR `#295` 当前仍 open；它必须等待 `#312` closeout PR 合入后再 close。
- Phase `#293` 当前仍 open；本 closeout 只为 Phase closeout 提供 `FR-0023` 完成输入，不关闭 Phase。
- `#309/#331/#310/#311` 已关闭；`#312` 当前 open，作为本轮唯一执行入口。

## Post-Merge GitHub Closeout 协议

本节固定 `#312` closeout PR 合入后的 GitHub 状态对账动作。合入前不得执行 `#295` close / Phase closeout，以免 GitHub truth 早于主干 truth。

1. 快进本地主干并确认 PR truth：
   - `git -C /Users/mc/dev/Syvert status --short --branch`
   - 期望：主仓 worktree 干净；若存在无关本地改动，先停止并人工确认，不得覆盖。
   - `git -C /Users/mc/dev/Syvert switch main`
   - `git -C /Users/mc/dev/Syvert fetch origin main --prune`
   - `git -C /Users/mc/dev/Syvert merge --ff-only origin/main`
   - `gh api repos/:owner/:repo/pulls/<pr> --jq '{number,state,merged,merged_at,merge_commit_sha,head:.head.sha}'`
   - 期望：`merged=true`，`state=closed`，`merge_commit_sha` 为新的 `origin/main` ancestor。
2. 确认 Work Item truth：
   - `gh api repos/:owner/:repo/issues/312 --jq '{number,state,state_reason,closed_at}'`
   - 期望：`state=closed`，`state_reason=completed`。若未自动关闭，使用 `gh api repos/:owner/:repo/issues/312 -X PATCH -f state=closed -f state_reason=completed` 补齐。
3. 在父 FR `#295` 写入 closeout comment：
   - `gh api repos/:owner/:repo/issues/295/comments -f body='<FR-0023 closeout comment>'`
   - Comment body：

```text
FR-0023 closeout 已完成。

对账范围：
- #309 / PR #318：第三方 Adapter 接入路径 formal spec 已合入主干。
- #331 / PR #334：第三方 Adapter resource proof admission bridge 已合入主干。
- #310 / PR #330：第三方 Adapter contract test entry 已合入主干。
- #311 / PR #337：Adapter SDK 接入文档与升级指引已合入主干。
- #312 / <PR>：父事项 closeout evidence 已合入主干。

主干 truth：origin/main 已包含 FR-0023 formal spec、resource proof admission bridge、third-party contract entry、runtime tests、SDK docs 与 parent closeout artifact。

本 FR 只冻结第三方 Adapter-only 稳定接入路径；不定义 ProviderCapabilityOffer、compatibility decision、provider selector / registry / marketplace 或真实 provider 产品支持。本 FR 不关闭 Phase #293，Phase closeout 仍等待剩余父项最终对账完成。
```

4. 关闭父 FR `#295`：
   - `gh api repos/:owner/:repo/issues/295 -X PATCH -f state=closed -f state_reason=completed --jq '{number,state,state_reason,closed_at}'`
5. 在 Phase `#293` 写入 progress comment：
   - `gh api repos/:owner/:repo/issues/293/comments -f body='<FR-0023 phase progress comment>'`
   - Comment body：

```text
v0.8.0 Phase progress：FR-0023 / #295 已完成并关闭。

已完成链路：#309/#331/#310/#311/#312 均为 closed completed；对应 PR #318/#334/#330/#337/<PR> 已合入主干。

Phase #293 继续保持 open，后续按剩余父项状态执行最终 Phase closeout。
```
6. 清理执行现场：
   - `git worktree remove /Users/mc/code/worktrees/syvert/issue-312-fr-0023`
   - `python3 scripts/retire_branch.py --branch issue-312-fr-0023 --strategy superseded --replaced-by origin/main --reason "PR <PR> squash merged into main"`

## 主干事实

- Formal spec：`docs/specs/FR-0023-third-party-adapter-entry-path/`
- Formal spec exec-plan：`docs/exec-plans/CHORE-0309-fr-0023-formal-spec-closeout.md`
- Resource proof admission bridge exec-plan：`docs/exec-plans/CHORE-0331-fr-0023-third-party-resource-proof-bridge.md`
- Contract entry：`tests/runtime/contract_harness/third_party_entry.py`
- Contract fixtures：`tests/runtime/contract_harness/third_party_fixtures.py`
- Contract tests：`tests/runtime/test_third_party_adapter_contract_entry.py`
- SDK docs：`adapter-sdk.md`
- SDK docs exec-plan：`docs/exec-plans/CHORE-0311-fr-0023-sdk-docs-migration.md`

## 完成语义

`FR-0023` 已完成以下 v0.8.0 范围：

- 冻结第三方 Adapter 最小 public metadata、manifest、fixture refs、contract test entry 与 migration boundary。
- 冻结真实第三方 `adapter_key` 消费 `FR-0027` approved shared profile proof 时必须使用 manifest-owned resource proof admission bridge，不得伪装为 `xhs` / `douyin` reference adapter。
- Contract entry 能 fail-closed 校验 manifest shape、public metadata、resource declaration、resource proof admission refs、fixture coverage、success raw / normalized 与 error mapping。
- SDK docs 已解释第三方 Adapter 作者如何运行 contract test、声明 manifest / fixture / resource proof admission，并区分 Adapter-only 与 Adapter + Provider 边界。

## 明确不完成

- 不定义 Provider capability offer 或 compatibility decision。
- 不接入真实外部 provider 样本。
- 不引入 provider 产品白名单、registry、selector、fallback、priority 或 marketplace。
- 不让 Core discovery / routing 感知 provider。
- 不关闭 Phase `#293`；Phase closeout 等所有父项完成后再执行。

## 后续消费

- Phase `#293` closeout 可引用本 closeout evidence 说明 `FR-0023` 已完成。
- 后续真实第三方 Adapter sample 可以消费本 FR 的 contract entry，但必须以独立 Work Item 进入。
- 若后续要改变第三方 Adapter manifest、resource proof admission 或 contract entry 语义，必须回到 formal spec / implementation Work Item，不在 parent closeout 中改写。
