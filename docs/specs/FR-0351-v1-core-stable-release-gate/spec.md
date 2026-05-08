# FR-0351 v1.0.0 Core stable release gate

## 关联信息

- item_key：`FR-0351-v1-core-stable-release-gate`
- Issue：`#351`
- item_type：`FR`
- release：`v1.0.0`
- sprint：`2026-S22`
- 上位 Phase：`#350`
- 关联执行事项：`#352 / CHORE-0352-v1-core-stable-release-gate-spec`

## 背景与目标

- 背景：`v0.8.0` 已完成第三方 Adapter 接入路径、Adapter capability requirement、Provider capability offer、Adapter / Provider compatibility decision 与 no-leakage guard 的主干收口。`v0.9.0` 将用真实外部 provider 验证样本压测这些 contract。`v1.0.0` 发布前仍缺少一个正式 release gate，用来判断 Core stable 是否已经满足。
- 目标：冻结 `v1.0.0` Core stable release gate 的检查项、证据输入、禁止边界与 closeout 规则，使 `v0.9.0` 完成后能用同一套 gate 判断是否可以发布 `v1.0.0`。

## 范围

- 本次纳入：
  - 冻结 `v1.0.0` Core stable release gate checklist。
  - 明确每个 gate item 的 required evidence 与 fail-closed 条件。
  - 明确 `v0.9.0` 真实 provider 验证样本是 `v1.0.0` gate 的必要输入。
  - 明确 `v1.0.0` 不要求上层应用、provider selector / fallback / marketplace 或 Python package publish。
  - 明确 release index、tag、GitHub Release 与 closeout truth 必须对齐后才可声明 `v1.0.0` 发布完成。
- 本次不纳入：
  - `v0.9.0` 真实 provider 样本的实现。
  - `v1.0.0` release closeout 本身。
  - runtime、Adapter、Provider 或 CI 代码变更。
  - Python packaging 实现或 PyPI / GitHub Packages publish。

## 需求说明

- 功能需求：
  - `v1.0.0` release gate 必须是 `v1.0.0` 发布前的 canonical checklist，不得只依赖 roadmap 文案或会话判断。
  - gate 必须覆盖 Core / Adapter / Provider 边界稳定性，证明 Core 仍只调用 Adapter，Provider 仍只作为 Adapter-bound execution capability 被 compatibility decision 消费。
  - gate 必须要求 `content_detail_by_url + url + hybrid` 双参考基线持续通过，且小红书、抖音参考适配器不得需要 Core 特殊分支。
  - gate 必须要求第三方 Adapter-only 接入路径可由 SDK、manifest / fixture、contract test 与 registry 校验独立解释。
  - gate 必须要求 Adapter + Provider compatibility decision 已有真实外部 provider 样本 evidence，证明 `ProviderCapabilityOffer -> AdapterProviderCompatibilityDecision -> Adapter-bound execution evidence` 可执行、可审计、可 fail-closed。
  - gate 必须要求 provider 信息不得进入 Core routing、registry discovery、TaskRecord、resource lifecycle、release gate source report 或 Core-facing failed envelope category。
  - gate 必须要求 CLI / HTTP API / release gate 仍消费同一 Core runtime path，不允许绕过 TaskRecord、resource lease、result envelope 或 observability carrier。
  - gate 必须要求 `docs/releases/v1.0.0.md`、annotated tag `v1.0.0`、GitHub Release、closeout Issue / PR 与 published truth carrier 对齐。
- 契约需求：
  - 每个 gate item 必须声明 `status`，允许值为 `pass`、`fail`、`not_applicable`。
  - `not_applicable` 必须携带理由和引用证据；不得用于跳过本 FR 标记为 required 的 gate item。
  - 任一 required gate item 为 `fail` 或缺少证据时，`v1.0.0` release gate 必须 fail-closed。
  - 真实 provider 样本 evidence 只证明 compatibility decision 链路可执行，不声明指定 provider 产品正式支持。
  - `v1.0.0` gate 不得把上层应用完整度、provider marketplace、selector / fallback 或 package publish 写成通过条件。
- 非功能需求：
  - gate checklist 必须可被 reviewer、guardian、release closeout Work Item 与未来自动化共同消费。
  - gate evidence 必须能从仓内 formal spec、exec-plan artifacts、release index、GitHub issues / PRs、Git tag 与 GitHub Release 复验。
  - gate 不得要求访问真实账号、私密 provider 配置或上层应用仓库才能判断 Core stable。

## Gate Items

| gate_id | required | 判定目标 | 最小 evidence |
|---|---:|---|---|
| `core_adapter_provider_boundary` | yes | Core / Adapter / Provider 边界无漂移 | platform leakage report、provider no-leakage report、relevant specs |
| `dual_reference_baseline` | yes | `content_detail_by_url` 双参考基线持续通过 | real adapter regression source report |
| `third_party_adapter_entry` | yes | 第三方 Adapter-only 接入路径可独立解释 | SDK docs、manifest / fixture、contract test entry |
| `provider_compatibility_sample` | yes | 真实 provider 样本证明 compatibility decision 链路可执行 | v0.9.0 provider sample evidence |
| `provider_no_leakage` | yes | provider 字段不进入 Core-facing surface | no-leakage guard evidence |
| `api_cli_same_core_path` | yes | API / CLI 共享 Core path | same-path tests / release gate evidence |
| `release_truth_alignment` | yes | release index、tag、GitHub Release、closeout 对齐 | `docs/releases/v1.0.0.md` published truth carrier |
| `application_boundary` | yes | 上层应用不进入 v1.0.0 完成条件 | roadmap / vision / release notes |
| `packaging_boundary` | yes | Python package publish 不是默认 gate | `docs/process/python-packaging.md` |

