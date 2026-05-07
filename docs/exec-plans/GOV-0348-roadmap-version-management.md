# GOV-0348 roadmap and version management boundary 执行计划

## 关联信息

- item_key：`GOV-0348-roadmap-version-management`
- Issue：`#348`
- item_type：`GOV`
- release：`v0.9.0`
- sprint：`2026-S21`
- 关联 spec：无（治理 / roadmap / version-management bootstrap 事项）
- 关联 decision：`docs/decisions/ADR-GOV-0348-roadmap-version-management.md`
- active 收口事项：`GOV-0348-roadmap-version-management`
- 关联 PR：`#349`
- 状态：`active`

## 目标

- 规范 Syvert `v0.x -> v1.0.0` 与 `v1.x -> v2.0.0` 路线边界。
- 明确 `v1.0.0` 是 Core stable，不是上层应用完成版。
- 明确 `v2.0.0` 由 runtime capability contract 稳定门禁触发，不由 `v1.9.0` 自动触发。
- 建立版本管理规则、version guard CI、Python packaging 防遗忘规划与 PR class policy 修正。

## 范围

- 本次纳入：
  - `vision.md`
  - `AGENTS.md`
  - `docs/AGENTS.md`
  - `docs/roadmap-v0-to-v1.md`
  - `docs/roadmap-v1-to-v2.md`
  - `docs/process/version-management.md`
  - `docs/process/python-packaging.md`
  - `docs/process/delivery-funnel.md`
  - `docs/releases/README.md`
  - `docs/releases/_template.md`
  - `.github/workflows/version-guard.yml`
  - `scripts/version_guard.py`
  - `scripts/policy/policy.json`
  - `tests/governance/test_version_guard.py`
  - 本 exec-plan 与对应 ADR
- 本次不纳入：
  - runtime / adapter 实现
  - formal spec 套件
  - `pyproject.toml`
  - PyPI / GitHub Packages publish
  - 上层应用仓库或产品实现

## 当前停点

- 标准 worktree `issue-348-task` 已创建。
- 当前路线图、版本管理、version guard、Python packaging 规划和 policy 修正已迁移到标准 worktree 分支。
- PR `#349` 已创建；guardian 已指出的 version guard、roadmap version 格式、release template、AGENTS 权威顺序、release published truth carrier 空占位校验与 exec-plan 状态一致性阻断均已修复。
- 最新已推送自动化修复 head `1a3c044` 的本地门禁与 GitHub checks 已通过；本 checkpoint 仅更新 active recovery carrier，使恢复事实与当前 merge-gate 状态一致。

## 下一步动作

- 等待最新 PR head 的 GitHub checks 全部通过。
- 运行 `scripts/pr_guardian.py review 349 --post-review` 作为最终 merge gate 复核。
- guardian 与 GitHub checks 通过后使用受控合并入口。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.9.0` 前置校准 `v1.0.0` 与 `v1.x -> v2.0.0` 的路线、版本、分发与发布门禁边界。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：治理 / roadmap / version management boundary carrier。
- 阻塞：如果本事项不收口，后续 `v0.9.0`、`v1.0.0` 与 Python packaging 讨论仍可能分散在会话中。

## 已验证项

- `python3 -m unittest tests.governance.test_version_guard`
- `python3 scripts/version_guard.py --mode ci`
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
- `python3 .loom/bin/loom_flow.py shadow-parity --target . --blocking`
- `python3 -m unittest discover -s tests/governance -p 'test_*.py'`
- `git diff --check`

## 未决风险

- 本 recovery carrier 更新推送后，GitHub checks 与 guardian 仍需在最新 PR head 上重新执行。
- 本事项不会创建 Python package；后续若需要真实 packaging，必须进入独立 FR。

## 回滚方式

- 使用独立 revert PR 撤销本事项新增的 roadmap、version management、version guard、Python packaging 规划、policy 分类与测试增量。

## 最近一次 checkpoint 对应的 head SHA

- 已验证自动化修复 head：`1a3c044621d5a53481821a73734c578131241fdb`
- 本 recovery carrier 更新提交后，以 GitHub checks 与 guardian review 绑定的 live PR head 作为最终 merge gate 真相。
- 当前 PR head 由 guardian state / GitHub checks 绑定，不把本字段作为 merge gate 的 live head 替代来源。
