# GOV-0345 v0.8.0 phase and release closeout record 执行计划

## 关联信息

- item_key：`GOV-0345-v0-8-0-phase-release-closeout-record`
- Issue：`#345`
- item_type：`GOV`
- release：`v0.8.0`
- sprint：`2026-S21`
- Parent Phase：`#293`
- 关联 spec：无（治理 / closeout record 事项）
- 关联 decision：`docs/decisions/ADR-GOV-0345-v0-8-0-phase-release-closeout-record.md`
- active 收口事项：`GOV-0345-v0-8-0-phase-release-closeout-record`
- 阶段 A PR：待创建
- 阶段 B published truth PR：待创建
- 状态：`active`

## 目标

- 补齐 `v0.8.0` final Phase / release closeout artifact，明确 Phase `#293` 已完成并关闭。
- 补齐 `#327 / FR-0026` parent closeout 的 post-merge REST closeout comment 与 GitHub 状态记录，使其与 `#312/#322` 的记录粒度一致。
- 让 release / sprint 索引、父项 closeout evidence、tag / GitHub Release、GitHub 状态与最终 main truth 一致。

## 范围

- 本次纳入：
  - `docs/exec-plans/GOV-0345-v0-8-0-phase-release-closeout-record.md`
  - `docs/exec-plans/artifacts/GOV-0345-v0-8-0-phase-release-closeout-evidence.md`
  - `docs/decisions/ADR-GOV-0345-v0-8-0-phase-release-closeout-record.md`
  - `docs/releases/v0.8.0.md`
  - `docs/sprints/2026-S21.md`
- 本次不纳入：
  - runtime / adapter / test 实现
  - formal spec 语义变更
  - `FR-0023` / `FR-0024` / `FR-0025` / `FR-0026` / `FR-0027` 范围改写
  - 真实 provider 样本
  - Core provider registry、provider selector、fallback、priority、marketplace 或 provider 产品支持承诺
  - 在阶段 A PR 合入前创建 tag 或 GitHub Release

## 当前停点

- worktree：`/Users/mc/code/worktrees/syvert/issue-345-v0-8-0-phase-release-closeout`
- 分支：`issue-345-v0-8-0-phase-release-closeout`
- worktree 创建基线：`594231b9f18a459bc64b771c486b73808ecaf764`
- `main == origin/main == 594231b9f18a459bc64b771c486b73808ecaf764`。
- Phase `#293` 已关闭为 `closed completed`，`closed_at=2026-05-05T10:22:32Z`。
- 父 FR `#294/#295/#296/#297/#298` 均已关闭为 `closed completed`。
- Work Item `#312/#322/#327` 均已关闭为 `closed completed`，对应 PR `#344/#343/#342` 已合入。
- 当前 open PR 为空。
- `issue-312-fr-0023`、`issue-322-fr-0025`、`issue-327-fr-0026` 远端分支已删除；主仓 `git fetch --prune origin` 后本地 remote-tracking refs 已清理。
- `git tag --list 'v0.8.0*'` 当前无输出。
- `gh release view v0.8.0 --repo MC-and-his-Agents/Syvert` 当前无输出。

## 下一步动作

- 阶段 A：提交并推送本 closeout record carrier，运行 docs / spec / workflow / governance / scope guard，创建 docs PR，运行 guardian review。
- 阶段 A guardian `APPROVE` 且 `safe_to_merge=true`、GitHub checks 全绿后受控合并。
- 阶段 A 合入后，在阶段 A merge commit 上创建并推送 `v0.8.0` annotated tag。
- 创建 GitHub Release `v0.8.0`。
- 阶段 B：通过 metadata-only/docs follow-up 回写 tag / GitHub Release published truth。
- 阶段 B 合入后关闭 Work Item `#345`，清理 worktree 并退役分支。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 完成 closeout record 与发布锚点补齐，使已完成的开放 Adapter 接入与 Provider 兼容性收敛目标具备可版本化、可复验的最终 Phase / release closeout artifact 与 published truth。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 的 post-closeout record / published truth Work Item，用于补齐最终 closeout artifact、`#327` post-merge closeout 记录粒度与 `v0.8.0` 发布锚点。
- 位置：本事项发生在 Phase `#293`、父 FR `#294-#298`、closeout Work Item `#312/#322/#327` 均已完成之后，不再承担产品交付或父 FR closeout。
- 阻塞：阶段 A 合入前不得创建 tag / GitHub Release；阶段 B 回写 published truth 前，不能把 release / sprint 索引视为完全覆盖正式发布锚点。

## 已验证项

- `gh api user --jq .login`
  - 结果：`mcontheway`。
- `git status --short --branch`
  - 结果：主仓为 `## main...origin/main`，无未提交改动。
- `git rev-parse HEAD && git rev-parse origin/main`
  - 结果：均为 `594231b9f18a459bc64b771c486b73808ecaf764`。
- `git worktree list --porcelain`
  - 结果：只剩主仓 `main` worktree。
- Phase / FR GitHub 状态：
  - `#293`：`closed completed`，`closed_at=2026-05-05T10:22:32Z`。
  - `#294`：`closed completed`，`closed_at=2026-04-30T09:06:01Z`。
  - `#295`：`closed completed`，`closed_at=2026-05-05T10:11:10Z`。
  - `#296`：`closed completed`，`closed_at=2026-05-03T13:02:59Z`。
  - `#297`：`closed completed`，`closed_at=2026-05-05T09:10:50Z`。
  - `#298`：`closed completed`，`closed_at=2026-05-05T08:05:29Z`。
