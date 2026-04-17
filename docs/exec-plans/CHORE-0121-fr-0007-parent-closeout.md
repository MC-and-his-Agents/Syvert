# CHORE-0121-fr-0007-parent-closeout 执行计划

## 关联信息

- item_key：`CHORE-0121-fr-0007-parent-closeout`
- Issue：`#121`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0007-release-gate-and-regression-checks/`
- 关联 PR：`待创建`
- 状态：`active`
- active 收口事项：`CHORE-0121-fr-0007-parent-closeout`

## 目标

- 在不引入新运行时代码或新 formal spec 语义的前提下，通过合法 Work Item `#121` 完成父 FR `#67` 的最终 closeout。
- 把 `FR-0007` 的 formal spec、`#118/#119/#120` 实现、release / sprint 索引与 GitHub issue 真相映射回同一条父事项证据链。
- 在满足条件时关闭 `#121`、关闭 `#67`，并独立核对 `#63` 是否满足阶段关闭前提。

## 范围

- 本次纳入：
  - `docs/exec-plans/FR-0007-release-gate-and-regression-checks.md`
  - `docs/exec-plans/CHORE-0121-fr-0007-parent-closeout.md`
  - `docs/exec-plans/CHORE-0079-fr-0007-formal-spec-closeout.md`
  - `docs/exec-plans/CHORE-0118-fr-0007-version-gate-orchestrator.md`
  - `docs/exec-plans/CHORE-0119-fr-0007-dual-reference-adapter-regression.md`
  - `docs/exec-plans/CHORE-0120-fr-0007-platform-leakage-check.md`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
  - GitHub `#121` / `#67` / `#63` issue 正文与 closeout 评论
- 本次不纳入：
  - 任何新的 runtime / adapter / test 实现
  - `FR-0007` formal spec 语义改写
  - `FR-0004`、`FR-0005`、`FR-0006` 的事项状态调整

## 当前停点

- `origin/main@f9f2b564f17c3ef269eb25faecd12f1c0e18442b` 已包含 `FR-0007` closeout 所需的关键前提：PR `#84`、`#122`、`#124`、`#123`。
- `#79` 已由 PR `#84` 合入并关闭；`#118` 已由 PR `#122` 合入并关闭；`#119` 已由 PR `#124` 合入并关闭；`#120` 已由 PR `#123` 合入并关闭。
- 当前 `FR-0007` GitHub closeout 仍包含 Work Item `#121` 与父 FR `#67`；阶段 `#63` 仍为 `OPEN`，因为其子 FR `#67` 尚未关闭。
- `#63` 的另外三个子 FR `#64/#65/#66` 已全部 `CLOSED`；`#67` 是当前阻止 `#63` closeout 的唯一直接前提。
- 当前执行现场为独立 worktree：`/Users/mc/code/worktrees/syvert/issue-121-chore-fr-0007`。

## 下一步动作

- 新增 `FR-0007` requirement container，把 `#79/#118/#119/#120` 历史执行轮次与 `#121` closeout 入口收敛到同一条仓内证据链。
- 同步 `docs/releases/v0.2.0.md` 与 `docs/sprints/2026-S15.md`，把 `FR-0007` 从 formal spec 入口推进到 implementation + parent closeout 完成的最终叙事。
- 通过 docs PR 收口 `#121`，合并后修正 GitHub `#121` / `#67` 正文并关闭；若 `#63` 关闭条件届时全部满足，再关闭 `#63`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 完成 `FR-0007` 父事项收口，使版本 gate、双参考适配器真实回归与平台泄漏检查 requirement 已被 formal spec、主干实现、验证证据与 GitHub 关闭语义完整消费。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0007` 父事项 closeout Work Item。
- 阻塞：
  - 必须先保证 `#79/#118/#119/#120` 全部关闭，且 release / sprint / exec-plan 不再把 `FR-0007` 误表述为只有 formal spec 入口。
  - 必须在关闭前修正 GitHub `#67` 正文，使其反映 formal spec、版本 gate、双参考适配器真实回归、平台泄漏检查与 parent closeout 的主干真相。
  - `#63` 只有在 `#67` 关闭后才可能满足阶段关闭前提；不得从 `#64/#65/#66` 已关闭自动推断。

## 已验证项

- 已阅读：`docs/specs/FR-0007-release-gate-and-regression-checks/`
- 已阅读：`docs/exec-plans/CHORE-0079-fr-0007-formal-spec-closeout.md`
- 已阅读：`docs/exec-plans/CHORE-0118-fr-0007-version-gate-orchestrator.md`
- 已阅读：`docs/exec-plans/CHORE-0119-fr-0007-dual-reference-adapter-regression.md`
- 已阅读：`docs/exec-plans/CHORE-0120-fr-0007-platform-leakage-check.md`
- `gh issue view 67 --json state,title,url,body`
  - 结果：`#67` 当前为 `OPEN`，且正文仍只覆盖 formal spec 与子 Work Item 列表，尚未写入 implementation 与 parent closeout 完成事实。
- `gh issue view 121 --json state,title,url,body`
  - 结果：`#121` 当前为 `OPEN`，且执行状态仍为 `待开始`。
- `gh issue view 63 --json state,title,url,body`
  - 结果：`#63` 当前为 `OPEN`，且关闭条件要求所有子 FR 完成并关闭。
- `gh issue view 64 --json state,url`
  - 结果：`#64` 为 `CLOSED`。
- `gh issue view 65 --json state,url`
  - 结果：`#65` 为 `CLOSED`。
- `gh issue view 66 --json state,url`
  - 结果：`#66` 为 `CLOSED`。
