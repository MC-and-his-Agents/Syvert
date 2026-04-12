# CHORE-0068-fr-0004-implementation-closeout 执行计划

## 关联信息

- item_key：`CHORE-0068-fr-0004-implementation-closeout`
- Issue：`#68`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0004-input-target-and-collection-policy/`
- 关联 decision：
- 关联 PR：`#93`
- 状态：`active`
- active 收口事项：`CHORE-0068-fr-0004-implementation-closeout`

## 目标

- 在 `#87`、`#89`、`#88` 全部关闭后，为 `FR-0004` 的 implementation 聚合入口完成 docs-only closeout，确认主干实现、exec-plan、release/sprint 索引与 GitHub 状态一致后关闭 `#68`。

## 范围

- 本次纳入：
  - `docs/exec-plans/FR-0004-input-target-and-collection-policy.md`
  - `docs/exec-plans/CHORE-0068-fr-0004-formal-spec-closeout.md`
  - `docs/exec-plans/CHORE-0087-fr-0004-core-input-admission.md`
  - `docs/exec-plans/CHORE-0089-fr-0004-core-adapter-projection.md`
  - `docs/exec-plans/CHORE-0088-fr-0004-fr-0002-compat-closeout.md`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
  - 本 exec-plan
  - GitHub `#68` closeout 评论
- 本次不纳入：
  - 任何新的 runtime / adapter / test 实现
  - `#64` 父 FR closeout（单独下一回合处理）
  - `FR-0005`、`FR-0006`、`FR-0007` 的事项状态调整

## 当前停点

- `FR-0004` formal spec 已由 PR `#82` 合入主干。
- `#87` 已由 PR `#90` 合入并关闭。
- `#89` 已由 PR `#91` 合入并关闭。
- `#88` 已由 PR `#92` 合入并关闭。
- 当前 `#68` 仍为 `OPEN`，但其下已无未完成 implementation 子事项。
- 旧 `CHORE-0068-fr-0004-formal-spec-closeout` 已显式标记为 `状态：inactive (...)`，避免与当前 implementation closeout 回合形成双 active 上下文。
- 当前独立 worktree：`/Users/mc/code/worktrees/syvert/issue-68-inputtarget-collectionpolicy`
- 当前执行分支：`issue-68-inputtarget-collectionpolicy`
- 最近一次显式 checkpoint 绑定 `480f0e697c5fa37313046838d7a3a16b71d5eb58`；其后的提交仅用于补齐 active exec-plan 的 PR 绑定、唯一化上下文与 sprint 聚合索引，不单独形成新的 closeout 停点。

## 下一步动作

- 等待 PR `#93` 的 GitHub checks 全绿，并对当前 head 运行 guardian 审查。
- 若 guardian `APPROVE` 且 `safe_to_merge=true`，通过受控入口合并 PR。
- 合并后在 GitHub `#68` 评论归档三条子事项与验证入口，随后关闭 `#68`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 收口 `FR-0004` 的 implementation 聚合层，确保 `#64` 父 FR closeout 可以直接消费主干事实而无需再次拼接子事项链。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0004` implementation 聚合 closeout 入口。
- 阻塞：
  - 必须先确认 `#87/#89/#88` 已全部关闭，且不存在额外遗漏的 implementation 子事项。
  - 本回合不得提前关闭 `#64`。

## 已验证项

- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`spec_review.md`
- 已阅读：`code_review.md`
- 已阅读：`docs/specs/FR-0004-input-target-and-collection-policy/`
- 已核对：`#87/#89/#88` 已关闭，`#68/#64` 仍为 `OPEN`
- 已核对：GitHub 中当前可见的 `FR-0004` implementation Work Item 仅有 `#87/#89/#88`，未发现额外仍处于 `OPEN` 的 implementation 子事项；额外出现的 `#85` 为 `spec_issue_sync.py` 自动维护的 spec 索引 issue，不承载 `#64` 下的 implementation closeout 语义
- 已核对：当前 `#68` worktree 基于 `origin/main@fe328a8dcb6228bf9d38b28b9c9c59ebf5cc34c2`
- 已核对：`docs/releases/v0.2.0.md` 与 `docs/sprints/2026-S15.md` 已同时索引 `FR-0004/#64`、历史 formal spec 回合、当前 implementation closeout 回合，以及 `#87/#89/#88 -> PR #90/#91/#92` 的主干实现链；合并本 PR 后不会留下双 active 或断链入口
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
  - 结果：已校验 2 条提交信息，全部通过
- `python3 scripts/open_pr.py --class docs --issue 68 --item-key CHORE-0068-fr-0004-implementation-closeout --item-type CHORE --release v0.2.0 --sprint 2026-S15 --title 'docs(closeout): 收口 FR-0004 implementation 聚合事项' --closing fixes --dry-run`
  - 结果：通过
- 已创建当前受审 PR：`#93 https://github.com/MC-and-his-Agents/Syvert/pull/93`

## closeout 证据

- formal spec 主干事实：PR `#82` 已合入，`InputTarget` 与 `CollectionPolicy` 的 formal spec 真相位于 `docs/specs/FR-0004-input-target-and-collection-policy/`
- implementation 子事项主干事实：`#87/#89/#88` 已分别由 PR `#90/#91/#92` 合入并关闭
- GitHub 调度层事实：当前仅剩 `#68` implementation 聚合 closeout 与父 FR `#64` 仍为 `OPEN`
- release / sprint 索引事实：`docs/releases/v0.2.0.md`、`docs/sprints/2026-S15.md` 已同时回链 formal spec、implementation closeout 与三条实现 PR，合并本 PR 后即可直接作为 `#68` closeout 评论引用入口

## 未决风险

- 若 `#68` 关闭前遗漏新的 implementation 子事项，会导致 `#64` 父 FR 关闭语义提前。
- 若只关闭 GitHub issue 而不补主干索引与 closeout 评论，后续回溯 `FR-0004` 实现链仍需手工拼接。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 release/sprint 索引与 exec-plan 的 docs-only closeout 增量。

## 最近一次 checkpoint 对应的 head SHA

- `480f0e697c5fa37313046838d7a3a16b71d5eb58`
