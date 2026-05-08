# FR-0387 contracts

## Contract name

`ResourceGovernanceHealthContract` / `v1.2.0`

## Contract purpose

本 contract 定义 account credential/session health 如何进入 Syvert resource admission、diagnostics 与 invalidation 判断。它复用既有 `ResourceRecord`、`ResourceLease`、`ResourceTraceEvent`、Adapter resource requirement、Provider offer 与 compatibility decision 边界，不新增 executable operation 或 runtime implementation。

## Core ownership rules

- Core 拥有 resource health admission、lease 收口与最终 invalidation。
- Core 只能基于已脱敏、可追溯、上下文匹配的 `ResourceHealthEvidence` 放行需要 credential/session health 的资源。
- Core 必须在 admission evaluation time 使用 `observed_at`、`expires_at` 与 `freshness_policy_ref` 判定 evidence freshness；过期 healthy evidence 必须投影为 `stale`。
- Core 不得在没有 active lease 的 pre-admission 场景中调用 `release(target_status_after_release=INVALID)`；这类 invalid evidence 在本 FR 内只能拒绝 admission。
- Core 必须把 malformed、unredacted 或 context-mismatched evidence 判定为 `invalid_contract`；这类 evidence 不是 `SessionHealth=invalid`，不得触发 resource invalidation。
- Core 不得把 `SessionHealth` 写成第二套 resource lifecycle status。
- Core-facing public envelope、TaskRecord public fields、registry discovery 与 routing metadata 不得暴露 raw credential/session material。

## Adapter consumer rules

- Adapter 只能消费 Core 注入的 `CredentialMaterial`。
- Adapter 可以把 material 派生为单次执行内的平台 session config、header、cookie 或网络配置。
- Adapter 不得自行来源化第二套账号、session 或 credential 作为主执行材料。
- Adapter 只能通过标准诊断或资源处置提示反馈 health 问题；不得直接改写 shared resource state、lease 或 trace truth。

## Provider and metadata rules

- Provider offer 不得声明 cookie、token、header、session object、credential freshness、health SLA 或 provider 私有登录状态。
- Adapter requirement 不得把 credential/session 私有字段写入 resource capability 或 profile。
- Compatibility decision 不得基于 provider 产品、credential freshness 或 health SLA 返回 `matched`。
- 健康证据不得被解释为 provider routing、fallback、priority、ranking、marketplace 或产品支持承诺。

## Forbidden carrier fields

以下字段或语义不得进入 public metadata、Core routing、TaskRecord public envelope、registry discovery、AdapterRequirement 或 ProviderOffer：

- raw cookie / token / header value / session dump
- `xsec_token`、`verify_fp`、`ms_token`、browser page state、sign request payload
- provider selector / routing / fallback / priority / ranking
- marketplace / provider product support / SLA
- login automation strategy、credential refresh workflow、operator secret note

## Compatibility rule

`v1.2.0` resource governance health contract 不改变 `content_detail_by_url + url + hybrid` stable baseline，不改变 `account` / `proxy` resource capability names，不改变 `AVAILABLE / IN_USE / INVALID` lifecycle state set。任何 runtime carrier、consumer migration 或 evidence implementation 都必须由后续 Work Item 在本 contract 合入后承接。
