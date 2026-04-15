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

- 采集时间：`2026-04-15T02:56:55Z`
- 采集命令：
  - `gh issue view 105 --repo MC-and-his-Agents/Syvert --json url,state,labels,projectItems,body`
  - `gh issue view 107 --repo MC-and-his-Agents/Syvert --json url,state,title`
  - `gh pr view 114 --repo MC-and-his-Agents/Syvert --json url,mergedAt,title`
  - `gh pr view 115 --repo MC-and-his-Agents/Syvert --json url,mergedAt,title`
  - `gh pr view 116 --repo MC-and-his-Agents/Syvert --json url,mergedAt,title`
  - `gh pr view 117 --repo MC-and-his-Agents/Syvert --json url,state,isDraft,title`
- `#105` 当前 labels：
  - `governance`
  - `integration:active`
- `#105` 当前 project items：
  - `Syvert 主交付看板`：`Todo`
  - `Syvert × WebEnvoy Integration`：`Review`
- `integration_ref` 当前指向 owner 级 project item，live state 已可由 merge gate / `governance_status` 读取。
- `#107` 当前状态：`OPEN`；待 replacement chain 完整后关闭为 superseded。
- `#114` / `#115` / `#116` 已分别在 `2026-04-14T10:04:20Z`、`2026-04-14T17:28:37Z`、`2026-04-15T02:19:22Z` 合并。
- 在 `2026-04-15T02:56:55Z` 的采集快照中，`#117` 为当前 `PR-D Evidence / Rollout` docs closeout PR，状态为 `OPEN`、`Draft=true`。

## Backfill

- GOV-0105 在进入 PR-D 前已经具备 canonical integration metadata、`integration:active` label 与 owner 级 integration project item。
- 本轮没有额外执行新的 labels / project / field backfill 变更；PR-D 只把这些既有外部事实的核验入口与快照集中保存在本 evidence 文档中。

## Replacement Chain

- `PR-A Contract Kernel`：`#114`
- `PR-B Consumer Wiring`：`#115`
- `PR-C Carrier Alignment`：`#116`
- `PR-D Evidence / Rollout`：`#117`

## 边界说明

- 本文档只记录 repo 外 rollout evidence 与 superseded closeout 所需的核验入口。
- canonical integration contract 的字段、枚举、merge gate 语义与 consumer 规则，以 `scripts/policy/integration_contract.json` 与 `scripts/integration_contract.py` 为准，不在此处重复。
