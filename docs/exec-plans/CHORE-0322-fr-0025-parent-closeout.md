# CHORE-0322-fr-0025-parent-closeout 执行计划

## 关联信息

- item_key：`CHORE-0322-fr-0025-parent-closeout`
- Issue：`#322`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- Parent Phase：`#293`
- Parent FR：`#297`
- 关联 spec：`docs/specs/FR-0025-provider-capability-offer-contract/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0322-fr-0025-parent-closeout`
- 状态：`active`

## 目标

- 汇总 `FR-0025` formal spec、Provider offer manifest / validator、SDK docs / evidence、review、guardian、主干事实与 GitHub 状态。
- 关闭父 FR `#297`，让 `#298 / FR-0026` 与 Phase `#293` 后续 closeout 可消费 Provider offer input truth。
- 保持本 closeout 为 docs / metadata 收口，不修改 `FR-0025` formal spec 正文、runtime、tests 或 `FR-0026` 语义。

## 范围

- 本次纳入：
  - `docs/exec-plans/CHORE-0322-fr-0025-parent-closeout.md`
  - `docs/exec-plans/artifacts/CHORE-0322-fr-0025-parent-closeout-evidence.md`
  - `docs/releases/v0.8.0.md`
  - `docs/sprints/2026-S21.md`
- 本次不纳入：
  - `docs/specs/FR-0025-provider-capability-offer-contract/**` 正文修改
  - `syvert/**`
  - `tests/**`
  - `scripts/**`
  - `FR-0026` compatibility decision 实现或 closeout
  - 把 Provider offer 的 `declared` 语义改写为 `matched`
  - 真实 provider 样本、provider selector、priority、fallback、marketplace 或产品支持承诺
  - Phase `#293` closeout

## 当前停点

- worktree：`/Users/mc/code/worktrees/syvert/issue-322-fr-0025`
- 分支：`issue-322-fr-0025`
- worktree 创建基线：`24ae582447165596a54edacb35568ab4c73a55cb`
- 已快进到 `origin/main=c0dc5bc77bca97a738549ef43f6fab6d560c9653`，保留已合入的 `#327 / PR #342` 主干 truth，不触碰 `/Users/mc/code/worktrees/syvert/issue-327-fr-0026`。
- 已确认子 Work Item 状态：
  - `#319` closed completed，formal spec closeout 已合入。
  - `#320` closed completed，Provider offer manifest / validator 已合入。
  - `#321` closed completed，SDK docs / evidence 已合入。
  - `#322` open，当前父 FR closeout 执行入口。
- 当前 checkpoint：已新增父 FR closeout evidence artifact，并更新 release/sprint 索引入口。本文档只做 closeout 证据与状态收口，不新增 spec/runtime/decision 语义。

## 下一步动作

- 运行 docs class 的 scope / governance 门禁。
- 提交并通过受控入口创建 docs PR。
- 等待 GitHub checks，运行 guardian review；guardian 不设置超时限制。
- guardian `APPROVE` 且 `safe_to_merge=true` 后，使用受控 merge 入口合入。
- 合入后使用 GitHub REST 在 `#297` 写入 closeout comment 并关闭为 `completed`；确认 `#322` 自动关闭，必要时使用 REST 补关闭。
- 在 Phase `#293` comment 记录 `FR-0025` closeout 事实，不关闭 Phase。
- 清理 worktree 并退役分支。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 固定 Provider capability offer 的父 FR closeout truth，使后续 `FR-0026` 只消费 `FR-0025` 的已批准 Provider offer input，不反向改写 offer carrier。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0025` 的 parent closeout Work Item。
- 阻塞：
  - `#298 / FR-0026` compatibility decision closeout 需要 `FR-0025` 作为 Provider offer input。
  - Phase `#293` closeout 需要 `FR-0025` 的 GitHub 状态、主干事实与 release/sprint 索引保持一致。

## closeout 证据

- formal spec 证据：
  - PR `#328`：新增并收口 `docs/specs/FR-0025-provider-capability-offer-contract/`，冻结 `ProviderCapabilityOffer` canonical carrier、固定字段、Adapter-bound provider identity、resource support、error carrier、version、evidence、lifecycle、observability、fail-closed 与禁止 Core provider discovery / routing 边界。
  - 主干路径：`docs/specs/FR-0025-provider-capability-offer-contract/`、`docs/exec-plans/CHORE-0319-fr-0025-formal-spec-closeout.md`。
- manifest / validator 证据：
  - PR `#335`：新增 `syvert/provider_capability_offer.py`、fixture 与 runtime tests，使合法 offer、invalid contract 与 scope drift 能稳定区分；selector、priority、fallback、marketplace、Core routing hint 与 compatibility decision 字段 fail-closed。
  - 主干路径：`syvert/provider_capability_offer.py`、`tests/runtime/provider_capability_offer_fixtures.py`、`tests/runtime/test_provider_capability_offer.py`、`docs/exec-plans/CHORE-0320-fr-0025-offer-manifest-validator.md`。
