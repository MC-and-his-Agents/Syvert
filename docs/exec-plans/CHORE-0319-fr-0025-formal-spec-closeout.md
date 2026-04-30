# CHORE-0319-fr-0025-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0319-fr-0025-formal-spec-closeout`
- Issue：`#319`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0025-provider-capability-offer-contract/`
- 关联 decision：
- 关联 PR：`#328`
- active 收口事项：`CHORE-0319-fr-0025-formal-spec-closeout`
- 状态：`active`

## 目标

- 创建并收口 `FR-0025` formal spec 套件，冻结 Provider capability offer canonical carrier、字段边界、evidence、version、error carrier 与 fail-closed 语义，为 `#320/#321/#322` 与后续 `FR-0026` compatibility decision 提供 implementation-ready formal input。

## 范围

- 本次纳入：
  - `docs/specs/FR-0025-provider-capability-offer-contract/spec.md`
  - `docs/specs/FR-0025-provider-capability-offer-contract/plan.md`
  - `docs/specs/FR-0025-provider-capability-offer-contract/data-model.md`
  - `docs/specs/FR-0025-provider-capability-offer-contract/contracts/README.md`
  - `docs/specs/FR-0025-provider-capability-offer-contract/risks.md`
  - `docs/exec-plans/CHORE-0319-fr-0025-formal-spec-closeout.md`
  - 必要的 `docs/releases/v0.8.0.md` 与 `docs/sprints/2026-S21.md` 索引入口
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `scripts/**`
  - `.github/**`
  - runtime provider implementation、manifest validator、SDK docs evidence 或 contract test 实现
  - `FR-0024`、`FR-0027` 或 `FR-0026` formal spec 修改
  - compatibility decision
  - provider selector、priority、fallback、marketplace 或真实 provider 产品支持
  - Core provider discovery / routing
  - 关闭父 FR `#297`
  - 无关未跟踪目录 `compatibility`

## 当前停点

- worktree：`/Users/mc/code/worktrees/syvert/issue-319-fr-0025-provider-capability-offer-formal-spec`
- 分支：`issue-319-fr-0025-provider-capability-offer-formal-spec`
- 原始 worktree 创建基线：`589ea1e73ebce464ac16d292c180e08cee302ce5`
- 已核对 `AGENTS.md`、`WORKFLOW.md`、`spec_review.md`、`FR-0021`、`FR-0024`、`FR-0027`、`#297`、`#298` 与 `#319` GitHub truth。
- 当前 checkpoint：已创建 `FR-0025` formal spec 套件与 active exec-plan；PR `#328` 已通过受控入口创建并绑定 `Fixes #319`，待 spec review / guardian、merge 与 closeout。

## 下一步动作

- 跑 `spec_guard --all`、`docs_guard`、`workflow_guard`、`governance_gate` 与 `pr_scope_guard --class spec`。
- 使用中文 Conventional Commit 提交 formal spec checkpoint。
- 使用 `scripts/open_pr.py` 受控创建 spec PR，并绑定 `Fixes #319`。
- 完成 spec review、guardian review、GitHub checks 与受控 merge。
- 合入后确认 `#319` closeout，更新父 FR `#297` GitHub comment，清理 worktree 并退役分支。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 把 Provider capability offer 从路线图目标推进为可审查、可验证、可被 manifest / SDK / compatibility decision 消费的 formal contract。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0025` 的 formal spec closeout Work Item。
- 阻塞：
  - `#320` Provider offer manifest validator 需要本 carrier 作为校验目标。
  - `#321` SDK docs / evidence 需要本 carrier 作为文档与证据目标。
  - `#322` 父 FR closeout 需要本 spec、validator、docs / evidence 与 GitHub 状态主干事实。
  - `FR-0026` compatibility decision 需要本 FR 作为 Provider offer input。

## 已验证项

