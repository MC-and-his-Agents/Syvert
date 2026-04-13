# ADR-GOV-0105 Syvert × WebEnvoy integration governance baseline

## 关联信息

- Issue：`#105`
- item_key：`GOV-0105-integration-governance-baseline`
- item_type：`GOV`
- release：`governance-baseline`
- sprint：`integration-governance`

## 背景

当前 owner 下已经同时推进 `Syvert` 与 `WebEnvoy`，但两个仓库此前缺少统一的跨仓治理插槽，导致共享契约、跨仓依赖与联合验收只能靠口头约定或临时同步处理。

本轮事项的目标不是合并两个治理栈，也不是新建第三个产品仓库，而是在保持两个仓库继续各自作为执行真相源的前提下，补齐最小 integration 协调层。

## 决策

- 新增 owner 级 `Syvert × WebEnvoy Integration` project，作为跨仓协调真相源。
- `Syvert Project` 与 `WebEnvoy Project` 继续分别承担各自仓库的本地执行真相，不合并为单一产品 project。
- 两个仓库的 issue / PR / review / workflow 载体统一补入 integration 字段与检查口径。
- 纯本仓库事项保持 `integration_touchpoint=none`；触及共享契约、跨仓依赖或联合验收时，必须显式绑定 integration ref。
- 各仓库继续按各自本地治理门禁拆分 PR；integration project 不规定另一仓库的内部文件切片方式。

## 约束

- 本轮只补跨仓联动插槽，不引入自动 bot、自动同步或第三个代码仓库。
- 本地 issue / PR 仍是执行与关闭真相源，integration project 只承担协调语义。
- 若后续扩张共享契约枚举、联合验收流程或 merge gate 语义，必须在新的独立治理事项中推进，不得直接扩展当前事项范围。

## 影响

- 当前事项的 bootstrap contract 由 `Issue #105 + ADR-GOV-0105 + GOV-0105 exec-plan` 构成；PR 只作为实现与验证载体，不反向进入 input contract。
- 后续所有触及跨仓共享契约的 Syvert / WebEnvoy PR，都必须显式判断是否进入 integration merge gate。
- integration 协调不再依赖隐式记忆，而是进入 project 字段、issue form、PR 模板与 guardian 审查链路。
