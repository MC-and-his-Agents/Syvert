# CHORE-0312-fr-0023-parent-closeout 执行计划

## 关联信息

- item_key：`CHORE-0312-fr-0023-parent-closeout`
- Issue：`#312`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- Parent Phase：`#293`
- Parent FR：`#295`
- 关联 spec：`docs/specs/FR-0023-third-party-adapter-entry-path/`
- 关联 decision：
- 关联 PR：`#344`
- active 收口事项：`CHORE-0312-fr-0023-parent-closeout`
- 状态：`active`

## 目标

- 汇总 `FR-0023` formal spec、resource proof admission bridge、third-party contract test entry、SDK docs / migration、主干事实与 GitHub 状态。
- 关闭父 FR `#295`，让 Phase `#293` 后续 closeout 可消费第三方 Adapter-only 接入路径 truth。
- 保持本 closeout 为 docs / metadata 收口，不修改 `FR-0023` formal spec 正文、runtime、tests 或 Provider offer / compatibility decision 语义。

## 范围

- 本次纳入：
  - `docs/exec-plans/CHORE-0312-fr-0023-parent-closeout.md`
  - `docs/exec-plans/artifacts/CHORE-0312-fr-0023-parent-closeout-evidence.md`
  - `docs/releases/v0.8.0.md`
  - `docs/sprints/2026-S21.md`
- 本次不纳入：
  - `docs/specs/FR-0023-third-party-adapter-entry-path/**` 正文修改
  - `syvert/**`
  - `tests/**`
  - `scripts/**`
  - Provider offer、compatibility decision、provider selector / registry / marketplace 语义
  - 真实外部 provider 样本
  - Phase `#293` closeout

## 当前停点

- worktree：`/Users/mc/code/worktrees/syvert/issue-312-fr-0023`
- 分支：`issue-312-fr-0023`
- worktree 创建基线：`c154f414428cc4a198b24e9c79fa32131d88b3d9`
- 已确认子 Work Item 状态：
  - `#309` closed completed，formal spec closeout 已合入。
  - `#331` closed completed，resource proof admission bridge 已合入。
  - `#310` closed completed，third-party contract test entry 已合入。
  - `#311` closed completed，SDK docs / migration 已合入。
  - `#312` open，当前父 FR closeout 执行入口。
- 当前 checkpoint：新增父 FR closeout evidence artifact，并更新 release/sprint 索引入口。本文档只做 closeout 证据与状态收口，不新增 spec/runtime/provider 语义。

## 下一步动作

- 当前 live PR：`#344`。
- 等待 / 核对 GitHub checks，运行 guardian review；guardian 不设置超时限制。
- guardian `APPROVE` 且 `safe_to_merge=true` 后，使用受控 merge 入口合入。
- 合入后使用 GitHub REST 在 `#295` 写入 closeout comment 并关闭为 `completed`；确认 `#312` 自动关闭，必要时使用 REST 补关闭。
- 在 Phase `#293` comment 记录 `FR-0023` closeout 事实，不关闭 Phase。
- 清理 worktree并退役分支。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 固定第三方 Adapter-only 稳定接入路径的父 FR closeout truth，使后续 Phase closeout 能消费 `FR-0023` 的 manifest、resource proof admission、contract entry 与 SDK docs 事实。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0023` 的 parent closeout Work Item。
- 阻塞：
  - Phase `#293` closeout 需要 `FR-0023` 的 GitHub 状态、主干事实与 release/sprint 索引保持一致。

## closeout 证据

- formal spec 证据：
  - PR `#318`：新增并收口 `docs/specs/FR-0023-third-party-adapter-entry-path/`，冻结第三方 Adapter 最小 public metadata、Adapter-only manifest / fixture / contract test 准入、迁移与升级约束。
  - 主干路径：`docs/specs/FR-0023-third-party-adapter-entry-path/`、`docs/exec-plans/CHORE-0309-fr-0023-formal-spec-closeout.md`。