- `python3 scripts/create_worktree.py --issue 319 --class spec`
  - 结果：通过，创建 worktree `issue-319-fr-0025-provider-capability-offer-formal-spec`
- `gh api user --jq .login`
  - 结果：通过，确认本机 `gh` keyring 可用，登录用户为 `mcontheway`
- 已核对 `AGENTS.md`、`WORKFLOW.md`、`spec_review.md`。
- 已核对 `#319` GitHub truth：item_key=`CHORE-0319-fr-0025-formal-spec-closeout`，item_type=`CHORE`，release=`v0.8.0`，sprint=`2026-S21`，integration fields 为 `none/no/local_only`。
- 已核对父 FR `#297` 保持 open，目标为冻结 Provider capability offer 声明契约，明确不定义 compatibility decision、provider selector、fallback priority、marketplace 或真实 provider 产品支持。
- 已核对 `#298`，确认 compatibility decision 属于 `FR-0026`，本事项不得定义 requirement x offer decision。
- 已核对 `FR-0024` formal spec，确认本 FR 必须消费 `AdapterCapabilityRequirement` 作为后续 decision 输入，不反向改写 requirement carrier。
- 已核对 `FR-0027` formal spec，确认 resource support 必须消费 `AdapterResourceRequirementDeclarationV2` 的 profile tuple、approved execution slice 与 proof binding 语义，不重写 matcher / proof truth。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-319-fr-0025-provider-capability-offer-formal-spec`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`spec`，变更类别=`docs, spec`
- `git commit -m 'docs(spec): 收口 FR-0025 provider offer 规约'`
  - 结果：已生成语义 checkpoint `9f9b54e17382a40b59a38647d69c261505202ad5`
- `git commit -m 'docs(spec): 记录 FR-0025 规约验证结果'`
  - 结果：已生成 validation follow-up checkpoint `32d6fb53abd8b245bc06c8386ab422edc74bbedc`
- `git push -u origin issue-319-fr-0025-provider-capability-offer-formal-spec`
  - 结果：通过，远端分支已创建并设置 upstream
- `python3 scripts/open_pr.py --class spec --issue 319 --item-key CHORE-0319-fr-0025-formal-spec-closeout --item-type CHORE --release v0.8.0 --sprint 2026-S21 --title 'docs(spec): 收口 FR-0025 Provider capability offer formal spec' --closing fixes --integration-touchpoint none --shared-contract-changed no --integration-ref none --external-dependency none --merge-gate local_only --contract-surface none --joint-acceptance-needed no --integration-status-checked-before-pr no --integration-status-checked-before-merge no`
  - 结果：已创建当前受审 spec PR `#328 https://github.com/MC-and-his-Agents/Syvert/pull/328`

## 待验证项

- PR `#328` 最新 head 的 spec review、guardian review、GitHub checks 与受控 merge gate

## 未决风险

- 若后续 `#320/#321` 在未消费本 spec 的情况下实现自己的 offer shape，会形成 manifest / SDK / decision 三套 truth。
- 若后续 `FR-0026` 反向改写 offer carrier，会破坏 requirement / offer / decision 的分层边界。
- 若 provider key、lifecycle 或 observability 字段被实现为 Core provider registry、routing、selector 或 marketplace，会破坏 Core / Adapter / Provider 边界。

## 回滚方式

- 使用独立 revert PR 撤销 `docs/specs/FR-0025-provider-capability-offer-contract/`、本 exec-plan 与 release/sprint 索引增量。
- 若需要改变 offer 声明边界，必须先回到父 FR `#297` 更新 GitHub truth，不得在后续 implementation PR 中隐式改写。

## 最近一次 checkpoint 对应的 head SHA

- formal spec 语义 checkpoint：`9f9b54e17382a40b59a38647d69c261505202ad5`
- validation result follow-up checkpoint：`32d6fb53abd8b245bc06c8386ab422edc74bbedc`
- worktree 创建基线：`589ea1e73ebce464ac16d292c180e08cee302ce5`
