# FR-0387 Resource governance admission and health contract

## 关联信息

- item_key：`FR-0387-resource-governance-admission-and-health-contract`
- Issue：`#387`
- item_type：`FR`
- release：`v1.2.0`
- sprint：`2026-S24`
- Parent Phase：`#380`
- Parent FR：`#387`
- 执行 Work Item：`#388 / CHORE-0388-v1-2-resource-governance-spec`

## 背景与目标

- 背景：`v1.1.0` 已发布 operation taxonomy foundation，现有 `account` / `proxy` lifecycle、trace 与 injection contract 仍只表达资源是否可分配、是否占用、是否失效。XHS `content_detail_by_url` 的 `account_proxy` 路径已经证明 Core 需要区分 credential/session stale、invalid、unknown 与可继续执行状态，否则 opaque account material 会把会话失效、代理失败、provider 失败和输入失败混在同一层。
- 目标：冻结 `v1.2.0` resource governance admission and health contract，只定义 `CredentialMaterial`、`SessionHealth`、`ResourceHealthEvidence` 与 resource lease / invalidation / admission 边界，为后续 runtime carrier、consumer migration、evidence 与 release closeout 提供 formal spec 输入。

## 范围

- 本次纳入：
  - `CredentialMaterial` 作为 `account` resource material 的受管凭据边界。
  - `SessionHealth` 的最小健康判断语义。
  - `ResourceHealthEvidence` 的 provenance、观测时间、resource / lease / task 绑定、诊断边界与脱敏要求。
  - resource health admission 如何消费既有 `ResourceRecord`、`ResourceLease`、`ResourceTraceEvent`。
  - 健康证据如何影响 admission、lease 收口与 invalidation 判定。
- 本次不纳入：
  - 新 runtime carrier 实现。
  - AdapterRequirement、ProviderOffer 或 compatibility decision consumer migration。
  - fake adapter、reference adapter 或真实 provider evidence 实现。
  - 自动登录、自动刷新 credential、健康修复循环或后台再验证机制。
  - 新资源类型、provider SLA、provider selector、fallback、ranking、marketplace、产品 UI 或 release closeout。

## 需求说明

- 功能需求：
  - `CredentialMaterial` 只能作为 `account` resource material 的受管凭据边界；本 FR 不新增 `credential`、`session`、`browser_state` 或其他资源类型。
  - Core 可以保存、校验、脱敏、注入和基于证据判定 `CredentialMaterial`，但不得把 cookie、token、header、session object、sign request 参数或平台私有字段提升为共享 routing metadata。
  - `SessionHealth` 必须至少能区分可继续执行、过期或疑似过期、已失效、未知四类健康状态；未知状态不得被当作新鲜健康证明。
  - `ResourceHealthEvidence` 必须记录 evidence provenance、observed_at、resource binding、lease / task binding、adapter / capability context、health status、reason 与 redaction boundary。
  - `healthy` evidence 必须带有可机器判定的 freshness boundary：`observed_at`、`expires_at` 与 `freshness_policy_ref`。Core 必须在 `ResourceAdmissionDecision.evaluated_at` 判定 freshness；若 `evaluated_at` 已经达到或超过 `expires_at`，必须把该 evidence 投影为 `stale`，不得继续当作 `healthy`。
  - Core 在资源 admission 前必须能消费最近有效的 health evidence；无法证明健康足够时必须 fail-closed 或拒绝把该资源注入需要健康凭据的执行路径。
  - Adapter 只能消费 Core 注入的 credential material，并通过标准诊断或资源处置提示反馈健康问题；最终 invalidation 与状态推进仍由 Core 执行。
  - health evidence 只能解释资源健康，不得被解释为 provider 产品支持、成功率、SLA 或 routing 优先级。
