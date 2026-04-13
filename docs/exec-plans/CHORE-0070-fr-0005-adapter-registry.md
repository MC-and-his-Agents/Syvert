# CHORE-0070-fr-0005-adapter-registry 执行计划

## 关联信息

- item_key：`CHORE-0070-fr-0005-adapter-registry`
- Issue：`#70`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`
- 关联 decision：
- 关联 PR：`#98`
- 状态：`inactive (historical implementation round; merged via PR #98 and issue #70 closed)`
- 历史收口事项：`CHORE-0070-fr-0005-adapter-registry`

## 目标

- 在 `FR-0005` 范围内落地 adapter registry，把 materialize、lookup、capability discovery 与 fail-closed 语义固化到运行时主路径。

## 范围

- 本次纳入：
  - `syvert/registry.py`
  - `syvert/runtime.py`
  - `syvert/adapters/__init__.py`
  - `tests/runtime/test_runtime.py`
  - `tests/runtime/test_executor.py`
  - `tests/runtime/test_registry.py`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
  - 本 exec-plan
- 本次不纳入：
  - fake adapter、harness、validator、version gate
  - `FR-0004` 的输入建模语义改写
  - 平台适配器内部平台逻辑

## 当前停点

- `FR-0005` formal spec 已由 PR `#78` 合入主干，`#70` 已由 PR `#98` 合入并关闭。
- 历史 worktree / 分支：`/Users/mc/code/worktrees/syvert/issue-70-task` / `issue-70-task`；对应实现回合已完成，待在本次 closeout 后退役。
- 当前主干已具备 registry materialization、lookup、capability discovery、duplicate-key fail-close 与 invalid declaration fail-close；本文件仅保留为历史实现记录。

## 下一步动作

- 无 active 动作。
- `#70` 的主干实现与 closeout 证据由 `docs/exec-plans/CHORE-0099-fr-0005-parent-closeout.md` 继续消费；本文件仅保留为历史实现记录。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 把 adapter registry contract 从 formal spec 落到 runtime，实现可验证的 registry materialization 与 discovery 语义。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0005` 的第二个 implementation Work Item，负责把 adapter registry contract 落到 Core。
- 阻塞：
  - 不得把 harness、fake adapter、gate 或额外 FR 范围并入当前回合。

## 已验证项

- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`spec_review.md`
- 已阅读：`code_review.md`
- 已阅读：`docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`
- `python3 -m unittest tests.runtime.test_runtime tests.runtime.test_executor tests.runtime.test_cli tests.runtime.test_registry`
  - 结果：`Ran 62 tests in 1.703s`，`OK`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
  - 结果：已校验 3 条提交信息，全部通过
- `python3 scripts/open_pr.py --class implementation --issue 70 --item-key CHORE-0070-fr-0005-adapter-registry --item-type CHORE --release v0.2.0 --sprint 2026-S15 --title 'feat(runtime): 落地 FR-0005 适配器注册表' --closing fixes --dry-run`
  - 结果：通过
- 已创建当前受审 PR：`#98 https://github.com/MC-and-his-Agents/Syvert/pull/98`
- `SYVERT_GUARDIAN_TIMEOUT_SECONDS=36000 python3 scripts/pr_guardian.py review 98 --post-review`
  - 结果：首轮 `REQUEST_CHANGES`；阻断项已定位为“无效 adapter 声明未在 materialization 阶段 fail-close”和“默认 shared builder 路径吞掉 duplicate key”

## 未决风险

- registry discovery 若引入真实平台副作用，将破坏 `FR-0005` 的 discovery 约束并影响后续 `FR-0006` harness。
- 若把 registry 失配误判为 `unsupported`，会破坏 `runtime_contract` 的 fail-closed 边界。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 registry、runtime、tests 与索引工件的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `37d6b835f01867ac99e307a46016498f5f9e5af9`
- 说明：该 checkpoint 已包含 registry 实现、测试与索引更新；后续 guardian 阻断收口提交仅补充 fail-closed 与 duplicate-key 保真，不改写 `FR-0005` contract 边界。
