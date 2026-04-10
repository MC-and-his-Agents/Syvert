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

- 最近一次显式实现 checkpoint 对应提交 `4973734d2bf190a9679951166916fceab9018f91`，其内容把当前事项输入契约收敛到 `item_context` 单一事实源，并让 `open_pr` / `context_guard` 共同消费 `formal_spec -> bootstrap -> unbound` 三种模式判断。
- 该 checkpoint 已解决本轮四个真实阻断：
  - `context_guard` 不再把 bootstrap decision 完整性错误施加到所有 touched `exec-plan`
  - `open_pr` 的 bootstrap fallback 已收紧到“当前事项自己的 active exec-plan + 关联 decision”
  - `docs/specs/README.md` 不再把当前 Work Item 完整上下文写成 formal spec 必需输入
  - `FR-0003 plan.md` 的手动验证与 implementation-ready 叙述已切换到 `#57 / GOV-0028`
- 当前 head 正在补记恢复证据与验证矩阵；下一步是推送 PR `#60` 最新 head，并仅针对该最新 head 重跑 guardian / merge gate。

## 下一步动作

- 推送 PR `#60` 最新 head，并核对该 head 对应的 GitHub checks。
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
- `python3 -m unittest tests/governance/test_item_context.py tests/governance/test_spec_guard.py tests/governance/test_context_guard.py tests/governance/test_open_pr.py tests/governance/test_pr_scope_guard.py tests/governance/test_workflow_guard.py tests/governance/test_pr_guardian.py`
- `python3 scripts/spec_guard.py --all`
- `python3 scripts/context_guard.py`
- `python3 scripts/workflow_guard.py`
- `python3 scripts/open_pr.py --class governance --issue 57 --item-key GOV-0028-harness-compat-migration --item-type GOV --release v0.2.0 --sprint 2026-S15 --closing fixes --dry-run`
- 已创建 PR：`#60 https://github.com/MC-and-his-Agents/Syvert/pull/60`
- 已补齐 PR 描述中的 `fixes #57`、`refs #55`、`refs #54`、风险与验证说明
- 已确认 `open_pr` 对当前事项优先消费 active `exec-plan` 的绑定输入：`formal_spec` 模式只认当前 `关联 spec`，`bootstrap` 模式只认当前 `关联 decision`
- 已确认 `context_guard` 对 touched `exec-plan` 按输入模式施加校验：非 `GOV` unbound 路径不再被 bootstrap contract 误伤
- 已确认新路径只要求 `spec.md + plan.md` 即可通过 formal spec / guard / `open_pr` 入口
- 已确认 legacy `TODO.md` 仍保持“存在则继续读取与校验；缺失不阻塞新事项；touched 删除仍在 `GOV-0028` 拒绝，最终清理由 `#58 / GOV-0029` 负责”

## 未决风险

- 若 review / guardian 仍隐式依赖历史 `TODO.md` 叙事，可能仍需在 PR 描述或评审评论中更明确地强调“默认输入已切换到 spec / plan / bootstrap contract / exec-plan”。
- 若后续 `#58` 清理 PR 没有延续本轮的 legacy 兼容边界，可能误删仍被历史事项使用的 `TODO.md`。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对治理脚本、治理测试、workflow 与文档模板的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `4973734d2bf190a9679951166916fceab9018f91`