- 契约需求：
  - 平台私有 credential/session 字段不得进入 `AdapterCapabilityRequirement`、`ProviderCapabilityOffer`、registry discovery、TaskRecord public envelope、resource requirement profile、Core routing metadata 或 Core-facing error category。
  - `ResourceRecord.status` 仍只复用既有 `AVAILABLE / IN_USE / INVALID`；`SessionHealth` 不得成为第二套 resource lifecycle status。
  - `ResourceLease` 仍是资源占用和收口的唯一共享 carrier；health evidence 可以绑定 lease，但不得重写 lease schema 或绕过 release 语义。
  - `ResourceTraceEvent` 仍是 task-bound 资源事件 truth；健康证据可引用 trace / lease / resource 关联，但不得替代 trace event。
  - 当 evidence 证明 credential/session invalid 时，Core 的最终资源状态收口必须通过既有 `release(target_status_after_release=INVALID)` 或等价后续 runtime carrier 承接。
  - pre-admission invalid evidence 若没有 active lease，不得调用 `release(target_status_after_release=INVALID)`，也不得直接把 `AVAILABLE` resource 改成 `INVALID`。在本 FR 内，它只能拒绝 admission；若后续需要库存态直接 invalidation carrier，必须另走 runtime/spec Work Item。
  - `stale` 只表示 freshness 不足或证据过期；它可以拒绝 admission，但不得单独把资源烧成 `INVALID`。只有后续 evidence 明确升级为 `invalid` 时，才允许进入 Core-owned invalidation。
- 非功能需求：
  - resource health contract 必须 fail-closed；无法证明 evidence 来源、时间、绑定或脱敏边界合法时，不得允许其影响 admission。
  - 所有 public carrier 必须默认脱敏，不得输出 raw secret、cookie、token、session dump、header value 或 provider private key。
  - 本 FR 只冻结 spec，不要求当前 PR 创建持久化 schema、API、CLI、runtime validator 或 migration。

## 约束

- 阶段约束：
  - `v1.2.0` 从 formal spec 开始；本 Work Item 只交付 spec suite。
  - 后续 runtime / migration / evidence / release closeout 必须在本 spec 合入后按实际需要另建 Work Item。
- 架构约束：
  - Core 负责 resource health admission、lease 收口与最终 invalidation。
  - Adapter 负责平台语义和对注入 material 的执行内消费，不负责直接改写共享 resource truth。
  - Provider 不能通过 offer 或 metadata 声明 cookie、token、session object、credential freshness 或 health SLA。
  - formal spec 与实现 PR 分离；本事项不得修改 `syvert/**`、`tests/**`、SDK 文档或 release index。

## GWT 验收场景

### 场景 1：健康凭据可以进入资源 admission

Given `account` resource 带有受管 `CredentialMaterial`，且 Core 已记录该 resource 的有效 `SessionHealth=healthy` evidence  
When Core 为需要 `account_proxy` 的 `content_detail_by_url` task 执行 resource admission  
Then Core 可以把该 account 与 proxy 作为同一 `ResourceBundle` 注入 Adapter，且 public carrier 不暴露 raw credential secret

### 场景 2：未知健康不得伪装为健康证明

Given `account` resource 只有 opaque material，且没有可验证的 `ResourceHealthEvidence`  
When 需要 credential/session health 的执行路径请求该 account  
Then Core 必须把 health 视为 unknown，并不得把 unknown 当作 fresh healthy evidence

### 场景 3：已失效 session 必须导向 invalidation 边界

Given Adapter 在执行期间通过标准诊断反馈当前 injected account session 已失效  
When Core 消费该诊断并建立 `ResourceHealthEvidence(status=invalid)`  
Then 最终资源收口必须走 Core-owned invalidation 语义，而不是由 Adapter 直接改写 resource state

### 场景 4：pre-admission invalid evidence 不得绕过 active lease

Given 某个 `account` resource 当前处于 `AVAILABLE`，且 Core 在 admission 前得到 `SessionHealth=invalid` evidence  
When 当前没有 active `ResourceLease` 持有该 resource  
Then Core 必须拒绝 admission，但不得调用 `release(target_status_after_release=INVALID)` 或直接把该 resource 改成 `INVALID`

### 场景 5：过期 healthy evidence 必须投影为 stale

Given 某条 `ResourceHealthEvidence(status=healthy)` 带有 `expires_at`，且 admission decision 带有 `evaluated_at`  
When admission evaluation time 已经达到或超过 `expires_at`  
Then Core 必须把该 evidence 投影为 `stale` 并拒绝需要 fresh credential 的 admission

