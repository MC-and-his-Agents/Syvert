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

- 最近一次已推送 checkpoint 对应 head 为 `7d222e62587687b410d56ac28546273ddf6f2eb9`。该 head 的 GitHub checks 已全绿，但 guardian 仍指出 6 个收口问题：`context_guard` 仍允许 cross-issue touched `exec-plan` / `decision`、CLI diff 模式未传入 `current_issue`、`governance_gate` 仍依赖本地分支推断 issue、legacy `HOTFIX` formal-input 兼容声明失真、`docs/specs/README.md` 最小套件表述矛盾、以及本 exec-plan 范围与停点描述已过期。
- 当前工作树正在同一事项内完成最后一轮一致性收口：
  - `context_guard` 对 touched formal spec、`exec-plan`、decision 全部按 `current_issue` 收紧；若无法从真实 git ref 推断当前事项，或同一 Issue 命中多个 active `exec-plan`，会直接 fail-closed。
  - formal-spec 模式下，只要声明了 `关联 decision`，就必须提供可校验的 `Issue` / `item_key` 元数据，不再接受 metadata-free / legacy decision 混入当前绑定；当前 `GOV-0028` 不再把 `ADR-0003` 作为本事项 bootstrap 输入。
  - `governance_gate` 在 CI 场景优先使用 PR `head-ref` 推断 issue，并通过 workflow step `env` 安全传入 `context_guard`。
  - `open_pr` 与治理文档不再宣称不存在的 legacy `HOTFIX` unbound formal-input 兼容；未绑定 `FR` 的本地 formal spec 套件只允许被 `implementation` 入口复用，`governance` / `spec` 不再走该回退。
  - 已将仍引用 `ADR-0003` 的 `GOV-0027` exec-plan 退役为 inactive，并把 `GOV-0028` 重新绑定到 `FR-0003` formal spec；`ADR-0003` 恢复为 `FR-0003` 的稳定上位治理决策，而不是当前 Work Item 的 bootstrap artifact。
  - `docs/specs/README.md` 与本 exec-plan 的范围、最小套件、待合入门槛同步回到当前 head 真相。

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
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
- `python3 scripts/open_pr.py --class governance --issue 57 --item-key GOV-0028-harness-compat-migration --item-type GOV --release v0.2.0 --sprint 2026-S15 --closing fixes --dry-run`
- `SYVERT_GUARDIAN_TIMEOUT_SECONDS=900 python3 scripts/pr_guardian.py review 60 --json-output /tmp/pr60-guardian-<head>.json`

## 未决风险

- 若 reviewer 仍把 formal spec 套件 contract 与执行回合 contract 混成一层，可能继续要求把 `TODO.md`、当前 Work Item 上下文与 FR formal spec contract 混写。
- 若后续 `#58` 未延续本轮的兼容边界，仍可能误删历史事项依赖的 `TODO.md`。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对治理脚本、治理测试、workflow 与文档模板的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `7d222e62587687b410d56ac28546273ddf6f2eb9`
