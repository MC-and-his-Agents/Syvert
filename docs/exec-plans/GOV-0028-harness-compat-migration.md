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
  - `scripts/open_pr.py`
  - `scripts/item_context.py`
  - `scripts/workflow_contract.py`
  - `WORKFLOW.md`
  - `docs/AGENTS.md`
  - `docs/decisions/ADR-0003-github-delivery-structure-and-repo-semantic-split.md`
  - `docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/spec.md`
  - `docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/plan.md`
  - `docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/TODO.md`
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

- 最近一次显式 checkpoint 对应提交 `7ccd556ec1ee7edcd436fbbe73f1277c73ab8d30`，其内容在 `5d7cf9e09caf1aa7450dd10d6ea7fe924c9e32bd` 的基础上，同步了 active `exec-plan` 的恢复证据，并把 FR-0003 legacy `TODO.md` 改写为明确的历史语义，避免 reviewer / guardian 将其误读为当前执行面。
- 当前受审 head 已在该 checkpoint 之后继续收敛 formal-spec binding 契约：`open_pr` 不再允许无 `关联 spec` 的治理事项回退到 repo-wide FR suite，`context_guard` 开始校验 touched exec-plan 的 `关联 spec` 是否存在、留在仓内且指向满足最小套件的 formal spec。
- 对应治理测试与 guard 已补齐到新契约：覆盖 missing binding / out-of-repo / nonexistent / legacy file-path 四类 `关联 spec` 情况，并重新验证 `context_guard`、`workflow_guard`、`open_pr --dry-run` 与相关治理单测。
- 当前停在提交上述系统性收口、推送 PR `#60` 新 head，并再次进入 guardian / merge gate。

## 下一步动作

- 等待并核对 PR `#60` 针对当前 head 的 GitHub checks。
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
- `python3 scripts/open_pr.py --class governance --issue 57 --item-key GOV-0028-harness-compat-migration --item-type GOV --release v0.2.0 --sprint 2026-S15 --closing fixes --dry-run`
- `python3 -m unittest tests/governance/test_open_pr.py tests/governance/test_context_guard.py tests/governance/test_pr_guardian.py tests/governance/test_workflow_guard.py`
- 已创建 PR：`#60 https://github.com/MC-and-his-Agents/Syvert/pull/60`
- 已补齐 PR 描述中的 `fixes #57`、`refs #55`、`refs #54`、风险与验证说明
- 已确认 `open_pr` 对当前事项优先消费 active `exec-plan` 的 `关联 spec`
- 已确认 legacy `TODO.md` 满足“存在即继续校验、不存在不阻塞、删除可接受、模板存在则仓库模式持续 lint”

## 未决风险

- 若 review / guardian 仍隐式依赖历史 `TODO.md` 叙事，可能仍需在 PR 描述或评审评论中更明确地强调“默认输入已切换到 spec / plan / bootstrap contract / exec-plan”。
- 若后续 `#58` 清理 PR 没有延续本轮的 legacy 兼容边界，可能误删仍被历史事项使用的 `TODO.md`。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对治理脚本、治理测试、workflow 与文档模板的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `7ccd556ec1ee7edcd436fbbe73f1277c73ab8d30`
