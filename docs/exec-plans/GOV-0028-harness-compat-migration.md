# GOV-0028 执行计划

## 关联信息

- item_key：`GOV-0028-harness-compat-migration`
- Issue：`#57`
- item_type：`GOV`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/`
- 关联 PR：`#60`
- active 收口事项：`GOV-0028-harness-compat-migration`

## 目标

- 让 repo harness、guard、template 与 review 输入适配新的 `Phase -> FR -> Work Item` 治理契约。
- 让 harness、guard、template 与 review 输入优先消费 active `exec-plan`、绑定的 `FR-0003` formal spec 与当前 Work Item 上下文，而不是继续混写到 GitHub 调度层。
- 在不改动 `FR-0003` formal spec 套件契约的前提下，收敛当前 PR 的治理实现范围，并保留对既有 `TODO.md` 的读取兼容。

## 范围

- 本次纳入：
  - `.github/workflows/governance-gate.yml`
  - `docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/spec.md`
  - `WORKFLOW.md`
  - `code_review.md`
  - `docs/AGENTS.md`
  - `docs/exec-plans/GOV-0027-governance-contract-rewrite.md`
  - `docs/exec-plans/GOV-0028-harness-compat-migration.md`
  - `docs/exec-plans/README.md`
  - `docs/process/agent-loop.md`
  - `docs/specs/README.md`
  - `scripts/context_guard.py`
  - `scripts/governance_gate.py`
  - `scripts/item_context.py`
  - `scripts/open_pr.py`
  - `scripts/policy/policy.json`
  - `scripts/workflow_contract.py`
  - `tests/governance/test_context_guard.py`
  - `tests/governance/test_item_context.py`
  - `tests/governance/test_open_pr.py`
  - `tests/governance/test_governance_gate.py`
  - `tests/governance/test_workflow_guard.py`
- 本次不纳入：
  - 删除任何现有 `TODO.md`
  - 改写 `FR-0003` formal spec 套件语义
  - 新增项目管理状态页面
  - 任何业务实现代码

## 当前停点

- 最近一次已推送 checkpoint 对应 head 为 `cdf734ccbc9d5db011d15ad34b1ddce085baa0ae`。该 head 已收口 issue-scope 授权、fenced-code metadata 伪造面、`spec_todo` 分类、legacy `ADR-0001` 的 implementation compatibility 以及 review artifact 完整性；当前工作树只在该 checkpoint 之上做最后一次 exec-plan 一致性修正。
- 当前收口边界已经明确：
  - `context_guard` 对 touched formal spec、`exec-plan`、decision 全部按 `current_issue` 收紧；若无法从真实 git ref 推断当前事项，或同一 Issue 命中多个 active `exec-plan`，会直接 fail-closed。
  - `关联 spec` 只接受 FR formal spec 套件根目录，或根目录下的 `spec.md` / `plan.md` 文件；任意嵌套子目录都不再视为合法绑定。
  - 对仍绑定 legacy `docs/decisions/ADR-0001-governance-bootstrap-contract.md` 的非 `GOV` formal-spec 事项，当前回合保留精确兼容；除此之外，`governance` / `spec` 入口与 touched decision 授权仍要求可校验的 decision 元数据。
  - `ADR-0003` 继续保留在 `FR-0003` 层作为上位治理决策，不作为 `GOV-0028` active `exec-plan` 的 machine-checkable `关联 decision` 输入；当前 Work Item 的可追溯闭环以 `关联 spec` + `关联 PR` 为准。
  - `governance_gate` 在 CI 场景按实际 diff 推断 PR class，再复用 `pr_scope_guard.build_report()` 与 `open_pr` preflight contract，不再把普通 implementation PR 误打成治理红灯。

## 下一步动作

- 等当前 head 的 GitHub checks 全绿后，重新运行 guardian，确认拿到 `APPROVE + safe_to_merge=true`。
- guardian 通过后，使用受控入口执行 `python3 scripts/merge_pr.py 60 --delete-branch`，并核对 `#57` 自动关闭。

## 合入门槛

- 当前 head 必须同时满足：治理单测全绿、`spec_guard` / `context_guard` / `workflow_guard` / `governance_gate` / `open_pr --dry-run` 全通过。
- 当前 PR `#60` 必须等到 GitHub checks 全绿后，再运行 guardian，并取得 `APPROVE + safe_to_merge=true`。
- 仅在上述门槛满足后，才能通过受控入口执行 squash merge，并确认 `#57` 自动关闭。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 的治理收敛回合提供可执行的 harness 契约，使 GitHub 单一调度层与仓内单一语义层在 guard、review 与恢复入口上真正对齐。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0003 / #55` 下的第二个治理 Work Item，负责把上一轮治理契约落到 harness、guard、template 与审查输入上。
- 阻塞：无外部阻塞；必须避免越界到 `#58` 的 legacy `TODO.md` 最终清理。

## 验证矩阵

- `python3 -m unittest discover -s tests/governance -p 'test_*.py'`
- `python3 scripts/spec_guard.py --all`
- `python3 scripts/context_guard.py`
- `python3 scripts/workflow_guard.py`
- `python3 scripts/governance_gate.py --mode ci --base-sha 8bae3fd6ceb5822d8c5c9d1be593ed45808de4b5 --head-sha HEAD --head-ref issue-57-governance-migrate-harness-for-delivery-structure-compatibility`
- `python3 scripts/open_pr.py --class governance --issue 57 --item-key GOV-0028-harness-compat-migration --item-type GOV --release v0.2.0 --sprint 2026-S15 --closing fixes --dry-run`
- `SYVERT_GUARDIAN_TIMEOUT_SECONDS=3600 python3 scripts/pr_guardian.py review 60 --json-output /tmp/pr60-guardian-<head>.json`

## 未决风险

- 若 reviewer 仍把 formal spec 套件 contract 与执行回合 contract 混成一层，可能继续要求把 `TODO.md`、当前 Work Item 上下文与 FR formal spec contract 混写。
- 若后续 `#58` 未延续本轮的兼容边界，仍可能误删历史事项依赖的 `TODO.md`。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对治理脚本、治理测试、workflow 与文档模板的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `cdf734ccbc9d5db011d15ad34b1ddce085baa0ae`