## GWT 验收场景

### 场景 1：所有 required gate item 均有证据时允许发布

Given `v0.9.0` 已完成真实 provider 样本 evidence，且所有 required gate item 的 status 均为 `pass`
When `v1.0.0` release closeout Work Item 汇总 gate evidence
Then `v1.0.0` release gate 可以返回 `pass`

### 场景 2：缺少真实 provider 样本时必须 fail-closed

Given `FR-0024`、`FR-0025`、`FR-0026` 与 no-leakage guard 均已存在
When 没有真实外部 provider 样本证明 compatibility decision 链路可执行
Then `provider_compatibility_sample` 必须为 `fail`，`v1.0.0` release gate 不得通过

### 场景 3：双参考基线漂移时不得发布 v1.0.0

Given `content_detail_by_url` 的小红书或抖音参考适配器回归失败
When release closeout 汇总 `dual_reference_baseline`
Then gate 必须返回 `fail`，不得用第三方 Adapter 或 provider 样本替代双参考基线

### 场景 4：provider 信息泄漏到 Core surface 时不得发布

Given compatibility decision 返回 `matched`
When Core routing、registry discovery、TaskRecord 或 resource lifecycle surface 出现 provider key、selector、fallback、routing 或 provider lifecycle 字段
Then `provider_no_leakage` 必须为 `fail`

### 场景 5：上层应用可运行不等于 v1.0.0 gate 通过

Given 某个账号矩阵、内容库、发布中心或自动运营应用可以消费 Syvert
When Core stable gate 缺少 provider sample、dual reference baseline 或 release truth evidence
Then `v1.0.0` release gate 仍必须失败

### 场景 6：Python package 未发布不阻塞 v1.0.0

Given Core stable gate 的 required runtime / contract / release truth evidence 均通过
When Syvert 尚未发布 PyPI / GitHub Packages artifact
Then `packaging_boundary` 可以为 `pass`，前提是 release notes 明确 package publish 不是本 release 交付物

### 场景 7：release truth 未回写时不得声明发布完成

Given `v1.0.0` tag 与 GitHub Release 已创建
When `docs/releases/v1.0.0.md` 尚未回写 tag target、GitHub Release URL 与 published at
Then `release_truth_alignment` 必须为 `fail`

## 异常与边界场景

- 如果某 gate item 只有会话描述、未入库证据或未绑定 GitHub / Git / release artifact，应视为缺少证据。
- 如果 `v0.9.0` provider sample evidence 声明某 provider 产品获得正式支持，应视为边界漂移，不能用于通过 `v1.0.0` gate。
- 如果 release closeout 把 `v1.0.0` 解释为上层应用完成版，应视为 `application_boundary` 失败。
- 如果 release closeout 把 Python package publish 缺失解释为必然失败，应视为 `packaging_boundary` 失败，除非该 release 明确把 package artifact 纳入交付物。
- 如果新增 capability contract 在 `v1.0.0` 前进入，应证明它不改写 `content_detail_by_url` 基线；否则应推迟到 `v1.x`。
- 如果某个 gate item 需要延期，必须在 GitHub FR / Work Item 中明确降级为 `v1.x` 候选；不得在 `v1.0.0` closeout 中静默跳过。

## 验收标准

- [ ] formal spec 冻结 `v1.0.0` Core stable release gate checklist。
- [ ] formal spec 明确真实 provider 样本 evidence 是 `v1.0.0` gate 的 required input。
- [ ] formal spec 明确 provider 样本不等于指定 provider 产品正式支持。
- [ ] formal spec 明确双参考 `content_detail_by_url` 基线不可由第三方样本替代。
- [ ] formal spec 明确 provider 信息不得进入 Core routing、registry、TaskRecord 或 resource lifecycle。
- [ ] formal spec 明确 API / CLI same Core path 是 release gate 条件。
- [ ] formal spec 明确 release index、tag、GitHub Release 与 closeout truth 必须对齐。
- [ ] formal spec 明确上层应用与 Python package publish 不属于 `v1.0.0` 默认完成条件。
- [ ] roadmap 与 version-management 已引用本 gate。
- [ ] 本事项不修改 runtime、Adapter、Provider 或 CI 代码。

## 依赖与外部前提

- `v0.8.0` 已完成第三方 Adapter 接入、Provider offer、compatibility decision 与 no-leakage guard 的 contract foundation。
- `v0.9.0` 必须提供真实 provider 样本 evidence，供 `provider_compatibility_sample` 消费。
- `v1.0.0` release closeout Work Item 必须消费本 FR，而不是重新解释 Core stable。

