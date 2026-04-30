# CHORE-0298-fr-0027-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0298-fr-0027-formal-spec-closeout`
- Issue：`#299`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0027-multi-profile-resource-requirement-contract/`
- 关联 decision：
- 关联 PR：`#304`
- active 收口事项：`CHORE-0298-fr-0027-formal-spec-closeout`
- 状态：`active`

## 目标

- 建立并收口 `FR-0027` formal spec 套件，冻结多 profile declaration carrier、matcher `one-of` 语义与 profile evidence 边界，为 `#300/#301/#302` 提供 governing artifact。

## 范围

- 本次纳入：
  - `docs/specs/FR-0027-multi-profile-resource-requirement-contract/`
  - `docs/exec-plans/FR-0027-multi-profile-resource-requirement-contract.md`
  - `docs/exec-plans/CHORE-0298-fr-0027-formal-spec-closeout.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - runtime matcher / evidence artifact / reference adapter 声明实现
  - `docs/releases/**`
  - `docs/sprints/**`
  - 其它 formal spec 套件

## 当前停点

- `issue-299-fr-0027-formal-spec` 已作为 `#299` 的独立 spec worktree 建立，基线为 `3410c212c3bc2a233892bcb5cf014fe90201fa19`。
- 已核对 `#294` 与 `#299-#303` 的目标、非目标与依赖关系。
- 当前 formal spec 回合采用“`FR-0027` 新主套件承接 `v0.8.0` truth，`FR-0013/14/15` 保留 `v0.5.0` 历史语义”的落盘策略，以满足现有 formal spec scope guard；`#299` 与 `#294` 的 GitHub truth 已同步到这一路径。
- 最新 formal spec 语义 checkpoint `c71d65e39fca547f02264522a663694164e24001` 已生成，当前受审 spec PR 为 `#304`；当前停点是等待基于最新 head 的 guardian verdict 回写状态面，并把修复后的 review / merge gate 真相持续同步回 exec-plan。

## 下一步动作

- 在当前受审 PR `#304` 上消费 spec review、guardian 与 merge gate 反馈。
- 若后续只追加 PR / checks / checkpoint metadata，则保持 review-sync follow-up 口径，不伪装成新的语义 checkpoint。
- 合入后在 `#299` 留 closeout comment，并为 `#300/#301/#302` 提供主干 formal input。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 把 multi-profile resource requirement、matcher `one-of` 与 profile evidence 边界推进为 implementation-ready formal contract。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0027` 的 formal spec closeout Work Item。
- 阻塞：
  - `#300`、`#301`、`#302` 都依赖本 spec 合入主干。
  - 若本 spec 不先冻结，evidence、runtime 与 reference adapter migration 会继续绑在旧的单声明模型上。

## 已验证项

- `python3 scripts/create_worktree.py --issue 299 --class spec`
  - 结果：通过，创建 worktree `issue-299-fr-0027-formal-spec`
- 已核对 `AGENTS.md`、`vision.md`、`docs/roadmap-v0-to-v1.md`、`WORKFLOW.md`、`docs/AGENTS.md`、`docs/process/delivery-funnel.md` 与 `spec_review.md` 的上位约束。
- 已核对 `FR-0013`、`FR-0014`、`FR-0015` 当前 `v0.5.0` 单声明基线与 `#294` 的 `v0.8.0` 目标差异。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-299-fr-0027-formal-spec`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `git commit -m 'docs(spec): 冻结 FR-0027 多 profile 资源依赖契约'`
  - 结果：已生成语义 checkpoint `af746a3b147ee55990abb6e475fed90dddaf39eb`
- `git commit -m 'docs(spec): 收紧 FR-0027 profile 证据契约'`
  - 结果：已生成语义 checkpoint `40bc383f48459176ed286c094aa5494b6176ba95`
- `git commit -m 'docs(spec): 绑定 FR-0027 适配器证据边界'`
  - 结果：已生成语义 checkpoint `c45c80f799d832036b13694a33885014534c0b07`
- `git commit -m 'docs(spec): 闭合 FR-0027 proof 绑定规则'`
  - 结果：已生成语义 checkpoint `408fb3ed0bc2ecb6937a930e1be2e27feaeea794`
- `gh api -X PATCH repos/<repo>/issues/299 -f body=...`
  - 结果：已把 `#299` 的 formal-spec scope 调整为“建立 `FR-0027` 新套件并明确 `v0.8.0` version boundary”，不再声称在同一 spec PR 并改多个旧 formal spec 套件。
- `gh api -X PATCH repos/<repo>/issues/294 -f body=...`
  - 结果：已把 `#294` 的关联 formal spec 调整为 `FR-0027` 主套件，并将 `FR-0013` / `FR-0014` / `FR-0015` 明确标记为历史输入。
- `git commit -m 'docs(spec): 收紧 FR-0027 规约边界'`
  - 结果：已生成最新语义 checkpoint `c4cc7862e61722d113260d6b0802e8461d8a7ea6`
- `git commit -m 'docs(spec): 固定 FR-0027 proof 适用边界'`
  - 结果：已生成语义 checkpoint `de2897ff993cf35cc344264d9e1745b204563a53`
- `gh api -X PATCH repos/<repo>/issues/299 -f body=...`
  - 结果：已把 `#299` 的 scope 进一步收紧为当前双参考 slice 的 formal-spec closeout。
- `gh api -X PATCH repos/<repo>/issues/294 -f body=...`
  - 结果：已把 `#294` 的 FR 目标与关闭条件同步收紧为当前双参考 slice 的 profile contract 收口。
- `git commit -m 'docs(spec): 收紧 FR-0027 双参考 slice 边界'`
  - 结果：已生成最新语义 checkpoint `ba8b5f5c03f523291b01e644258726d2527a76c0`
- `git commit -m 'docs(spec): 校正 FR-0027 审批词汇与 checkpoint'`
  - 结果：已生成最新语义 checkpoint `c71d65e39fca547f02264522a663694164e24001`
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-299-fr-0027-formal-spec`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/open_pr.py --class spec --issue 299 --item-key CHORE-0298-fr-0027-formal-spec-closeout --item-type CHORE --release v0.8.0 --sprint 2026-S21 --title 'docs(spec): 收口 FR-0027 多 profile 资源依赖 formal spec' --closing fixes --integration-touchpoint none --shared-contract-changed no --integration-ref none --external-dependency none --merge-gate local_only --contract-surface none --joint-acceptance-needed no --integration-status-checked-before-pr no --integration-status-checked-before-merge no`
  - 结果：已创建当前受审 spec PR `#304 https://github.com/MC-and-his-Agents/Syvert/pull/304`
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 304 --post-review --json-output /tmp/syvert-pr-304-guardian.json`
  - 结果：REQUEST_CHANGES。guardian 指出两类阻断：checkpoint SHA 写错，以及 `FR-0027` 要求 profile-level approved evidence 却未冻结最小 approval proof contract。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 304 --post-review --json-output /tmp/syvert-pr-304-guardian-r2.json`
  - 结果：REQUEST_CHANGES。guardian 进一步指出 approved profile proof 尚未反向约束 declaration `adapter_key`，存在未验证 adapter 借用 `xhs/douyin` 批准 tuple 的风险。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 304 --post-review --json-output /tmp/syvert-pr-304-guardian-r3.json`
  - 结果：REQUEST_CHANGES。guardian 继续指出 proof 绑定规则仍未闭合：每条 `evidence_ref` 还必须与 declaration 的 `capability + profile tuple` 完全对齐，而不能只做到“可解析 + adapter 覆盖”。

## 未决风险

- 若 `FR-0027` 没有明确写清 supersede 边界，后续事项可能继续并行消费旧 `FR-0013/14/15` 的单声明 truth。
- 若多 profile 被写成优先级 / fallback 语义，runtime 与 adapter migration 会越过 `#294` 明确不在范围的边界。

## 回滚方式

- 使用独立 revert PR 撤销 `docs/specs/FR-0027-multi-profile-resource-requirement-contract/` 与本 exec-plan / requirement container 的增量修改。
- 若需要改变 `FR-0027` 范围，必须先更新 `#294`，不得在后续实现 PR 中隐式改写。

## 最近一次 checkpoint 对应的 head SHA

- `c71d65e39fca547f02264522a663694164e24001`
- worktree 创建基线：`3410c212c3bc2a233892bcb5cf014fe90201fa19`
