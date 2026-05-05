# CHORE-0327-fr-0026-parent-closeout 执行计划

## 关联信息

- item_key：`CHORE-0327-fr-0026-parent-closeout`
- Issue：`#327`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 父 FR：`#298`
- 关联 spec：`docs/specs/FR-0026-adapter-provider-compatibility-decision/`
- active 收口事项：`CHORE-0327-fr-0026-parent-closeout`
- 状态：`active`

## 目标

- 汇总 `FR-0026` formal spec、decision runtime、no-leakage guards、docs / evidence、review、guardian、主干事实与 GitHub 状态。
- 关闭父 FR `#298`，让 Phase `#293` 后续 closeout 可消费 `FR-0026` 结果。

## 范围

- 本次纳入：
  - `docs/exec-plans/CHORE-0327-fr-0026-parent-closeout.md`
  - `docs/exec-plans/artifacts/CHORE-0327-fr-0026-parent-closeout-evidence.md`
  - `docs/releases/v0.8.0.md`
  - `docs/sprints/2026-S21.md`
- 本次不纳入：
  - `docs/specs/FR-0026-adapter-provider-compatibility-decision/**`
  - `syvert/**`
  - `tests/**`
  - `scripts/**`
  - 真实 provider 样本
  - Phase `#293` closeout

## 当前停点

- worktree：`/Users/mc/code/worktrees/syvert/issue-327-fr-0026`
- 分支：`issue-327-fr-0026`
- worktree 创建基线：`24ae582447165596a54edacb35568ab4c73a55cb`
- 已确认子 Work Item 状态：
  - `#323` closed completed，formal spec closeout 已合入。
  - `#324` closed completed，decision runtime 已合入。
  - `#325` closed completed，provider no-leakage guard 已合入。
  - `#326` closed completed，SDK docs / evidence 已合入。
- 当前 checkpoint：已新增父 FR closeout evidence artifact，并更新 release/sprint 索引入口。本文档只做 closeout 证据与状态收口，不新增 spec/runtime 语义。

## 下一步动作

- 运行 docs class gates：`docs_guard`、`spec_guard --all`、`workflow_guard`、`governance_gate`、`pr_scope_guard --class docs`。
- 提交中文 Conventional Commit，使用 `scripts/open_pr.py` 受控开 PR。
- guardian review 通过且 checks 全绿后使用受控 merge。
- 合并后关闭 `#298`，更新 Phase `#293` comment，清理 worktree 并退役分支。

## 已验证项

- `python3 scripts/create_worktree.py --issue 327 --class docs`
  - 结果：通过；创建 worktree `/Users/mc/code/worktrees/syvert/issue-327-fr-0026`，分支 `issue-327-fr-0026`，基线 `24ae582447165596a54edacb35568ab4c73a55cb`。
- GitHub issue status：
  - `#323`：closed completed。
  - `#324`：closed completed。
  - `#325`：closed completed。
  - `#326`：closed completed。
  - `#327`：open，当前执行入口。
- 父 FR `#298`
  - 结果：仍 open，等待本 closeout PR 合入后关闭。
- `git diff --check`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-327-fr-0026`
  - 结果：通过。
- 提交前 `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：首次运行因新增文件尚未进入 Git diff，返回“当前分支相对基线没有变更”；提交后复跑。

## 待验证项

- docs class gates。
- PR guardian、GitHub checks、受控 merge。
- `#298` closeout comment / close issue。
- Phase `#293` progress comment。
- worktree cleanup 与 branch retirement。

## 风险

- 若 closeout 在子 Work Item 未完成时关闭 `#298`，会造成 GitHub truth 与主干 truth 不一致。
- 若 closeout 文档新增 compatibility decision 语义，会违反 formal spec / implementation PR 分离。

## 回滚方式

- 若发现 closeout 前提不足，停止关闭父 FR，并回到对应 Work Item 补齐。
- 若 closeout PR 已合入但父 FR 尚未关闭，可用补充 comment 标记阻塞并重新打开 / 继续父 FR。
- 若文档索引需要回滚，使用独立 revert PR 撤销本 closeout 文档增量。

## 最近一次 checkpoint 对应的 head SHA

- worktree 创建基线：`24ae582447165596a54edacb35568ab4c73a55cb`
