# GOV-0028 执行计划

## 关联信息

- item_key：`GOV-0028-harness-compat-migration`
- Issue：`#57`
- item_type：`GOV`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/`
- 关联 decision：`docs/decisions/ADR-0003-github-delivery-structure-and-repo-semantic-split.md`
- 关联 PR：`#60`
- active 收口事项：`GOV-0028-harness-compat-migration`

## 目标

- 让 repo harness、guard、template 与 review 输入适配新的 `Phase -> FR -> Work Item` 治理契约。
- 让新 formal spec suite 只要求 `spec.md + plan.md`，不再把 `TODO.md` 当作新事项硬依赖。
- 保留 legacy `TODO.md` 的兼容读取与回写路径，但不提前做最终删除清理。

## 范围

- 本次纳入：
  - `scripts/policy/policy.json`
  - `scripts/context_guard.py`
  - `scripts/workflow_contract.py`
  - `WORKFLOW.md`
  - `docs/AGENTS.md`
  - `docs/process/agent-loop.md`
  - `docs/specs/README.md`
  - `docs/specs/_template/TODO.md`
  - `docs/exec-plans/README.md`
  - `spec_review.md`
  - `code_review.md`
  - `tests/governance/test_spec_guard.py`
  - `tests/governance/test_context_guard.py`
  - `tests/governance/test_open_pr.py`
  - `tests/governance/test_workflow_guard.py`
  - 本 exec-plan
- 本次不纳入：
  - 删除任何现有 `TODO.md`
  - 大规模改写存量 `exec-plan`
  - 新增项目管理状态页面
  - 任何业务实现代码

## 当前停点

- 最近一次显式 checkpoint 对应提交 `0417d437ee8dcc880f8e544019400af6714d6d85`，其内容已覆盖治理测试、policy、guard、workflow contract、formal spec/agent-loop/review 文档收口。
- 当前 head 仅继续补充 `GOV-0028` 的 active `exec-plan` 与 PR 关联元数据，不单独推进新的 checkpoint。
- PR `#60` 已创建，当前停在等待 GitHub checks、guardian 与 merge gate 收口。

## 下一步动作

- 等待并核对 PR `#60` 的 GitHub checks。
- 运行 guardian / merge gate；若结论满足 `APPROVE + safe_to_merge=true` 且 checks 全绿，则通过受控入口合并。
- 合并后按分支/worktree 退役协议收口当前现场。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 的治理收敛回合提供可执行的 harness 契约，使 GitHub 单一调度层与仓内单一语义层在 guard、review 与恢复入口上真正对齐。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0003 / #55` 下的第二个治理 Work Item，负责把上一轮治理契约落到 harness、guard、template 与审查输入上。
- 阻塞：无外部阻塞；必须避免越界到 `#58` 的 legacy `TODO.md` 最终清理。

## 已验证项

- `python3 scripts/create_worktree.py --issue 57 --class governance`
- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`docs/process/agent-loop.md`
- 已核对 GitHub 真相：`#57 -> release=v0.2.0 -> sprint=2026-S15`
- `python3 -m unittest tests/governance/test_spec_guard.py tests/governance/test_context_guard.py tests/governance/test_open_pr.py tests/governance/test_workflow_guard.py`
- `python3 -m unittest tests/governance/test_spec_guard.py tests/governance/test_context_guard.py tests/governance/test_open_pr.py tests/governance/test_workflow_guard.py tests/governance/test_pr_scope_guard.py tests/governance/test_pr_guardian.py`
- `python3 scripts/spec_guard.py --all`
- `python3 scripts/context_guard.py`
- `python3 scripts/workflow_guard.py`
- 已创建 PR：`#60 https://github.com/MC-and-his-Agents/Syvert/pull/60`
- 已补齐 PR 描述中的 `fixes #57`、`refs #55`、`refs #54`、风险与验证说明

## 未决风险

- 若 review / guardian 仍隐式依赖历史 `TODO.md` 叙事，可能需要在 PR 描述中更明确地强调“默认输入已切换到 spec / plan / bootstrap contract / exec-plan”。
- 若后续 `#58` 清理 PR 没有延续本轮的 legacy 兼容边界，可能误删仍被历史事项使用的 `TODO.md`。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对治理脚本、治理测试、workflow 与文档模板的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `0417d437ee8dcc880f8e544019400af6714d6d85`
