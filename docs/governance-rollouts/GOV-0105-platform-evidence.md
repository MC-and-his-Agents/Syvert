# GOV-0105 Platform Evidence

## 关联信息

- Issue：`#105`
- item_key：`GOV-0105-integration-governance-baseline`
- release：`governance-baseline`
- sprint：`integration-governance`

## 目标

- 为 GOV-0105 保留 repo 外 rollout facts 的独立证据入口。
- 证明 external GitHub Project / labels / backfill 只作为 rollout evidence 存在，不再回写到 canonical integration contract 主体。

## 外部 evidence 入口

- integration project item：<https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_lADOECSWpc4BUdmRzgpwYyM>
- canonical issue：<https://github.com/MC-and-his-Agents/Syvert/issues/105>
- superseded PR candidate：<https://github.com/MC-and-his-Agents/Syvert/pull/107>

## 当前核验记录

- `#105` 当前 labels：
  - `governance`
  - `integration:active`
- `#105` 当前 project items：
  - `Syvert 主交付看板`：`Todo`
  - `Syvert × WebEnvoy Integration`：`Review`
- `integration_ref` 当前指向 owner 级 project item，live state 已可由 merge gate / `governance_status` 读取。

## Replacement Chain

- `PR-A Contract Kernel`：`#114`
- `PR-B Consumer Wiring`：`#115`
- `PR-C Carrier Alignment`：`#116`
- `PR-D Evidence / Rollout`：本批 docs closeout round

## 边界说明

- 本文档只记录 repo 外 rollout evidence 与 superseded closeout 所需的核验入口。
- canonical integration contract 的字段、枚举、merge gate 语义与 consumer 规则，以 `scripts/policy/integration_contract.json` 与 `scripts/integration_contract.py` 为准，不在此处重复。