- closeout Work Item / PR 状态：
  - `#312`：`closed completed`；PR `#344` 已合入，merge commit `594231b9f18a459bc64b771c486b73808ecaf764`。
  - `#322`：`closed completed`；PR `#343` 已合入，merge commit `c154f414428cc4a198b24e9c79fa32131d88b3d9`。
  - `#327`：`closed completed`；PR `#342` 已合入，merge commit `c0dc5bc77bca97a738549ef43f6fab6d560c9653`。
- `gh api 'repos/MC-and-his-Agents/Syvert/pulls?state=open&per_page=100'`
  - 结果：`[]`。
- `git ls-remote --heads origin 'issue-312*' 'issue-322*' 'issue-327*'`
  - 结果：无输出。
- `git tag --list 'v0.8.0*'`
  - 结果：无输出。
- `gh release view v0.8.0 --repo MC-and-his-Agents/Syvert --json tagName,name,url,isDraft,isPrerelease,publishedAt,targetCommitish`
  - 结果：当前无 GitHub Release `v0.8.0`。
- `python3 -m unittest tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_adapter_capability_requirement tests.runtime.test_reference_adapter_capability_requirement_baseline tests.runtime.test_provider_capability_offer tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard`
  - 结果：通过，`Ran 145 tests`。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `git diff --check`
  - 结果：通过。
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-345-v0-8-0-phase-release-closeout`
  - 结果：通过。
- 提交前 `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：当前分支相对基线没有已提交变更；提交后复跑。
- 提交后 `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`docs`，变更类别=`docs`。
- 提交后 `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-345-v0-8-0-phase-release-closeout`
  - 结果：通过。
- `python3 scripts/pr_guardian.py review 346 --post-review --json-output /tmp/syvert-pr-346-guardian.json`
  - 结果：`REQUEST_CHANGES`，`safe_to_merge=false`。阻断项是 `#327` post-merge closeout 协议与 closeout comment body 未达到 `#312/#322` evidence 粒度。
  - 处理：当前 follow-up 在 `docs/exec-plans/artifacts/GOV-0345-v0-8-0-phase-release-closeout-evidence.md` 新增 `FR-0026 Post-Merge GitHub Closeout 协议补录`，保存可复验 REST 步骤、comment body、`#327/#298/#293` 状态对账和不回写历史 carrier 的 ownership 说明。

## 待验证项

- guardian follow-up 后 docs / spec / workflow / governance / scope guard。
- guardian follow-up 后重新运行 guardian。
- PR guardian、GitHub checks、受控 merge。
- 阶段 A merge commit 上创建并推送 `v0.8.0` annotated tag。
- 创建 GitHub Release `v0.8.0`。
- 阶段 B 回写 published truth PR。
- `#345` closeout comment / close issue。
- worktree cleanup 与 branch retirement。

## closeout 证据

- 可复验 evidence artifact：`docs/exec-plans/artifacts/GOV-0345-v0-8-0-phase-release-closeout-evidence.md`。
- Release index：`docs/releases/v0.8.0.md`。
- Sprint index：`docs/sprints/2026-S21.md`。
- `#327` parent closeout record：
  - `docs/exec-plans/CHORE-0327-fr-0026-parent-closeout.md`（历史输入，不在本回合改写）
  - `docs/exec-plans/artifacts/CHORE-0327-fr-0026-parent-closeout-evidence.md`（历史输入，不在本回合改写）

## 风险

- 若 final closeout artifact 只重复 release 索引而不保存可复验 GitHub / Git 查询入口，会再次形成“口头完成但仓内不可复验”的缺口。
- 若 tag / GitHub Release 指向未经过阶段 A review / guardian / merge gate 的提交，会破坏 release closeout 的可审计性。
- 若 release / sprint 索引提前声明 published truth，会造成 tag / GitHub Release 与仓内文档分叉。
- 若 `#327` post-merge 记录补充被写回 `#327` 历史 exec-plan，会破坏 Work Item ownership；本事项只在 `GOV-0345` evidence 中补齐最终对账。
- 若本事项声明真实 provider 产品支持，会越过 `v0.8.0` 明确不在范围。

## 回滚方式

- 仓内回滚：使用独立 revert PR 撤销本事项新增的 `GOV-0345` exec-plan / ADR / evidence 与 release / sprint closeout 记录增量。
- 仓外回滚：若 tag / GitHub Release 已建立但主干事实有误，先修正主干与 GitHub truth，再按独立治理回合决定是否删除 / 重建发布锚点。
- GitHub issue 回滚：若本事项 closeout 后发现事实错误，使用 REST PATCH 重新打开 `#345`，追加纠正评论，并通过新的治理 Work Item 修正仓内事实。

## 最近一次 checkpoint 对应的 head SHA

- `594231b9f18a459bc64b771c486b73808ecaf764`
- 说明：该 checkpoint 对应 `v0.8.0` final main truth。当前事项只补齐 closeout record，不推进 runtime 或 formal spec checkpoint。