### 场景 6：credential 私有字段不得进入 Adapter/Provider metadata

Given Adapter requirement 或 Provider offer 试图声明 `cookies`、`xsec_token`、`verify_fp`、`ms_token`、`headers` 或 session object 字段  
When contract consumer 校验该 metadata  
Then 该声明必须被视为 contract violation，而不是合法 resource capability

### 场景 7：health evidence 不得替代 lease truth

Given 某条 `ResourceHealthEvidence` 引用了 `lease_id` 与 `resource_id`  
When 系统重建 task 的资源占用与收口过程  
Then 仍必须以 `ResourceLease` 与 `ResourceTraceEvent` 为生命周期 truth，health evidence 只能作为 admission / invalidation 判断依据

## 异常与边界场景

- 异常场景：
  - evidence 缺少 `resource_id`、`observed_at`、`status`、`provenance` 或脱敏边界时必须 `invalid_contract`，不得被当作 `SessionHealth=invalid`。
  - `healthy` evidence 缺少 `expires_at` 或 `freshness_policy_ref` 时不得作为 fresh credential 证明，且必须按 evidence contract invalid fail-closed。
  - evidence 引用的 `lease_id / task_id / adapter_key / capability` 与当前执行上下文不一致时必须 `invalid_contract` fail-closed。
  - evidence payload 含 raw secret、cookie、token、header value 或 session dump 时必须 `invalid_contract`，不得触发 session invalidation。
  - Provider offer 或 Adapter requirement 暴露 credential/session 私有字段时必须 invalid。
- 边界场景：
  - `SessionHealth=unknown` 可以作为“需要进一步证明”的 admission-time projection 存在，但不得写成持久化 `ResourceHealthEvidence.status`，也不得提升为健康证明。
  - `stale` 或 `expired` 不自动要求本 FR 定义刷新机制，也不自动等同于 `INVALID`；恢复、刷新、重新登录与人工修复属于后续 FR。
  - `CredentialMaterial` 是 account material 的治理边界，不改变 `proxy` material 的最小 contract。
  - 本 FR 不定义新的 public operation，也不改变 `content_detail_by_url` stable baseline。

## 验收标准

- [ ] formal spec 明确冻结 `CredentialMaterial` 只属于 `account` resource material 边界，不新增资源类型。
- [ ] formal spec 明确冻结 `SessionHealth` 最小状态与 unknown / stale / invalid / healthy 的 admission 语义。
- [ ] formal spec 明确冻结 `ResourceHealthEvidence` 的 provenance、时间、绑定、诊断与脱敏要求。
- [ ] formal spec 明确冻结 freshness / expiry 的机器判定规则。
- [ ] formal spec 明确 pre-admission invalid evidence 只能拒绝 admission，不能绕过 active lease 直接 release。
- [ ] formal spec 明确 malformed / unredacted / context-mismatched evidence 是 contract-invalid，不是 `SessionHealth=invalid`。
- [ ] formal spec 明确 health evidence 与 `ResourceRecord`、`ResourceLease`、`ResourceTraceEvent` 的关系。
- [ ] formal spec 明确 Adapter / Provider metadata 不得声明 credential/session 私有字段。
- [ ] formal spec 明确本 Work Item 不实现 runtime、不迁移 consumer、不补 evidence、不做 release closeout。

## 依赖与外部前提

- 外部依赖：
  - `v1.1.0` taxonomy 已发布。
  - `FR-0010` 已冻结 minimal resource lifecycle。
  - `FR-0011` 已冻结 task-bound resource tracing。
  - `FR-0012` 已冻结 Core-injected resource bundle and Adapter boundary。
  - `FR-0024`、`FR-0025`、`FR-0026`、`FR-0027` 已冻结 Adapter requirement、Provider offer、compatibility decision 与 multi-profile resource requirement baseline。
- 上下游影响：
  - 后续 runtime carrier Work Item 必须消费本 spec，而不是重新定义 health status 或 evidence shape。
  - 若 runtime carrier 影响 AdapterRequirement / ProviderOffer，必须另建 consumer migration Work Item。
  - 若需要 fake/reference/real evidence，必须另建 evidence Work Item。