- SDK docs / evidence 证据：
  - PR `#338`：补齐 Adapter SDK 与 evidence artifact，说明 `ProviderCapabilityOffer` 的作者路径、fixture refs、validator 结论、Adapter-bound 边界与后续 `FR-0026` 消费关系。
  - 主干路径：`adapter-sdk.md`、`docs/exec-plans/CHORE-0321-fr-0025-sdk-docs-evidence.md`、`docs/exec-plans/artifacts/CHORE-0321-fr-0025-provider-offer-sdk-evidence.md`。
- GitHub / main provenance：
  - 可复验证据保存于 `docs/exec-plans/artifacts/CHORE-0322-fr-0025-parent-closeout-evidence.md`。
  - `#319/#320/#321` 均已关闭为 completed；父 FR `#297` 仍 open，等待本 closeout PR 合入后关闭；Phase `#293` 仍 open。
  - `#328/#335/#338` 的 merge commit 均为 `origin/main` ancestor，且主干包含 FR-0025 spec、validator、tests、SDK 与 evidence 路径。

## 已验证项

- `gh api user --jq .login`
  - 结果：通过；确认本机 `gh` keyring 可用，返回 `mcontheway`，未全局导出 `GH_TOKEN` / `GITHUB_TOKEN`。
- `python3 scripts/create_worktree.py --issue 322 --class docs`
  - 结果：通过；创建 worktree `/Users/mc/code/worktrees/syvert/issue-322-fr-0025`，分支 `issue-322-fr-0025`，基线 `24ae582447165596a54edacb35568ab4c73a55cb`。
- `git merge --ff-only origin/main`
  - 结果：通过；快进到 `c0dc5bc77bca97a738549ef43f6fab6d560c9653`，消费已合入的 #327 主干索引，不覆盖其 worktree。
- GitHub issue status：
  - `#319/#320/#321`：closed completed。
  - `#322`：open，当前执行入口。
  - `#297`：open，等待本 closeout PR 合入后关闭。
  - `#293`：open，本事项不关闭 Phase。
- GitHub PR / main provenance：
  - `#328/#335/#338`：均为 `merged=true`、`state=closed`。
  - `git merge-base --is-ancestor <merge_commit_sha> origin/main`：`#328/#335/#338` 的 merge commit 均通过。
  - `git cat-file -e origin/main:<path>`：FR-0025 formal spec、validator、tests、SDK 与 evidence 路径均存在。
- `rg -n "declared|matched|ProviderCapabilityOffer|provider offer" ...`
  - 结果：通过；确认 `ProviderCapabilityOffer` 合法结果仍是 `declared`，`matched` 仅由后续 `FR-0026` compatibility decision 产生。
- `git diff --check`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-322-fr-0025`
  - 结果：通过。
- 提交前 `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：首次运行因新增文件尚未进入 Git diff，返回“当前分支相对基线没有变更”；提交后复跑。
- `git commit -m 'docs(closeout): 收口 FR-0025 父事项'`
  - 结果：已生成 closeout semantic checkpoint `317f7a66fbf1f2d6ef5ea08946af52504f83586b`。
- 提交后 `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`docs`，变更类别=`docs`。
- `python3 scripts/pr_guardian.py review 343 --post-review --json-output /tmp/syvert-pr-343-guardian.json`
  - 结果：首轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项是 closeout exec-plan 中一处 main-sync 验证记录保留了不存在的 SHA；当前 follow-up 修正为真实 `origin/main=c0dc5bc77bca97a738549ef43f6fab6d560c9653`，并复核 evidence artifact 与 checkpoint 区域 SHA 一致。
- guardian follow-up 后 `git diff --check`
  - 结果：通过。
- guardian follow-up 后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- guardian follow-up 后 `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- guardian follow-up 后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- guardian follow-up 后 `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-322-fr-0025`
  - 结果：通过。
- guardian follow-up 后 `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`docs`，变更类别=`docs`。
- `python3 scripts/pr_guardian.py review 343 --post-review --json-output /tmp/syvert-pr-343-guardian-db97557.json`
  - 结果：第二轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项是当前受审 head `db9755728c85c008b264d009e88d83e8953ff11e` 的 follow-up 后 docs class gates 未落盘；当前 follow-up 只补充上述门禁记录，不改变 `FR-0025` semantic checkpoint。
- head `d02e8d27d707ccc0dec4667dd36e3149390dcb28` 后 `git diff --check`
  - 结果：通过。
- head `d02e8d27d707ccc0dec4667dd36e3149390dcb28` 后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- head `d02e8d27d707ccc0dec4667dd36e3149390dcb28` 后 `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- head `d02e8d27d707ccc0dec4667dd36e3149390dcb28` 后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- head `d02e8d27d707ccc0dec4667dd36e3149390dcb28` 后 `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-322-fr-0025`
  - 结果：通过。
