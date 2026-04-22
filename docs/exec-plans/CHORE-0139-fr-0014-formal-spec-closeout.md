# CHORE-0139-fr-0014-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0139-fr-0014-formal-spec-closeout`
- Issue：`#193`
- item_type：`CHORE`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 spec：`docs/specs/FR-0014-core-resource-capability-matching/`
- 关联 PR：`#199`
- 状态：`active`
- active 收口事项：`CHORE-0139-fr-0014-formal-spec-closeout`

## 目标

- 建立并收口 `FR-0014` formal spec 套件，冻结 Core 资源能力匹配的最小 input / output、`matched / unmatched` 规则与错误口径边界。

## 范围

- 本次纳入：
  - `docs/specs/FR-0014-core-resource-capability-matching/`
  - `docs/exec-plans/FR-0014-core-resource-capability-matching.md`
  - `docs/exec-plans/CHORE-0139-fr-0014-formal-spec-closeout.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - runtime matcher / scheduler / provider 选择实现
  - `docs/releases/**`
  - `docs/sprints/**`
  - 根级治理文档与其他 FR 套件

## 当前停点

- `issue-193-fr-0014-formal-spec` 已作为 `#193` 的独立 spec worktree 建立。
- `FR-0014` formal spec 套件与 requirement container / Work Item exec-plan 已在当前分支首次落盘。
- 最新 formal spec 语义 checkpoint `d5360230e4a1938be460bba2e9ae97554caf37f9` 已生成，当前受审 spec PR 为 `#199`；当前停点是把最新门禁结果与 PR 真相同步回 exec-plan，并等待 review / guardian / merge gate。

## 下一步动作

- 运行 `spec_guard`、`docs_guard`、`workflow_guard` 与 `governance_gate`，修复 `FR-0014` 套件的一致性问题。
- 在当前受审 PR `#199` 上继续消费 review / guardian / merge gate 反馈。
- 若后续只追加 PR / checks / checkpoint metadata，则保持 review-sync follow-up 口径，不伪装成新的语义 checkpoint。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.5.0` 把“资源能力是否满足声明”的前置判断推进为 implementation-ready 的 formal contract。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0014` 的 formal spec closeout Work Item。
- 阻塞：
  - 若 `FR-0014` 不先收口，runtime matcher 会被迫自行决定 partial match、错误口径与 scope 边界。
  - 若 `FR-0013 / FR-0015` 的上游真相未被消费，matcher 很容易重新发明能力词汇或声明形状。

## 已验证项

- 已核对 `#188`、`#190`、`#193` 对 `v0.5.0` Core 资源能力匹配事项的目标、非目标与关闭条件描述。
- 已核对 `AGENTS.md`、`vision.md`、`docs/roadmap-v0-to-v1.md`、`WORKFLOW.md` 与 `spec_review.md` 的上位约束。
- 已核对 `FR-0010`、`FR-0012` 与当前 `FR-0013 / FR-0015` 规划边界，确认 matcher 只应承担能力满足性判断，而不承担 acquire / 注入 / provider 选择责任。
- `git commit -m 'docs(spec): 冻结 FR-0014 Core 资源能力匹配 contract'`
  - 结果：已生成最新语义 checkpoint `d5360230e4a1938be460bba2e9ae97554caf37f9`
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-193-fr-0014-formal-spec`
  - 结果：通过
- `python3 scripts/open_pr.py --class spec --issue 193 --item-key CHORE-0139-fr-0014-formal-spec-closeout --item-type CHORE --release v0.5.0 --sprint 2026-S18 --title 'docs(spec): 收口 FR-0014 Core 资源能力匹配 formal spec' --closing fixes --integration-touchpoint none --shared-contract-changed no --integration-ref none --external-dependency none --merge-gate local_only --contract-surface none --joint-acceptance-needed no --integration-status-checked-before-pr no --integration-status-checked-before-merge no`
  - 结果：已创建当前受审 spec PR `#199 https://github.com/MC-and-his-Agents/Syvert/pull/199`

## 未决风险

- 若 `unmatched` 与 `invalid_resource_requirement` 的口径没有一次写清，runtime 很容易把合法声明误报成 contract 违法。
- 若 matcher surface 出现 provider id、排序分数或技术字段，后续实现会把本事项误扩张成 scheduler 或技术桥接层。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `FR-0014` formal spec 套件与当前 closeout exec-plan 的增量修改。

## checkpoint 记录方式

- semantic checkpoint：使用通过全部 formal-spec 门禁后的 commit SHA 作为唯一语义 checkpoint。
- review-sync follow-up：若后续只回填当前受审 PR、checks 或 checkpoint metadata，不把 metadata-only 修改伪装成新的语义 checkpoint。

## 最近一次 checkpoint 对应的 head SHA

- `d5360230e4a1938be460bba2e9ae97554caf37f9`
- review-sync 说明：当前 live head 已包含 checkpoint SHA、门禁结果与 PR metadata；后续若只追加同类同步，不把 metadata-only follow-up 伪装成新的语义 checkpoint。
