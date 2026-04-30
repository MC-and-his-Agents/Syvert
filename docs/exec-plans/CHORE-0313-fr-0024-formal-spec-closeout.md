# CHORE-0313-fr-0024-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0313-fr-0024-formal-spec-closeout`
- Issue：`#313`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0024-adapter-capability-requirement-contract/`
- 关联 decision：
- 关联 PR：`#317`
- active 收口事项：`CHORE-0313-fr-0024-formal-spec-closeout`
- 状态：`active`

## 目标

- 创建并收口 `FR-0024` formal spec 套件，冻结 Adapter capability requirement canonical carrier，并消费 `FR-0027` 的 resource requirement profiles / proof binding，为 `#314/#315/#316` 提供 implementation-ready formal input。

## 范围

- 本次纳入：
  - `docs/specs/FR-0024-adapter-capability-requirement-contract/spec.md`
  - `docs/specs/FR-0024-adapter-capability-requirement-contract/plan.md`
  - `docs/specs/FR-0024-adapter-capability-requirement-contract/data-model.md`
  - `docs/specs/FR-0024-adapter-capability-requirement-contract/contracts/README.md`
  - `docs/specs/FR-0024-adapter-capability-requirement-contract/risks.md`
  - `docs/exec-plans/CHORE-0313-fr-0024-formal-spec-closeout.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - runtime matcher、manifest validator、reference adapter migration 或 contract test 实现
  - Provider capability offer
  - compatibility decision
  - profile priority、排序、自动 fallback、打分或 provider selector
  - 新共享能力词汇
  - 关闭父 FR `#296`
  - `#309` worktree 或无关文件

## 当前停点

- worktree：`/Users/mc/code/worktrees/syvert/issue-313-fr-0024-adapter-capability-requirement-formal-spec`
- 分支：`issue-313-fr-0024-adapter-capability-requirement-formal-spec`
- 原始 worktree 创建基线：`16c4b8b137f38a1d494f08163fc4ad8a8eb10f68`
- 已核对 `AGENTS.md`、`WORKFLOW.md`、`spec_review.md`、`FR-0027` formal spec、`FR-0021` formal spec、`#296` 与 `#313` GitHub truth。
- 当前 checkpoint：已创建 `FR-0024` formal spec 套件与 active exec-plan；PR `#317` 已通过受控入口创建并绑定 `Fixes #313`，当前回合停点为修正 guardian 审查发现的 exec-plan 状态漂移后等待 review / merge gate 收口。

## 下一步动作

- 在 PR `#317` 上完成 guardian review、GitHub checks 与受控 merge。
- PR `#317` 合入后由 `Fixes #313` 关闭当前 Work Item；父 FR `#296` 保持 open，等待 `#314/#315/#316` 后续收口。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 把 Adapter capability requirement 从路线图目标推进为可审查、可验证、可被 manifest / SDK / reference adapter migration 消费的 formal contract。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0024` 的 formal spec closeout Work Item。
- 阻塞：
  - `#314` manifest fixture validator 需要本 carrier 作为校验目标。
  - `#315` reference adapter requirement migration 需要本 carrier 作为迁移目标。
  - `#316` 父 FR closeout 需要本 spec、validator 与 migration 主干事实。
  - 后续 Provider offer / compatibility decision 需要本 FR 作为 requirement input。

## 已验证项

- `gh api repos/:owner/:repo/issues/313 --jq '{number,title,state,labels:[.labels[].name],milestone:.milestone.title,body}'`
  - 结果：通过；确认 `#313` open，item_key=`CHORE-0313-fr-0024-formal-spec-closeout`，release=`v0.8.0`，sprint=`2026-S21`，scope 为 `FR-0024` formal spec closeout。
- `gh api repos/:owner/:repo/issues/296 --jq '{number,title,state,labels:[.labels[].name],body}'`
  - 结果：通过；确认父 FR `#296` open，目标为冻结 Adapter capability requirement 声明契约，明确不定义 Provider offer / decision / profile fallback / 新共享能力词汇。