- head `d02e8d27d707ccc0dec4667dd36e3149390dcb28` 后 `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`docs`，变更类别=`docs`。
- head `d02e8d27d707ccc0dec4667dd36e3149390dcb28` 后 `gh api repos/:owner/:repo/commits/d02e8d27d707ccc0dec4667dd36e3149390dcb28/check-runs --jq '{total_count,check_runs:[.check_runs[] | {name,status,conclusion}]}'`
  - 结果：4 个 check runs 全部 `success`。
- `python3 scripts/pr_guardian.py review 343 --post-review --json-output /tmp/syvert-pr-343-guardian-d02e8d2.json`
  - 结果：第三轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项：
    - 当前受审 head `d02e8d27d707ccc0dec4667dd36e3149390dcb28` 的门禁 / guardian 证据未落盘。
    - 父 FR `#297` 的 post-merge closeout comment / close issue 对账协议未版本化。
  - 当前 follow-up 将上述 head 的 gates / checks / guardian 结果落盘，并在 evidence artifact 中固定 `#297/#293` post-merge REST closeout 协议；不提前关闭 `#297`。
- post-merge closeout protocol follow-up 后 `git diff --check`
  - 结果：通过。
- post-merge closeout protocol follow-up 后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- post-merge closeout protocol follow-up 后 `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- post-merge closeout protocol follow-up 后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- post-merge closeout protocol follow-up 后 `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-322-fr-0025`
  - 结果：通过。
- post-merge closeout protocol follow-up 后 `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`docs`，变更类别=`docs`。
- `python3 scripts/pr_guardian.py review 343 --post-review --json-output /tmp/syvert-pr-343-guardian-b897bac.json`
  - 结果：第四轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项是 release / sprint 索引与 closeout evidence 发生事实漂移：
    - `docs/releases/v0.8.0.md` 仍把 `#319` 写成负责 formal spec closeout，而不是已完成并合入主干。
    - `docs/sprints/2026-S21.md` 把 `#320` 误归类为 docs / evidence / parent closeout，而不是 offer manifest / validator。
  - 当前 follow-up 同步 release / sprint 索引，使 `#319/#320/#321/#322` 职责与本 closeout evidence 一致。
- release / sprint 索引 follow-up 后 `git diff --check`
  - 结果：通过。
- release / sprint 索引 follow-up 后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- release / sprint 索引 follow-up 后 `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- release / sprint 索引 follow-up 后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- release / sprint 索引 follow-up 后 `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-322-fr-0025`
  - 结果：通过。
- release / sprint 索引 follow-up 后 `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`docs`，变更类别=`docs`。

## 待验证项

- guardian review、GitHub checks、受控 merge。
- 按 evidence artifact 的 post-merge closeout 协议执行 `#297` closeout comment / close issue。
- 按 evidence artifact 的 post-merge closeout 协议执行 Phase `#293` progress comment。
- worktree cleanup 与 branch retirement。

## 未决风险

- 本 PR 合入前不得关闭 `#297`；否则 GitHub 状态会早于仓内 closeout truth。
- 若 closeout 文档把 `declared` offer 写成 `matched` 或 compatibility approved，会越过 `FR-0025` 边界并破坏 `FR-0026` 职责。
- 若 release / sprint 索引覆盖已合入的 `#327 / PR #342` 主干入口，会破坏并行 agent 已完成的 FR-0026 truth。
- 若后续要改变 `ProviderCapabilityOffer` carrier 本体，必须回到 `FR-0025` formal spec 或 validator Work Item，不得在 parent closeout 中隐式改写。

## 回滚方式

- 仓内回滚：使用独立 revert PR 撤销本 closeout exec-plan、evidence artifact 与 release / sprint closeout 索引。
- GitHub 侧回滚：若关闭后发现事实不一致，使用 REST PATCH 重新打开 `#297` 或 `#322`，追加纠正评论，并通过新的 closeout Work Item 修正仓内事实。

## 最近一次 checkpoint 对应的 head SHA

- worktree 创建基线：`24ae582447165596a54edacb35568ab4c73a55cb`
- main sync 基线：`c0dc5bc77bca97a738549ef43f6fab6d560c9653`
- closeout semantic checkpoint：`317f7a66fbf1f2d6ef5ea08946af52504f83586b`
- checkpoint record follow-up：当前后续提交只回填 checkpoint SHA，不改变 `FR-0025` semantic checkpoint；受审 head 以 PR head SHA 与 guardian / merge gate 绑定。
- 本 exec-plan 是 `#322` 的首个版本化恢复工件；后续 review-sync 若只更新验证记录或 GitHub 状态，不推进新的 formal spec / runtime 语义。
