# GOV-0105 执行计划

## 关联信息

- item_key：`GOV-0105-integration-governance-baseline`
- Issue：`#105`
- item_type：`GOV`
- release：`governance-baseline`
- sprint：`integration-governance`
- 关联 spec：无（治理联动事项）
- 关联 decision：`docs/decisions/ADR-GOV-0105-integration-governance-baseline.md`
- 关联 PR：`#107`
- active 收口事项：`GOV-0105-integration-governance-baseline`

## 目标

- 为 `Syvert × WebEnvoy` 的跨仓协同补齐最小治理插槽，使当前仓库继续作为本地执行真相源，但在触及共享契约、跨仓依赖或联合验收时有明确的 integration 联动入口。

## 范围

- 本次纳入：`WORKFLOW.md`、`code_review.md`、`.github/PULL_REQUEST_TEMPLATE.md`、`.github/ISSUE_TEMPLATE/**`、`docs/decisions/ADR-GOV-0105-integration-governance-baseline.md`、当前 exec-plan，以及为受控 integration gate 落地所需的 `scripts/common.py`、`scripts/open_pr.py`、`scripts/pr_guardian.py`、`scripts/merge_pr.py`、`tests/governance/test_open_pr.py`、`tests/governance/test_pr_guardian.py`。
- 本次不纳入：自动 bot / 自动同步系统、新的产品仓库、跨仓实现代码、对现有 `Phase / FR / sprint` 语义做统一改造。

## 当前停点

- 最新可执行 checkpoint 已覆盖 Syvert 侧治理载体改造，并已在 GitHub owner 级 integration project、repo projects、labels 与 issue 回填层面建立联动基线。
- 当前回合已按 guardian finding 收紧 issue form schema、`integration_ref` 可核查性、guardian merge gate 解析逻辑与 merge-time 回滚路径，并补上 issue/work-item canonical integration 元数据与 PR `integration_check` 的一致性校验。
- 当前回合同时补入存量 PR 兼容策略：缺少 `integration_check` 的历史 PR 只有在其上位 issue / work item 尚未声明 canonical integration 字段时，才允许沿用 legacy 路径继续收口。
- 最新 guardian 已对当前 PR head 给出新一轮 finding；当前工作树正在补齐 legacy PR 兼容路径、`integration_ref` 语义等价比较、独立 worktree 下的仓库 slug 归一、以及 exec-plan 作用域与最终合并顺序的同步。

## 下一步动作

- 推送当前修正后的 `common.py` / guardian / `open_pr` / tests / exec-plan head，并等待 checks 全绿。
- 在当前工作分支准备进入最终合并前，先 rebase 到最新 `origin/main`。
- 针对 rebase 后的最新 head 重新运行 checks 与 guardian，确认 `latest guardian=APPROVE`、`safe_to_merge=true`、checks 全绿、PR 非 Draft、reviewed head 与 merge head 一致。
- 上述条件全部满足后，再通过 `python3 scripts/merge_pr.py 107 --delete-branch --confirm-integration-recheck` 走受控合并。

## 当前 checkpoint 推进的 release 目标

- 为当前治理基线建立可审查、可恢复、可合并的单一执行上下文，使 integration 联动规则不再只停留在 project 与 issue 字段层，而是进入受控 PR 流程。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`Syvert × WebEnvoy` integration governance baseline 的 Syvert 侧治理收口项。
- 阻塞：当前事项自身属于 `integration_touchpoint=active`、`external_dependency=both`、`merge_gate=integration_check_required` 的治理基线收口项；除本仓库 checks 与 guardian 外，merge 前还必须把 `integration_ref` 对应状态复核收口到 PR 元数据与受控 merge gate。

## 已验证项

- `python3` 成功解析 `.github/ISSUE_TEMPLATE/*.yml`
- 已人工复核 PR 模板、workflow、code review 与 issue forms 的 integration 字段口径一致
- owner 级 integration project、repo project 字段、labels 与治理锚点 issue 已落地
- `python3 -m unittest tests.governance.test_open_pr tests.governance.test_pr_guardian`
- `python3 scripts/context_guard.py --mode ci --base-sha 530f94a2e9c23684fc4119162c34a5292143f30a --head-sha HEAD --head-ref issue-105-integration-governance-baseline`
- `python3 scripts/governance_gate.py --mode ci --base-sha 530f94a2e9c23684fc4119162c34a5292143f30a --head-sha HEAD --head-ref issue-105-integration-governance-baseline`

## 未决风险

- `Syvert/main` 在当前审查回合内继续前进；任何基于旧 head 的 guardian 结论都不能直接用于最终合并，必须在最后一次 rebase 后重跑 checks 与 guardian。
- merge 前仍需再次核对 owner 级 integration project 的状态、依赖与联合验收口径。
- 若后续仍有未回填 canonical integration 字段的存量 issue / PR，需要在进入下一轮执行前补齐，避免长期依赖 legacy 兼容路径。
- 若后续继续扩张 integration 枚举或 gate 语义，需要再走独立治理回合，不应直接在当前 PR 上扩 scope。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销当前治理文档、issue forms 与 exec-plan 增量，并同步回退对应 project / issue 联动口径。

## 最近一次 checkpoint 对应的 head SHA

- 当前受审 head：以 PR `#107` 的 latest head 为准；本节不再把“当前受审 head”与静态 SHA 写成同一个值，避免文档在生成新 commit 时自带一拍滞后。
- 最近一轮已完成 guardian 的 checkpoint：`ab258a69c684b2ceb2914fa0b46ba4452765624a`
- 说明：该 checkpoint 已把上一轮 guardian finding 收口到 `local_only` 无法绕过 canonical integration 一致性校验、merge-time 回滚优先保留最新 PR 描述、以及 `open_pr` 对上位 Issue canonical integration 元数据的一致性校验；当前工作树继续在此基础上收口 guardian 于 `ab258a6` 提出的 fail-open 与最终 merge 前漂移保护问题。