- resource proof admission bridge 证据：
  - PR `#334`：冻结 manifest-owned `resource_proof_admissions`、逐 profile `ThirdPartyResourceProofAdmission` 与 `AdmissionEvidenceRef` schema，使真实第三方 `adapter_key` 可合法消费 `FR-0027` approved shared profile proof，不放宽 `FR-0027` shape / proof lookup / tuple / execution path / fail-closed 规则。
  - 主干路径：`docs/specs/FR-0023-third-party-adapter-entry-path/`、`docs/exec-plans/CHORE-0331-fr-0023-third-party-resource-proof-bridge.md`。
- contract test entry 证据：
  - PR `#330`：新增第三方 Adapter contract test entry 与 fixture truth，覆盖 manifest shape、public metadata、resource declaration、resource proof admission refs、fixture coverage、success raw / normalized 与 error mapping fail-closed。
  - 主干路径：`tests/runtime/contract_harness/third_party_entry.py`、`tests/runtime/contract_harness/third_party_fixtures.py`、`tests/runtime/test_third_party_adapter_contract_entry.py`、`docs/exec-plans/CHORE-0310-fr-0023-contract-test-entry.md`。
- SDK docs / migration 证据：
  - PR `#337`：补齐 Adapter SDK 作者入口，说明 `run_third_party_adapter_contract_test()`、manifest / fixture validator、resource proof admission 与 Adapter-only vs Adapter + Provider 边界。
  - 主干路径：`adapter-sdk.md`、`docs/exec-plans/CHORE-0311-fr-0023-sdk-docs-migration.md`。
- GitHub / main provenance：
  - 可复验证据保存于 `docs/exec-plans/artifacts/CHORE-0312-fr-0023-parent-closeout-evidence.md`。
  - `#309/#331/#310/#311` 均已关闭为 completed；父 FR `#295` 仍 open，等待本 closeout PR 合入后关闭；Phase `#293` 仍 open。
  - `#318/#334/#330/#337` 的 merge commit 均为 `origin/main` ancestor，且主干包含 FR-0023 spec、bridge、contract entry、tests、SDK 与 evidence 路径。

## 已验证项

- `python3 scripts/create_worktree.py --issue 312 --class docs`
  - 结果：通过；创建 worktree `/Users/mc/code/worktrees/syvert/issue-312-fr-0023`，分支 `issue-312-fr-0023`，基线 `c154f414428cc4a198b24e9c79fa32131d88b3d9`。
- `gh api repos/:owner/:repo/issues/312 --jq '{number,title,state,state_reason,body,labels:[.labels[].name]}'`
  - 结果：`#312` open，item_key=`CHORE-0312-fr-0023-parent-closeout`，release=`v0.8.0`，sprint=`2026-S21`，父 FR=`#295`。
- `gh api repos/:owner/:repo/issues/295 --jq '{number,title,state,state_reason,body,labels:[.labels[].name]}'`
  - 结果：父 FR `#295` open，关闭条件要求 formal spec、contract test entry、SDK / docs / contract test 准入说明与 roadmap / release / decision 保持一致。
- GitHub issue status：
  - `#309/#331/#310/#311`：closed completed。
  - `#312`：open，当前执行入口。
  - `#295`：open，等待本 closeout PR 合入后关闭。
  - `#293`：open，本事项不关闭 Phase。
- GitHub PR / main provenance：
  - `#318/#334/#330/#337`：均为 `merged=true`、`state=closed`。
  - `git merge-base --is-ancestor <merge_commit_sha> origin/main`：`#318/#334/#330/#337` 的 merge commit 均通过。
  - `git cat-file -e origin/main:<path>`：FR-0023 formal spec、resource proof bridge exec-plan、contract entry、fixtures、tests、SDK docs 与 docs exec-plan 路径均存在。
- `git diff --check`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-312-fr-0023`
  - 结果：通过。
- 提交前 `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：首次运行因新增文件尚未进入 Git diff，返回“当前分支相对基线没有变更”；提交后复跑。
- `git commit -m 'docs(closeout): 收口 FR-0023 父事项'`
  - 结果：已生成 closeout semantic checkpoint `bbc9af6623d8972243bda4cb6305d232ffd6384f`。
