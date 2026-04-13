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

- 本次纳入：`WORKFLOW.md`、`code_review.md`、`.github/PULL_REQUEST_TEMPLATE.md`、`.github/ISSUE_TEMPLATE/**`、`docs/decisions/ADR-GOV-0105-integration-governance-baseline.md` 与当前 exec-plan。
- 本次不纳入：自动 bot / 自动同步系统、新的产品仓库、跨仓实现代码、对现有 `Phase / FR / sprint` 语义做统一改造。

## 当前停点

- 最新可执行 checkpoint 已覆盖 Syvert 侧治理载体改造，并已在 GitHub owner 级 integration project、repo projects、labels 与 issue 回填层面建立联动基线。
- 当前回合已按 guardian finding 收紧 issue form schema：恢复 `Phase` 创建入口、给治理快捷表单补回上位绑定字段，并刷新 bootstrap contract 工件到当前受审 head。

## 下一步动作

- 推送当前修正后的 forms / exec-plan head，重新等待 PR `#107` 的 GitHub checks 与 guardian 结论。
- 若 guardian 给出 `APPROVE + safe_to_merge=true`，再通过 `python3 scripts/merge_pr.py 107 --delete-branch` 走受控合并。

## 当前 checkpoint 推进的 release 目标

- 为当前治理基线建立可审查、可恢复、可合并的单一执行上下文，使 integration 联动规则不再只停留在 project 与 issue 字段层，而是进入受控 PR 流程。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`Syvert × WebEnvoy` integration governance baseline 的 Syvert 侧治理收口项。
- 阻塞：当前事项自身属于 `integration_touchpoint=active`、`external_dependency=both`、`merge_gate=integration_check_required` 的治理基线收口项；除本仓库 checks 与 guardian 外，merge 前还必须把 `integration_ref` 对应状态复核收口到 PR 元数据与受控 merge gate。

## 已验证项

- `python3` 成功解析 `.github/ISSUE_TEMPLATE/*.yml`
- 已人工复核 PR 模板、workflow、code review 与 issue forms 的 integration 字段口径一致
- owner 级 integration project、repo project 字段、labels 与治理锚点 issue 已落地
- `python3 scripts/context_guard.py --mode ci --base-sha 530f94a2e9c23684fc4119162c34a5292143f30a --head-sha HEAD --head-ref issue-105-integration-governance-baseline`
- `python3 scripts/governance_gate.py --mode ci --base-sha 530f94a2e9c23684fc4119162c34a5292143f30a --head-sha HEAD --head-ref issue-105-integration-governance-baseline`

## 未决风险

- 当前受控入口尚未把 `integration_check` 元数据完整接入 `open_pr` / `merge_pr`；若不补齐，文档门禁与实际受控入口会继续漂移。
- merge 前仍需再次核对 owner 级 integration project 的状态、依赖与联合验收口径。
- 若后续继续扩张 integration 枚举或 gate 语义，需要再走独立治理回合，不应直接在当前 PR 上扩 scope。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销当前治理文档、issue forms 与 exec-plan 增量，并同步回退对应 project / issue 联动口径。

## 最近一次 checkpoint 对应的 head SHA

- `bb5cfea7906d5ab863499f68ff8bffc968fd8f07`
- 说明：若当前修正提交仅用于收口 guardian 对 forms / bootstrap contract 的阻断，本工件继续记录最近一次显式 checkpoint SHA；当前受审 head 以 PR `#107` 最新 head 与 guardian verdict 绑定为准。
