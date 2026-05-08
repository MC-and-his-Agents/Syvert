# ADR-GOV-0396 v1.2 Resource Governance Release Closeout

## 关联信息

- Issue：`#396`
- item_key：`GOV-0396-v1-2-resource-governance-release-closeout`
- item_type：`GOV`
- release：`v1.2.0`
- sprint：`2026-S24`

## Status

Accepted

## Decision

`v1.2.0` 发布语义固定为 Resource Governance Foundation。该 release 可以新增 resource governance formal spec、runtime carrier、consumer no-leakage boundary 与 replayable evidence，但不能发布自动登录、自动刷新、修复循环、新资源类型、provider health SLA 或新的 executable operation。

## Rationale

Resource governance 是后续读侧、写侧、batch / dataset 能力的前置条件。账号会话健康必须在 Core admission 与 invalidation 边界内被治理，否则 Adapter / Provider 会继续通过 opaque material 或 public metadata 私自表达 credential/session 状态，破坏 Core / Adapter / Provider 边界。

本 release 只冻结 foundation：CredentialMaterial redacted boundary、SessionHealth projection、ResourceHealthEvidence provenance / freshness / context binding、health admission fail-closed、active lease invalidation 与 consumer no-leakage。自动恢复和更高层资源产品化必须由后续 FR 单独批准。

## Consequences

- `content_detail_by_url` 仍是 stable baseline；本 release 不新增 executable operation。
- Core 拥有 resource health admission 与最终 invalidation。
- Adapter 只能消费 Core 注入 material 并返回标准诊断 / 处置提示。
- Provider / Adapter metadata 不得声明 credential/session 私有字段或 health SLA。
- 后续 runtime carrier 扩展、consumer migration、fake/reference evidence 与 release closeout 必须继续按 Work Item 拆分进入。
