# CHORE-0079 执行计划

## 关联信息

- item_key：`CHORE-0079-fr-0007-formal-spec-closeout`
- Issue：`#79`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0007-release-gate-and-regression-checks/`
- 关联 PR：`#80`
- active 收口事项：`CHORE-0079-fr-0007-formal-spec-closeout`

## 目标

- 作为 `FR-0007` 下的真实 Work Item，完成版本门禁与回归检查 formal spec 的独立收口。
- 通过独立 spec PR 完成 spec review / checks / guardian / merge gate / closeout，使 `FR-0007` 成为主干 formal spec truth。

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

- `FR-0007` formal spec 套件已迁入当前 Work Item 分支，当前执行现场为独立 worktree：`/Users/mc/code/worktrees/syvert/issue-79-fr-0007-formal-spec`。
- 旧 PR `#73` 因直接把 FR 作为执行入口，被 guardian 判定违反 Work-Item-only 执行契约，已关闭并由当前 PR `#80` 接续。
- 当前 PR `#80` 的 GitHub checks 已通过；最新 guardian 阻断集中在 active `exec-plan` 审查态信息回写与 release 索引范围收窄。

## 下一步动作

- 回写当前 `exec-plan` 与 release 索引到最新 guardian 指出的阻断。
- 推送当前 head，确认 PR `#80` checks 继续全绿。
- 重跑 guardian；通过后受控合并 PR `#80`，并关闭 `#79` 与 `#67`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 冻结版本级验证 requirement，使“双参考适配器回归 + 平台泄漏检查”从路线图意图变成 formal spec 真相，并与 Work Item 执行入口契约保持一致。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0007` 下的 spec-only closeout Work Item，负责让 formal spec 经由合法执行入口合入主干。
- 阻塞：
  - 无外部阻塞；当前只需完成执行入口重绑、门禁、审查与合并收口。

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
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
- `python3 scripts/open_pr.py --class spec --issue 79 --item-key CHORE-0079-fr-0007-formal-spec-closeout --item-type CHORE --release v0.2.0 --sprint 2026-S15 --title "spec: 收口 FR-0007 的 formal spec" --closing fixes --dry-run`
- `gh pr checks 80`
  - 结果：`Validate Commit Messages`、`Validate Docs And Guard Scripts`、`Validate Governance Tooling`、`Validate Spec Review Boundaries` 全部通过
- `python3 scripts/pr_guardian.py review 80`
  - 结果：最新 guardian 要求同步当前 active `exec-plan` 审查态，并收窄 `docs/releases/v0.2.0.md` 到 FR-0007 所需的最小索引更新

## 未决风险

- 若仍把 active `exec-plan` / PR 绑定到 FR 而非 Work Item，会继续违反主干治理基线并被 guardian 拒绝。
- 若重绑后仍残留旧的 FR-bound 索引入口，release / sprint 真相会继续混入错误执行语义。

## 回滚方式

- 使用独立 revert PR 撤销本事项对 `FR-0007` formal spec 套件、Work Item active `exec-plan` 与 release/sprint 索引的更新。

## 最近一次 checkpoint 对应的 head SHA

- `c3fb529cf0ca4cbb5f9a411b4fb1adfd27d44939`