- 已核对 `AGENTS.md`、`WORKFLOW.md`、`spec_review.md`。
- 已核对 `docs/specs/FR-0027-multi-profile-resource-requirement-contract/`，确认 `FR-0024` 必须消费 `AdapterResourceRequirementDeclarationV2` 与 `ApprovedSharedResourceRequirementProfileEvidenceEntry`，不重写 profile truth。
- 已核对 `docs/specs/FR-0021-adapter-provider-port-boundary/`，确认本 FR 不把 provider port 升格为 Core-facing provider SDK 或 provider offer。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-313-fr-0024-adapter-capability-requirement-formal-spec`
  - 结果：首次尝试未通过；原因是该脚本只消费已提交的 `HEAD` diff，当前新增 formal spec 尚未提交，返回“绑定 Issue 的实现事项缺少 formal spec 或 bootstrap contract”。提交 checkpoint 后必须重跑。
- `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
  - 结果：首次尝试未通过；原因是该脚本只消费已提交的 `HEAD` diff，当前新增文件尚未提交，返回“当前分支相对基线没有变更，无法创建或校验 PR”。提交 checkpoint 后必须重跑。
- `git commit -m 'docs(spec): 收口 FR-0024 适配器能力需求规约'`
  - 结果：已生成语义 checkpoint `59bed8351a7b1758cad9cbaf4afac3ab456f927b`
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-313-fr-0024-adapter-capability-requirement-formal-spec`
  - 结果：未通过；`关联 decision：无` 被解析为有意义路径，触发“必须绑定到 `docs/decisions/*.md`”；同时 formal spec input 绑定因此未通过 preflight。处理：将 `关联 decision` 留空，对齐既有 formal spec closeout exec-plan 样式。
- `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`spec`，变更类别=`docs, spec`
- `git commit -m 'docs(spec): 记录 FR-0024 规约验证结果'`
  - 结果：已生成 validation follow-up checkpoint `812edf6788e41bc6facfa21ebb66b2170035d38f`
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-313-fr-0024-adapter-capability-requirement-formal-spec`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`spec`，变更类别=`docs, spec`
- `git commit -m 'docs(spec): 校正 FR-0024 执行计划元数据'`
  - 结果：已生成 metadata 修正 checkpoint `08bb25f6000624a12f40db304e2c3ce7cc001f12`
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-313-fr-0024-adapter-capability-requirement-formal-spec`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`spec`，变更类别=`docs, spec`

## 待验证项

- PR `#317` 最新 head 的 guardian review 与受控 merge gate。

## 未决风险

- 若后续 `#314/#315` 在未消费本 spec 的情况下实现自己的 requirement shape，会形成 manifest / SDK / adapter migration 三套 truth。
- 若后续 Provider offer / compatibility decision 反向改写 requirement carrier，会破坏 `FR-0024` 与 `FR-0026` 的分层边界。
- 若 lifecycle / observability 字段被实现为 runtime resource store、provider selector 或技术链路字段，Core / Adapter / Provider 边界会漂移。

## 回滚方式

- 使用独立 revert PR 撤销 `docs/specs/FR-0024-adapter-capability-requirement-contract/` 与本 exec-plan 的增量修改。
- 若需要改变 requirement 声明边界，必须先回到父 FR `#296` 更新 GitHub truth，不得在后续 implementation PR 中隐式改写。

## 最近一次 checkpoint 对应的 head SHA

- formal spec 语义 checkpoint：`59bed8351a7b1758cad9cbaf4afac3ab456f927b`
- metadata 修正 checkpoint：`08bb25f6000624a12f40db304e2c3ce7cc001f12`
- validation result follow-up checkpoint：`812edf6788e41bc6facfa21ebb66b2170035d38f`
- review-sync follow-up checkpoint：`2be4b0c57cf4fac82132438bd4e269b75acab801`
- 当前 PR merge-base：`ea44f9cdc863b244b7ceba5a3a70f2e23e41b7a5`
