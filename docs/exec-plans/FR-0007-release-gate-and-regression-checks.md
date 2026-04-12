# FR-0007 执行计划

## 关联信息

- item_key：`FR-0007-release-gate-and-regression-checks`
- Issue：`#67`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0007-release-gate-and-regression-checks/`
- 关联 PR：`#73`
- active 收口事项：`FR-0007-release-gate-and-regression-checks`

## 目标

- 为 `#67` 建立独立 formal spec 套件，冻结版本 gate、双参考适配器回归与平台泄漏检查的 requirement 边界。
- 以独立 spec PR 完成 spec review / checks / guardian / merge / issue closeout，使 `FR-0007` 成为主干 formal spec truth。

## 范围

- 本次纳入：
  - `docs/specs/FR-0007-release-gate-and-regression-checks/`
  - `docs/exec-plans/FR-0007-release-gate-and-regression-checks.md`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
- 本次不纳入：
  - `src/**`
  - `scripts/**`
  - `tests/**`
  - gate / harness / CI 的具体实现

## 当前停点

- `FR-0007` formal spec 套件、最小 active `exec-plan` 与 `v0.2.0` / `2026-S15` 索引更新已落在当前 head，受审 PR 为 `#73`。
- 本地门禁 `spec_guard`、`docs_guard`、`pr_scope_guard` 与 `open_pr --dry-run` 已通过；GitHub checks 已全绿。
- 首轮 guardian 已指出 3 个阻断：`release-ready` 术语未在上位文档定义、上游依赖被过早标记为已就绪、active `exec-plan` 审查态信息滞后。当前回合正基于该最新阻断收口并准备重跑 guardian。

## 下一步动作

- 修正 guardian 最新阻断并更新当前 `exec-plan` / PR 正文的一致性。
- 推送当前 head，确认 GitHub checks 继续全绿。
- 重跑 guardian；通过后使用受控 merge 合并 PR `#73`，再关闭 `#67`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 冻结版本级验证 requirement，使“双参考适配器回归 + 平台泄漏检查”从路线图意图变成 formal spec 真相。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`v0.2.0` 验证主线中的 formal spec 事项，负责冻结版本 gate requirement。
- 阻塞：
  - 无外部阻塞；当前仅需完成 formal spec 起草、门禁、审查与合并收口。

## 已验证项

- `gh issue view 63`
- `gh issue view 64`
- `gh issue view 65`
- `gh issue view 66`
- `gh issue view 67`
- `sed -n '1,220p' vision.md`
- `sed -n '1,260p' docs/roadmap-v0-to-v1.md`
- `sed -n '1,260p' WORKFLOW.md`
- `sed -n '1,260p' docs/AGENTS.md`
- `sed -n '1,260p' spec_review.md`
- `sed -n '1,260p' docs/releases/v0.2.0.md`
- `python3 scripts/spec_guard.py --all`
- `python3 scripts/spec_guard.py --base-ref origin/main --head-ref HEAD`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
- `python3 scripts/open_pr.py --class spec --issue 67 --item-key FR-0007-release-gate-and-regression-checks --item-type FR --release v0.2.0 --sprint 2026-S15 --title "spec: 冻结 FR-0007 的版本门禁与回归检查" --closing refs --dry-run`
- `gh pr checks 73`
  - 结果：`Validate Commit Messages`、`Validate Docs And Guard Scripts`、`Validate Governance Tooling`、`Validate Spec Review Boundaries` 全部通过
- `python3 scripts/pr_guardian.py review 73`
  - 结果：首轮 guardian 返回 `REQUEST_CHANGES`，当前按其最新阻断收口

## 未决风险

- 若 formal spec 把版本 gate 写死为某个实现入口，会抢占后续 Work Item 的设计空间。
- 若 release / sprint 索引不回写 `FR-0007` 入口，仓内主干真相与 GitHub FR 状态会继续失配。

## 回滚方式

- 使用独立 revert PR 撤销本事项对 `FR-0007` formal spec 套件、exec-plan 与 release/sprint 索引的更新。

## 最近一次 checkpoint 对应的 head SHA

- `92261bd8c7a63706551e5a2bc406d71190a7e1f6`
