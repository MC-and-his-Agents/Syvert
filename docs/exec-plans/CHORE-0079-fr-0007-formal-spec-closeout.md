# CHORE-0079 执行计划

## 关联信息

- item_key：`CHORE-0079-fr-0007-formal-spec-closeout`
- Issue：`#79`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0007-release-gate-and-regression-checks/`
- 关联 PR：`#84`
- active 收口事项：`CHORE-0079-fr-0007-formal-spec-closeout`

## 目标

- 作为 `FR-0007` 下的真实 Work Item，完成版本门禁与回归检查 formal spec 的独立收口。
- 通过独立 spec PR 完成 checks / guardian / merge gate / closeout，使 `FR-0007` 形成主干上的 `spec-ready` formal spec truth。

## 范围

- 本次纳入：
  - `docs/specs/FR-0007-release-gate-and-regression-checks/`
  - `docs/exec-plans/CHORE-0079-fr-0007-formal-spec-closeout.md`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
- 本次不纳入：
  - `src/**`
  - `scripts/**`
  - `tests/**`
  - gate / harness / CI 的具体实现
  - `FR-0004`、`FR-0005`、`FR-0006` 的 formal spec 本体

## 当前停点

- `FR-0007` formal spec 套件已迁入当前 Work Item 分支，当前执行现场为独立 worktree，key 为 `issue-79-fr-0007-formal-spec`。
- 旧 PR `#73` 因直接把 FR 作为执行入口，被 guardian 判定违反 Work-Item-only 执行契约，随后由 `#80` 接续。
- 当前实质 checkpoint 已推进到 `674fed9e210edca0bcb5cb29879bca05c75c8a10`，该提交冻结了 `FR-0007` 的最小双参考回归矩阵与平台泄漏允许区/禁止区边界，使当前 PR 的 requirement truth 达到可审查终态。
- 相对最近一次实质 checkpoint（`674fed9e210edca0bcb5cb29879bca05c75c8a10`）之后的跟进提交，当前受审 head 仅补充 exec-plan 证据、guardian closeout 与收尾叙述，不改变 `FR-0007` 已冻结的 requirement truth；相对 `origin/main`，本 PR 负责把 `FR-0007` formal spec 套件、active exec-plan 与 release/sprint 索引首次落盘为主干候选。
- 当前活跃 PR 已切换为 `#84`，用于恢复 GitHub `pull_request` checks；formal spec 内容与 Work Item 绑定保持不变。

## 下一步动作

- 在当前 head 上重跑 guardian，确认 formal spec 审查输入已闭合。
- 若 guardian 通过，则继续处理 merge gate 所需的 checks / head 一致性。
- 通过受控 merge 完成 PR `#84`，随后关闭 `#79`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 冻结版本级验证 requirement，使“双参考适配器回归 + 平台泄漏检查”从路线图意图变成 formal spec 真相，并与 Work Item 执行入口契约保持一致。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0007` 下的 spec-only closeout Work Item，负责让 formal spec 经由合法执行入口以 `spec-ready` 基线合入主干。
- 阻塞：
  - 当前 PR 仅剩 latest guardian 对当前受审 head 的文档口径收口；GitHub checks 与 mergeability 需继续以 PR `#84` 的当前 head 状态为准。
  - 本 closeout 只负责把 `FR-0007` 收口为 `spec-ready` formal spec truth；是否进入 `implementation-ready` 由 `spec_review.md` 的审查结论与进入实现前条件共同决定。

## 已验证项

- `gh issue view 63`
- `gh issue view 67`
- `gh issue view 79`
- `sed -n '1,220p' vision.md`
- `sed -n '1,260p' docs/roadmap-v0-to-v1.md`
- `sed -n '1,260p' WORKFLOW.md`
- `sed -n '1,260p' docs/AGENTS.md`
- `sed -n '1,260p' spec_review.md`
- `python3 scripts/pr_guardian.py review 73`
  - 结果：guardian 要求把 formal spec 执行回合从 FR 重新绑定到真实 Work Item，并避免把未实现的依赖写成 spec 仍不可进入实现
- `python3 scripts/spec_guard.py --all`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：当前受审 head 通过。
- `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
  - 结果：当前受审 head 的 PR class 为 `spec`，变更类别为 `docs, spec`，scope 校验通过。
- `python3 scripts/open_pr.py --class spec --issue 79 --item-key CHORE-0079-fr-0007-formal-spec-closeout --item-type CHORE --release v0.2.0 --sprint 2026-S15 --title "spec: 收口 FR-0007 的 formal spec" --closing fixes --dry-run`
  - 结果：受控 open_pr 干跑通过，可生成合法 spec PR 输入。
- `gh pr view 84 --json url,headRefOid,mergeStateStatus,statusCheckRollup,reviews,reviewDecision`
  - 结果：可直接复核 PR `#84` 的当前 head SHA、latest review 元数据、merge state 与 status rollup。
- `gh pr checks 84`
  - 结果：可直接复核 PR `#84` 当前 head 的 required checks 结果。
- `python3 scripts/commit_check.py --mode pr --base-sha $(git merge-base origin/main HEAD) --head-sha $(git rev-parse HEAD)`
  - 结果：当前受审 head 的提交信息校验通过。
- `python3 scripts/spec_guard.py --mode ci --base-sha $(git merge-base origin/main HEAD) --head-sha $(git rev-parse HEAD)`
  - 结果：当前受审 head 通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：当前受审 head 通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：当前受审 head 通过。
- `python3 scripts/governance_gate.py --mode ci --base-sha $(git merge-base origin/main HEAD) --head-sha $(git rev-parse HEAD) --head-ref issue-79-fr-0007-formal-spec`
  - 结果：当前受审 head 通过。
- `python3 -m unittest discover -s tests/governance -p 'test_*.py'`
  - 结果：执行 235 项治理测试，全部通过。
- `python3 scripts/pr_guardian.py review 80`
  - 结果：latest guardian 继续要求 formal spec、exec-plan 与 PR 目标对 `spec-ready` / `implementation-ready` 的口径保持一致
- `python3 scripts/pr_guardian.py review 84`
  - 结果：以 PR `#84` 当前受审 head 的最新 guardian review 为准；当前剩余 closeout 仅允许围绕 latest guardian 指出的文档口径问题继续收口。

## 未决风险

- 若仍把 active `exec-plan` / PR 绑定到 FR 而非 Work Item，会继续违反主干治理基线并被 guardian 拒绝。
- 若重绑后仍残留旧的 FR-bound 索引入口，release / sprint 真相会继续混入错误执行语义。

## 回滚方式

- 使用独立 revert PR 撤销本事项对 `FR-0007` formal spec 套件、Work Item active `exec-plan` 与 release/sprint 索引的更新。

## 最近一次 checkpoint 对应的 head SHA

- `674fed9e210edca0bcb5cb29879bca05c75c8a10`
- 说明：该 checkpoint 完成了 `FR-0007` 最小双参考回归矩阵与平台泄漏边界的 formal spec 冻结；其后的提交只承载 exec-plan 证据刷新与 guardian closeout 收尾，不再改写 requirement truth，并需继续以当前受审 head 复核 guardian 与 checks 结果。
