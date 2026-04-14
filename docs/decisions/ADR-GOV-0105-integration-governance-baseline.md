# ADR-GOV-0105 Syvert × WebEnvoy integration governance baseline

## 关联信息

- Issue：`#105`
- item_key：`GOV-0105-integration-governance-baseline`
- item_type：`GOV`
- release：`governance-baseline`
- sprint：`integration-governance`

## 背景

当前 owner 下已经同时推进 `Syvert` 与 `WebEnvoy`，但两个仓库此前缺少统一的跨仓治理插槽，导致共享契约、跨仓依赖与联合验收只能靠口头约定或临时同步处理。

`#107` 已验证单一大 PR 会把 contract 定义、消费者接线、载体对齐和 rollout evidence 一次性耦合，超出稳定审查范围。本事项改为按同一 Work Item `#105` 串行拆成多个小 PR 落地。

## 决策

- canonical integration contract 的单一真相源固定在仓库内：机器可读定义位于 `scripts/policy/integration_contract.json`，共享消费逻辑位于 `scripts/integration_contract.py`。
- 本事项按四个串行 PR 收口：`PR-A Contract Kernel`、`PR-B Consumer Wiring`、`PR-C Carrier Alignment`、`PR-D Evidence / Rollout`。
- 第一批必须先把 `Issue + decision + exec-plan` 的 bootstrap contract 落到 `main`，后续三个 PR 才能在同一事项上下文下继续通过受控入口推进。
- 两个仓库的 issue / PR / review / workflow 载体最终都只消费 canonical integration contract，不再各自维护第二套 integration 枚举或组合约束。
- 纯本仓库事项保持 `integration_touchpoint=none`；触及共享契约、跨仓依赖或联合验收时，必须显式绑定 integration ref。
- 外部 GitHub Project、labels 与 issue backfill 只作为 rollout evidence，不再写入 repo 内 contract 主体。

## 约束

- 本轮只补跨仓联动插槽，不引入自动 bot、自动同步或第三个代码仓库。
- 本地 issue / PR 仍是执行与关闭真相源；外部 integration project 只承担协调语义，且其当前 live state 只能作为 merge gate 运行时输入。
- 当前事项继续只使用 `Issue #105` / `item_key=GOV-0105-integration-governance-baseline`，不额外拆新的执行 issue。
- 若后续扩张共享契约枚举、联合验收流程或 merge gate 语义，必须在新的独立治理事项中推进，不得直接扩展当前事项范围。

## 影响

- 当前事项的 bootstrap contract 由 `Issue #105 + ADR-GOV-0105 + GOV-0105 exec-plan` 构成；替代链路中的各个 PR 只承担各自层级的实现与验证。
- `#107` 保留为冻结的拆分母体和审查历史容器，不再进入 merge；替代 PR 链路全部合并后再按 superseded 关闭。
- 后续所有触及跨仓共享契约的 Syvert / WebEnvoy PR，都必须通过 canonical integration contract 显式判断是否进入 integration merge gate。