- `gh issue view 118 --json state,title,url,body`
  - 结果：`#118` 为 `CLOSED`，对应 PR `#122` / merge commit `eb5bbc3d0bf0dc5b91fe64a8a63aa24c34ba8479`。
- `gh issue view 119 --json state,title,url,body`
  - 结果：`#119` 为 `CLOSED`，对应 PR `#124` / merge commit `830c1021febf4a4fa5be670dcdece009dc2352b5`。
- `gh issue view 120 --json state,title,url,body`
  - 结果：`#120` 为 `CLOSED`，对应 PR `#123` / merge commit `f9f2b564f17c3ef269eb25faecd12f1c0e18442b`；GitHub merge 真相、issue 关闭真相与 remote branch 删除真相已独立成立。
- `gh pr view 122 --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`，`mergeCommit=eb5bbc3d0bf0dc5b91fe64a8a63aa24c34ba8479`
- `gh pr view 124 --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`，`mergeCommit=830c1021febf4a4fa5be670dcdece009dc2352b5`
- `gh pr view 123 --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`，`mergeCommit=f9f2b564f17c3ef269eb25faecd12f1c0e18442b`

## closeout 证据

- formal spec 证据：PR `#84` 已把 `FR-0007` formal spec 合入主干，对应 `docs/specs/FR-0007-release-gate-and-regression-checks/`
- implementation 证据：
  - PR `#122` / `#118`：落地版本 gate 编排与统一结果模型，冻结 harness / real-regression / platform-leakage 三类 source report 的公共消费面
  - PR `#124` / `#119`：落地双参考适配器真实回归执行器，固定 `xhs` / `douyin` 最小回归矩阵并生成版本 gate 可直接消费的 source report
  - PR `#123` / `#120`：落地平台泄漏检查器，固定共享边界扫描面、fail-closed evidence trace 与 `shared_input_model` / `shared_error_model` / `shared_result_contract` 分类
- 主干证据：`origin/main@f9f2b564f17c3ef269eb25faecd12f1c0e18442b` 已包含 `FR-0007` 当前全部 formal spec + implementation 前提
- GitHub closeout 证据：当前剩余 GitHub closeout issue 为 active Work Item `#121` 与父 FR `#67`；`#63` 需等 `#67` 关闭后再独立核对阶段关闭条件

## GitHub closeout 工件

- `#67` 正文修正目标：
  - 明确 formal spec 已由 PR `#84` 合入主干
  - 明确版本 gate 编排已由 `#118` / PR `#122` 落地
  - 明确双参考适配器真实回归执行器已由 `#119` / PR `#124` 落地
  - 明确平台泄漏检查器已由 `#120` / PR `#123` 落地
  - 将父事项 closeout 入口补为 `#121`
  - 子 Work Item 保持：`#118`、`#119`、`#120`、`#121`
- `#67` closeout 评论草案：
  - `FR-0007` formal spec 已由 PR `#84` 合入主干，spec 真相位于 `docs/specs/FR-0007-release-gate-and-regression-checks/`
  - `#118` / PR `#122` 已完成版本 gate 编排与统一结果模型
  - `#119` / PR `#124` 已完成双参考适配器真实回归执行器
  - `#120` / PR `#123` 已完成平台泄漏检查器，并独立区分 GitHub merge 真相与本地清理尾项
  - 当前父事项 closeout 已由 `#121` 承接，release / sprint / exec-plan / GitHub issue 真相已回链到同一条 `FR-0007` 证据链
- `#63` 条件性关闭前提：
  - `#64/#65/#66/#67` 必须全部 `CLOSED`
  - `#63` 正文必须更新为与 `docs/releases/v0.2.0.md`、`docs/sprints/2026-S15.md` 一致的阶段完成事实
  - 若任一条件不满足，则不得关闭 `#63`

## 未决风险

- 若 `#67` 关闭前 release / sprint 仍只把 `FR-0007` 视为 formal spec 入口，会留下 requirement / implementation / closeout 语义断裂。
- 若把 `#120` 这轮的本地 branch/worktree 保留误判成 GitHub merge 未完成，会错误阻塞 `#121` 与 `#67` closeout。
- 若在 `#67` 关闭前不独立核对 `#63` 的子 FR 状态与阶段正文，会把阶段 closeout 建立在推断而非证据上。

## 回滚方式

- 仓内回滚：如需回滚，使用独立 revert PR 撤销本事项对 `docs/exec-plans/FR-0007-release-gate-and-regression-checks.md`、`docs/exec-plans/CHORE-0121-fr-0007-parent-closeout.md`、`docs/releases/v0.2.0.md` 与 `docs/sprints/2026-S15.md` 的增量修改。
- GitHub 侧回滚：
  - 若已编辑 `#67` / `#63` 正文但 PR 未合入，恢复其 closeout 前正文，并保留 `#121/#67/#63` 的 open/closed 真相不变
  - 若已发布 closeout 评论但发现仓内工件仍不一致，在对应 issue 追加纠正评论并停止关闭动作
  - 若 `#67` 或 `#63` 已关闭后发现 closeout 事实错误，先重新打开对应 issue，再通过独立 revert PR 与新的 closeout 回合修复仓内 / GitHub 状态

## 最近一次 checkpoint 对应的 head SHA

- `f9f2b564f17c3ef269eb25faecd12f1c0e18442b`
- 说明：该 checkpoint 已包含 `FR-0007` formal spec、`#118/#119/#120` implementation 主干真相与 `#120` closeout 后的 GitHub 状态；本回合仅负责 parent closeout 元数据收口。
