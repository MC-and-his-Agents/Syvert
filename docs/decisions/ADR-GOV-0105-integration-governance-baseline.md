# ADR-GOV-0105 Syvert × WebEnvoy integration governance baseline

## 关联信息

- Issue：`#105`
- item_key：`GOV-0105-integration-governance-baseline`
- item_type：`GOV`
- release：`governance-baseline`
- sprint：`integration-governance`

## 背景

当前 owner 下已经同时推进 `Syvert` 与 `WebEnvoy`，仓库内需要一份稳定、单一的 canonical integration contract，来约束 issue / PR / reviewer / guardian / merge gate 的一致消费方式。

在 `PR-A Contract Kernel`、`PR-B Consumer Wiring` 与 `PR-C Carrier Alignment` 合并后，仓库内运行时消费者与 carrier 已经收口到同一 contract；剩余的 owner 级 GitHub Project、labels 与 backfill 事实只应作为 rollout evidence 保留，不能继续混入 contract 主体。

## 决策

- canonical integration contract 的单一真相源固定在仓库内：机器可读定义位于 `scripts/policy/integration_contract.json`，共享消费逻辑位于 `scripts/integration_contract.py`。
- 仓库内所有治理消费者都只消费这一份 canonical integration contract：Issue / Work Item metadata、PR `integration_check`、reviewer、guardian、`merge_pr` 与 `governance_status` 不得再各自维护第二套 integration 字段、枚举或组合约束。
- `WORKFLOW.md`、`code_review.md`、PR template 与 issue forms 只暴露 carrier 与消费边界，不承载第二套 contract 规则；`Phase` 不是 canonical integration metadata carrier。
- 纯本仓库事项保持 `integration_touchpoint=none`；触及共享契约、跨仓依赖或联合验收时，必须显式绑定 integration ref。
- 外部 GitHub Project、labels 与 issue backfill 只作为 rollout evidence，单独记录在 evidence 工件中，不再写入 repo 内 contract 主体、ADR 主体或 active `exec-plan` 主体。

## 约束

- 本轮只补跨仓联动插槽，不引入自动 bot、自动同步或第三个代码仓库。
- 本地 issue / PR 仍是执行与关闭真相源；外部 integration project 只承担协调语义，且其当前 live state 只能作为 merge gate 运行时输入。
- 若后续扩张共享契约枚举、联合验收流程或 merge gate 语义，必须在新的独立治理事项中推进，不得直接扩展当前事项范围。

## 影响

- 仓库内治理终态收口为“一份 canonical integration contract + 多个只读 consumer/carrier”，而不是“多份分散规则文本”。
- repo 内 contract 与 repo 外 rollout evidence 的职责彻底分离：前者决定 merge gate 与 consumer 语义，后者只保留外部系统的核验入口与 rollout 证据。
- 后续所有触及跨仓共享契约的 Syvert / WebEnvoy PR，都必须通过 canonical integration contract 显式判断是否进入 integration merge gate。
