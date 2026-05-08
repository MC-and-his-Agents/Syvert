# GOV-0360 v0.9.0 release closeout record 执行计划

## 关联信息

- item_key：`GOV-0360-v0-9-0-release-closeout-record`
- Issue：`#360`
- item_type：`GOV`
- release：`v0.9.0`
- sprint：`2026-S22`
- Parent Phase：`#354`
- Parent FR：`#355`
- 关联 spec：无（治理 / release closeout 事项）
- 关联 decision：`docs/decisions/ADR-GOV-0360-v0-9-0-release-closeout-record.md`
- active 收口事项：`GOV-0360-v0-9-0-release-closeout-record`
- 状态：`active`

## 目标

- 补齐 `v0.9.0` release index、sprint index 与 closeout evidence。
- 在阶段 A carrier 合入 main 后创建 `v0.9.0` annotated tag 与 GitHub Release。
- 阶段 B 回写 published truth carrier，并关闭 Phase `#354`、FR `#355` 与 Work Item `#360`。

## 范围

- 本次纳入：
  - `docs/releases/v0.9.0.md`
  - `docs/sprints/2026-S22.md`
  - `docs/exec-plans/GOV-0360-v0-9-0-release-closeout-record.md`
  - `docs/exec-plans/artifacts/GOV-0360-v0-9-0-release-closeout-evidence.md`
  - `docs/decisions/ADR-GOV-0360-v0-9-0-release-closeout-record.md`
- 本次不纳入：
  - runtime / adapter / provider 实现变更
  - formal spec 语义变更
  - provider 产品正式支持声明
  - Core provider registry、provider selector、fallback、priority、ranking 或 marketplace
  - Python package publish

## 当前停点

- Phase `#354`：open。
- FR `#355`：open。
- Work Item `#356`：closed completed；PR `#357` 已合入，merge commit `5d505179f3ea4d0508e913e407f39b4c73ba8874`。
- Work Item `#358`：closed completed；PR `#359` 已合入，merge commit `ecfc3bf53299191e42c13c5b1c6578fd90aa84b6`。
- Work Item `#360`：open。
- 主仓 main 已快进到 `ecfc3bf53299191e42c13c5b1c6578fd90aa84b6`。
- `v0.9.0` tag 与 GitHub Release 尚未创建。

## 下一步动作

- 阶段 A：提交 release / sprint / closeout evidence carrier，开 docs PR，等待 checks 与 guardian，通过后受控合入。
- 发布锚点：阶段 A 合入后在 main 上创建并推送 `v0.9.0` annotated tag，创建 GitHub Release。
- 阶段 B：回写 release index 与 closeout evidence 的 published truth carrier，开 follow-up docs PR。
- 阶段 B 合入后：关闭 `#355/#354/#360`，清理 worktree 并退役分支。

## 当前 checkpoint 推进的 release 目标

- 使 `v0.9.0` 的 provider compatibility sample evidence、release index、tag、GitHub Release 与 GitHub issue truth 对齐。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S22` release closeout / published truth Work Item。
- 阻塞：阶段 A 合入前不得创建 tag / GitHub Release；阶段 B 回写前不得声明 release 已完成。

## 已验证项

- `gh api repos/MC-and-his-Agents/Syvert/pulls/357 --jq '{number,state,merged,merged_at,merge_commit_sha,head:.head.ref,head_sha:.head.sha}'`
  - 结果：PR `#357` merged，merge commit `5d505179f3ea4d0508e913e407f39b4c73ba8874`。
- `gh api repos/MC-and-his-Agents/Syvert/pulls/359 --jq '{number,state,merged,merged_at,merge_commit_sha,head:.head.ref,head_sha:.head.sha}'`
  - 结果：PR `#359` merged，merge commit `ecfc3bf53299191e42c13c5b1c6578fd90aa84b6`。
- `gh api repos/MC-and-his-Agents/Syvert/issues/356 --jq '{number,state,state_reason,closed_at,title}'`
  - 结果：`closed completed`。
- `gh api repos/MC-and-his-Agents/Syvert/issues/358 --jq '{number,state,state_reason,closed_at,title}'`
  - 结果：`closed completed`。
- `git tag --list 'v0.9.0*'`
  - 阶段 A 前结果：无输出。
- `gh release view v0.9.0 --repo MC-and-his-Agents/Syvert --json tagName,name,url,isDraft,isPrerelease,publishedAt,targetCommitish`
  - 阶段 A 前结果：无 GitHub Release `v0.9.0`。

## 待验证项

- 阶段 A 本地 docs / spec / workflow / governance / version guard。
- 阶段 A PR checks、guardian 与受控 merge。
- `v0.9.0` annotated tag 与 GitHub Release。
- 阶段 B published truth 回写 PR checks、guardian 与受控 merge。
- Phase / FR / Work Item closeout comment 与 GitHub 状态。

## closeout 证据

- 可复验 evidence artifact：`docs/exec-plans/artifacts/GOV-0360-v0-9-0-release-closeout-evidence.md`
- Release index：`docs/releases/v0.9.0.md`
- Sprint index：`docs/sprints/2026-S22.md`

## 风险

- 若 release index 提前声明 published truth，会造成 tag / GitHub Release 与仓内文档分叉。
- 若 tag 指向未包含 release carrier 的提交，会降低 release closeout 可复验性。
- 若 closeout 声明 provider 产品正式支持，会越过 `v0.9.0` 明确边界。

## 回滚方式

- 仓内回滚：使用独立 revert PR 撤销 `GOV-0360` release closeout carrier。
- 仓外回滚：若 tag / GitHub Release 已建立但发现主干事实错误，先修正主干 truth，再通过独立治理 Work Item 决定是否删除 / 重建发布锚点。
- GitHub issue 回滚：若 closeout 后发现事实错误，使用 REST 重新打开对应 Issue 并追加纠正评论。

## 最近一次 checkpoint 对应的 head SHA

- 阶段 A 前 implementation truth：`ecfc3bf53299191e42c13c5b1c6578fd90aa84b6`
