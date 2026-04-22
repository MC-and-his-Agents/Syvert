# CHORE-0144-fr-0015-evidence-registry-reconciliation 执行计划

## 关联信息

- item_key：`CHORE-0144-fr-0015-evidence-registry-reconciliation`
- Issue：`#206`
- item_type：`CHORE`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 spec：`docs/specs/FR-0015-dual-reference-resource-capability-evidence/`
- 关联 PR：`#208`
- 状态：`active`
- active 收口事项：`CHORE-0144-fr-0015-evidence-registry-reconciliation`

## 目标

- 修订 `FR-0015` formal spec 中的 evidence registry 追溯入口，使 implementation closeout 当前消费的 `evidence_ref` 都能在 `research.md` 中找到稳定登记项。
- 把 `browser_state` 的 formal evidence basis 明确绑定到 browser / page-state fallback 路径，而不是复用无关的 `account-material` 证据。
- 保持 formal spec 与 implementation PR 分离，在不改写 runtime 代码的前提下修复上游 requirement truth。

## 范围

- 本次纳入：
  - `docs/specs/FR-0015-dual-reference-resource-capability-evidence/research.md`
  - 与 evidence ref traceability 直接相关的同套件最小 formal spec 修订
  - `docs/exec-plans/FR-0015-dual-reference-resource-capability-evidence.md`
  - `docs/exec-plans/CHORE-0144-fr-0015-evidence-registry-reconciliation.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/runtime/**`
  - `docs/releases/**`
  - `docs/sprints/**`
  - `FR-0013` / `FR-0014` 套件

## 当前停点

- `#197 / PR #204` 的 guardian 已明确指出：implementation closeout 当前引入的 `evidence_ref` 无法从 `FR-0015 research.md` 的 formal registry 回指，导致 formal spec truth 与实现真相分叉。
- `issue-206-fr-0015-formal-evidence-registry` 已作为 `#206` 的独立 spec worktree 建立。
- 当前回合只负责补齐 `research.md` evidence registry 与示例基线，不在本事项内改写 runtime / tests / release-sprint 索引。
- 最新 follow-up 语义 checkpoint `b3e05228ffc418da2655b3329400b5c4eca6edf1` 已生成，当前停点是吸收最新 `main`、继续消费 guardian / merge gate 反馈，并把 checkpoint / PR metadata 同步回 formal spec 工件。
- 当前受审 formal-spec follow-up PR 为 `#208`，后续 guardian / merge gate 反馈统一回写到本 exec-plan。

## 下一步动作

- 在 `research.md` 中补齐 `url-request-tokens`、`request-signature-token`、`page-state-fallback` 等 stable evidence refs，并同步负向候选示例基线。
- 更新 requirement container 的追溯入口，使 `#206` formal-spec follow-up 与 `#197` implementation closeout 的依赖关系显式可见。
- 运行 `spec_guard`、`docs_guard`、`workflow_guard` 与 `governance_gate`，通过后创建 formal-spec PR。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.5.0` 的资源能力证据 closeout 提供单一、可追溯的 formal evidence registry，避免 implementation PR 自行发明未登记的 evidence refs。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0015` formal spec 的 follow-up Work Item，负责修补 evidence registry traceability 缺口。
- 阻塞：
  - 在本事项合入前，`#197` 无法把新增 negative candidate evidence refs 视为 formal-traceable truth。
  - 若 `research.md` 继续缺失这些登记项，后续 `#195 / #196` 也无法对 evidence refs 建立稳定消费边界。

## 已验证项

- 已核对 `#197 / PR #204` guardian 最新 review，确认当前 formal spec 缺口集中在 `research.md` evidence registry 与 `browser_state` evidence basis。
- 已核对 `FR-0015` 当前 formal spec 套件与 requirement container，确认 follow-up 只需补齐 formal evidence traceability，不应扩张为新的 runtime 语义变更。
- `git commit -m 'docs(spec): 补齐 FR-0015 evidence registry 追溯入口'`
  - 结果：已生成最新语义 checkpoint `b3e05228ffc418da2655b3329400b5c4eca6edf1`
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `BASE=$(git merge-base origin/main HEAD); python3 scripts/governance_gate.py --mode ci --base-sha \"$BASE\" --head-sha $(git rev-parse HEAD) --head-ref issue-206-fr-0015-formal-evidence-registry`
  - 结果：通过
- `python3 scripts/open_pr.py --class spec --issue 206 --item-key CHORE-0144-fr-0015-evidence-registry-reconciliation --item-type CHORE --release v0.5.0 --sprint 2026-S18 --title 'docs(spec): 补齐 FR-0015 evidence registry 追溯入口' --base main --closing fixes`
  - 结果：已创建当前受审 PR `#208 https://github.com/MC-and-his-Agents/Syvert/pull/208`

## 未决风险

- 若 follow-up 只补 evidence registry 而不同步示例基线，formal spec 仍会在 review 中呈现两套互相矛盾的 evidence truth。
- 若把实现细节扩大成新的共享能力词汇，本事项会再次越过 `FR-0015` 已冻结的 `account / proxy` 边界。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `FR-0015` formal spec suite 与本 follow-up exec-plan 的最小修订。

## checkpoint 记录方式

- semantic checkpoint：使用通过 formal-spec 门禁后的 commit SHA 作为本回合唯一 requirement checkpoint。
- review-sync follow-up：若后续只回填 PR / checks / checkpoint metadata，不把 metadata-only 修改伪装成新的语义 checkpoint。

## 最近一次 checkpoint 对应的 head SHA

- `b3e05228ffc418da2655b3329400b5c4eca6edf1`
