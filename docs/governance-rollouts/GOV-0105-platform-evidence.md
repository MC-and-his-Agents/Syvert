# GOV-0105 Platform Evidence

## 目的

为 `GOV-0105-integration-governance-baseline` 记录 GitHub 平台侧 rollout 的可验证入口。  
本文件是外部 rollout 证明，不是 workflow contract。

## 验证对象

- owner integration project:
  - `Syvert × WebEnvoy Integration`
  - https://github.com/orgs/MC-and-his-Agents/projects/3
- repo project:
  - `Syvert 主交付看板`
  - https://github.com/orgs/MC-and-his-Agents/projects/2
- peer repo project:
  - `WebEnvoy`
  - https://github.com/orgs/MC-and-his-Agents/projects/1
- anchor issue:
  - `Syvert#105`
  - https://github.com/MC-and-his-Agents/Syvert/issues/105

## 推荐验证命令

- `env GH_TOKEN="$GH_TOKEN" gh project view 3 --owner MC-and-his-Agents`
- `env GH_TOKEN="$GH_TOKEN" gh project view 2 --owner MC-and-his-Agents`
- `env GH_TOKEN="$GH_TOKEN" gh project view 1 --owner MC-and-his-Agents`
- `env GH_TOKEN="$GH_TOKEN" gh label list --repo MC-and-his-Agents/Syvert`
- `env GH_TOKEN="$GH_TOKEN" gh issue view 105 --repo MC-and-his-Agents/Syvert --json number,title,url,body`
- `env GH_TOKEN="$GH_TOKEN" gh issue list --repo MC-and-his-Agents/Syvert --state open --limit 20`

## 当前抽样

- owner integration project 已可读，project id 为 `3`
- `Syvert 主交付看板` 已存在 `Integration Touchpoint`、`Integration Ref`、`External Dependency`、`Merge Gate`、`Contract Surface`、`Joint Acceptance` 字段
- `WebEnvoy` 已存在同口径 integration 联动字段
- `Syvert#105` 当前已声明 canonical integration 元数据，并绑定 `https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_lADOECSWpc4BUdmRzgpwYyM`
- Syvert 仓库 labels 中已存在：
  - `integration:check-required`
  - `integration:active`
  - `contract-surface:execution-provider`
  - `contract-surface:ids-trace`
  - `contract-surface:errors`
  - `contract-surface:raw-normalized`
  - `contract-surface:diagnostics-observability`
  - `contract-surface:runtime-modes`

## 验收记录

- 最近一次验证日期：`2026-04-14`
- 验证方式：`gh` 只读查询
- 说明：本文件只提供外部 rollout 的验证入口与抽样结果；reviewer / guardian / merge gate 的运行时输入仍以 issue / PR canonical integration 与 `integration_ref` 的实时读取结果为准