- 提交后 `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`docs`，变更类别=`docs`。
- 提交后 `git diff --check`
  - 结果：通过。
- 提交后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- 提交后 `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- 提交后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- 提交后 `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-312-fr-0023`
  - 结果：通过。
- `python3 scripts/open_pr.py --class docs --issue 312 --item-key CHORE-0312-fr-0023-parent-closeout --item-type CHORE --release v0.8.0 --sprint 2026-S21 --title 'docs(closeout): 收口 FR-0023 父事项' --closing fixes --integration-touchpoint none --shared-contract-changed no --integration-ref none --external-dependency none --merge-gate local_only --contract-surface none --joint-acceptance-needed no --integration-status-checked-before-pr no --integration-status-checked-before-merge no`
  - 结果：通过；创建 PR `#344`。
- `python3 scripts/pr_guardian.py review 344 --post-review --json-output /tmp/syvert-pr-344-guardian-0e0bbfe.json`
  - 结果：首轮 `REQUEST_CHANGES`，`safe_to_merge=false`。阻断项是 release / sprint 的 exec-plan 索引遗漏本 PR 新增的 `CHORE-0312` closeout 工件。
  - 当前 follow-up 在 `docs/releases/v0.8.0.md` 与 `docs/sprints/2026-S21.md` 的 exec-plan 列表中补入 `docs/exec-plans/CHORE-0312-fr-0023-parent-closeout.md` 与 `docs/exec-plans/artifacts/CHORE-0312-fr-0023-parent-closeout-evidence.md`。
- `CHORE-0312` 索引 follow-up 后 `git diff --check`
  - 结果：通过。
- `CHORE-0312` 索引 follow-up 后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `CHORE-0312` 索引 follow-up 后 `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `CHORE-0312` 索引 follow-up 后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `CHORE-0312` 索引 follow-up 后 `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-312-fr-0023`
  - 结果：通过。
- `CHORE-0312` 索引 follow-up 后 `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`docs`，变更类别=`docs`。

## 待验证项

- GitHub checks、guardian review、受控 merge。
- 按 evidence artifact 的 post-merge closeout 协议执行 `#295` closeout comment / close issue。
- 按 evidence artifact 的 post-merge closeout 协议执行 Phase `#293` progress comment。
- worktree cleanup 与 branch retirement。

## 未决风险

- 本 PR 合入前不得关闭 `#295`；否则 GitHub 状态会早于仓内 closeout truth。
- 若 closeout 文档把第三方 Adapter 接入扩张为 provider 产品接入、selector、registry 或 marketplace，会越过 `FR-0023` Adapter-only 边界。
- 若漏掉 `#331` bridge，`FR-0023` closeout 会低估真实第三方 `adapter_key` 与 `FR-0027` approved proof coverage 的 formal/evidence 前提。
- 若后续要改变 third-party adapter manifest / proof admission / contract entry 语义，必须回到 formal spec 或 implementation Work Item，不得在 parent closeout 中隐式改写。

## 回滚方式

- 仓内回滚：使用独立 revert PR 撤销本 closeout exec-plan、evidence artifact 与 release / sprint closeout 索引。
- GitHub 侧回滚：若关闭后发现事实不一致，使用 REST PATCH 重新打开 `#295` 或 `#312`，追加纠正评论，并通过新的 closeout Work Item 修正仓内事实。

## 最近一次 checkpoint 对应的 head SHA

- worktree 创建基线：`c154f414428cc4a198b24e9c79fa32131d88b3d9`
- closeout semantic checkpoint：`bbc9af6623d8972243bda4cb6305d232ffd6384f`
- live-head evidence policy：版本化工件记录历史 review 证据与可复验 REST 查询入口，不硬编码“当前 live head”；当前 live head、checks 与 guardian state 由当前 PR、GitHub checks 与 guardian merge gate 绑定。
