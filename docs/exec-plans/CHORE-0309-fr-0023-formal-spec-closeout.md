# CHORE-0309-fr-0023-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0309-fr-0023-formal-spec-closeout`
- Issue：`#309`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0023-third-party-adapter-entry-path/`
- 关联 decision：`docs/decisions/ADR-CHORE-0291-open-adapter-provider-boundary.md`
- 关联 PR：
- active 收口事项：`CHORE-0309-fr-0023-formal-spec-closeout`
- 状态：`active`

## 目标

- 创建并收口 `FR-0023` formal spec 套件，冻结第三方 Adapter 最小 public metadata、Adapter-only 稳定接入路径、manifest / fixture / contract test 准入与 reference adapter 升级约束，为 `#310/#311/#312` 提供 governing artifact。

## 范围

- 本次纳入：
  - `docs/specs/FR-0023-third-party-adapter-entry-path/spec.md`
  - `docs/specs/FR-0023-third-party-adapter-entry-path/plan.md`
  - `docs/specs/FR-0023-third-party-adapter-entry-path/data-model.md`
  - `docs/specs/FR-0023-third-party-adapter-entry-path/contracts/README.md`
  - `docs/specs/FR-0023-third-party-adapter-entry-path/risks.md`
  - `docs/exec-plans/CHORE-0309-fr-0023-formal-spec-closeout.md`
- 本次不纳入：
  - runtime 实现
  - contract test harness 实现
  - SDK 代码实现
  - reference adapter 代码迁移
  - Provider capability offer
  - Adapter / Provider compatibility decision
  - 真实外部 provider 样本
  - provider registry、selector、marketplace 或 fallback
  - `#313` worktree 或任何无关文件

## 当前停点

- `issue-309-fr-0023-adapter-formal-spec` 已作为 `#309` 的独立 worktree 建立，当前基线为 `16c4b8b137f38a1d494f08163fc4ad8a8eb10f68`。
- 已核对 `AGENTS.md`、`WORKFLOW.md`、`spec_review.md`、`#309`、父 FR `#295`、`FR-0021`、`FR-0027` 与 `ADR-CHORE-0291`。
- 已采用“`FR-0023` 冻结 Adapter-only 接入路径，`FR-0027` 提供 resource requirement 前提，provider offer / compatibility decision 留给独立 FR”的落盘策略。

## 下一步动作

- 运行 spec / docs / workflow / governance / scope 门禁。
- 修正门禁发现的问题。
- 提交中文 Conventional Commit。
- 不开 PR、不合并、不关闭 issue，由主线程统一处理 GitHub 状态。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 固定第三方 Adapter 稳定接入路径的 formal truth，使后续 contract test entry 与 SDK docs / migration 不再各自定义 manifest、fixture、metadata 或 provider 边界。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0023` 的 formal spec closeout Work Item。
- 阻塞：
  - `#310` contract test entry 需要消费本 spec 的 manifest / fixture / metadata 准入。
  - `#311` SDK docs / migration 需要消费本 spec 的第三方 Adapter 作者路径。
  - `#312` parent closeout 需要本 spec、contract test entry、SDK docs / migration 与 GitHub 状态齐备。

## 已验证项

- `gh api user --jq .login`
  - 结果：通过，当前认证用户为 `mcontheway`。
- `gh api repos/:owner/:repo/issues/309 --jq '{number,title,state,body,labels:[.labels[].name],milestone:.milestone.title}'`
  - 结果：通过，确认 `#309` 为 `CHORE-0309-fr-0023-formal-spec-closeout`，release=`v0.8.0`，sprint=`2026-S21`，父 FR=`#295`。
- `gh api repos/:owner/:repo/issues/295 --jq '{number,title,state,body,labels:[.labels[].name]}'`
  - 结果：通过，确认 `FR-0023` 目标为第三方 Adapter 稳定接入路径，明确不定义 Provider offer、compatibility decision 或真实外部 provider 样本。
- 已核对 `AGENTS.md`、`WORKFLOW.md`、`spec_review.md`、`docs/specs/FR-0021-adapter-provider-port-boundary/`、`docs/specs/FR-0027-multi-profile-resource-requirement-contract/`。
- 待运行：`python3 scripts/spec_guard.py --mode ci --all`
- 待运行：`python3 scripts/docs_guard.py --mode ci`
- 待运行：`python3 scripts/workflow_guard.py --mode ci`
- 待运行：`BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-309-fr-0023-adapter-formal-spec`
- 待运行：`python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`

## 未决风险

- 本事项只完成 formal spec，不证明 contract test entry 或 SDK docs 已落地；`#310/#311/#312` 必须继续按本 spec 收口。
- 若后续需要定义 Provider offer 或 compatibility decision，必须进入独立 FR，不得在 `FR-0023` 的 Adapter-only manifest 中隐式扩张。
- 本 spec 依赖 `FR-0027` 作为 resource requirement 前提；若 `FR-0027` 后续变更，`FR-0023` 的 resource declaration 准入说明需同步复审。

## 回滚方式

- 使用独立 revert PR 撤销 `docs/specs/FR-0023-third-party-adapter-entry-path/` 与本 exec-plan 的增量修改。
- 若需要改变 `FR-0023` 范围，必须先更新父 FR `#295`，不得在后续 implementation PR 中隐式改写。

## 最近一次 checkpoint 对应的 head SHA

- `16c4b8b137f38a1d494f08163fc4ad8a8eb10f68`
- worktree 创建基线：`16c4b8b137f38a1d494f08163fc4ad8a8eb10f68`
- 说明：该 checkpoint 记录 `#309` formal spec closeout 的执行前基线；完成文档与门禁后将以本事项提交 SHA 作为最新语义 checkpoint。
