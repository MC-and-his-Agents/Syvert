# CHORE-0051-fr-0005-formal-spec 执行计划

## 关联信息

- item_key：`CHORE-0051-fr-0005-formal-spec`
- Issue：`#77`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`
- 关联 decision：
- 关联 PR：`#78`
- active 收口事项：`CHORE-0051-fr-0005-formal-spec`

## 目标

- 为父 FR `#65` 的 formal spec 执行回合提供独立 Work Item 入口，完成 spec PR、checks、guardian、merge gate 与 closeout。
- 保持本次回合只服务于 `FR-0005` formal spec，不提前进入 `#69`、`#70` 的实现。

## 范围

- 本次纳入：
  - `docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`
  - `docs/exec-plans/CHORE-0051-fr-0005-formal-spec.md`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
- 本次不纳入：
  - `#69` 的错误模型实现
  - `#70` 的 adapter registry 实现
  - harness、fake adapter、gate 或 validator 设计细节
  - `src/**`、`scripts/**`、`tests/**` 的运行时改造

## 当前停点

- `FR-0005` formal spec 套件已在当前分支落地，且已按 guardian 对 PR `#72` 的阻断要求，将执行回合从 FR `#65` 重绑到独立 Work Item `#77`。
- 当前受审 PR 为 `#78`，绑定 `Issue #77` / `item_key=CHORE-0051-fr-0005-formal-spec`，远端 checks 已全绿。
- 当前停在 guardian 前的最后审查补件：已补齐 adapter-side pre-platform 输入失败的分类语义、exec-plan 当前停点与本轮验证证据。

## 下一步动作

- 对 PR `#78` 执行 guardian 审查。
- 若 guardian 给出新的阻断，只修当前 head 的最新阻断。
- guardian 通过后使用受控 `merge_pr` 合并。
- 合并后同步 `#65` 的 formal spec 入口，并关闭 `#77`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 冻结“标准化错误模型 + adapter registry”这一共享契约，并把 formal spec 执行回合收回到符合 `Phase -> FR -> Work Item` 的治理模型。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0005` 的 formal spec Work Item。
- 阻塞：
  - 无外部阻塞；当前仅需完成 Work Item 重绑、受控 PR、checks、guardian 与 merge gate。

## 已验证项

- `gh issue view 65`
  - 结果：`FR-0005` 为 `v0.2.0` FR 容器，formal spec 为其 requirement 真相入口
- `gh issue view 69`
  - 结果：`#69` 为“实现标准化错误模型”的后续 Work Item
- `gh issue view 70`
  - 结果：`#70` 为“实现适配器注册表”的后续 Work Item
- `gh issue view 77`
  - 结果：`#77` 已创建为当前 formal spec 执行回合的独立 Work Item
- `gh issue view 64`
  - 结果：`FR-0004` 负责 `InputTarget` 与 `CollectionPolicy`
- `gh issue view 66`
  - 结果：`FR-0006` 负责 adapter contract test harness
- `gh issue view 67`
  - 结果：`FR-0007` 负责版本 gate 与回归检查
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/context_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/open_pr.py --class spec --issue 77 --item-key CHORE-0051-fr-0005-formal-spec --item-type CHORE --release v0.2.0 --sprint 2026-S15 --title "docs(spec): 冻结 FR-0005 错误模型与适配器注册表契约" --closing refs --dry-run`
  - 结果：通过
- `gh pr checks 78`
  - 结果：`Validate Commit Messages`、`Validate Docs And Guard Scripts`、`Validate Governance Tooling`、`Validate Spec Review Boundaries` 全部通过
- `gh pr close 72 --comment "... Superseded by #78 ..."`
  - 结果：PR `#72` 已关闭；当前有效审查入口为 PR `#78`

## 未决风险

- 若 formal spec 没有把 adapter 侧 pre-platform 输入失败映射到明确类别，`#69` 仍会留下分类空洞。
- 若 branch / worktree / exec-plan / PR 继续绑在 FR `#65` 而不是 Work Item `#77`，guardian 会持续阻断合并。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`、`docs/exec-plans/CHORE-0051-fr-0005-formal-spec.md`、`docs/releases/v0.2.0.md` 与 `docs/sprints/2026-S15.md` 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `80b2588fbdba7c2e286e598bb9c7e4b70eab8720`
- 说明：该 checkpoint 已包含 Work Item 重绑与 spec 边界修正；当前 head 只补充 review / checks / PR 审查元数据，可由 guardian state 继续绑定当前受审 head。
