# CHORE-0321 FR-0025 Provider offer SDK evidence

## 目的

本文档把 `FR-0025` formal spec 与 `#320` validator / fixtures 转成 Adapter 作者可引用的证据口径。它不定义新的 carrier，不修改 formal spec，也不提前定义 `FR-0026` compatibility decision。

## 主干事实

- Formal carrier：`ProviderCapabilityOffer`，由 `docs/specs/FR-0025-provider-capability-offer-contract/` 冻结。
- Validator truth：`syvert/provider_capability_offer.py`。
- Fixture truth：`tests/runtime/provider_capability_offer_fixtures.py::valid_provider_capability_offer()`。
- Regression truth：`tests/runtime/test_provider_capability_offer.py`。
- SDK author surface：`adapter-sdk.md` 的 `Adapter + Provider` 与 `ProviderCapabilityOffer` 示例。

## 合法 offer 解释

合法 validator 结果只表示 `declared`：

- offer carrier 结构可信。
- offer 绑定到单一 Adapter-owned provider port。
- offer 的 resource support 已回指 `FR-0027` approved profile proof，并且 proof 覆盖当前 `adapter_key`。
- offer 的错误、版本、lifecycle、observability 与 fail-closed 口径满足 `FR-0025`。

`declared` 不表示：

- Adapter requirement 已匹配。
- provider 被 Core 选中或排序。
- provider 可作为 fallback candidate。
- Core 可以发现、路由或直接调用 provider。
- 真实 provider 产品获得正式支持、SLA、marketplace listing 或发布承诺。

## Fixture refs

`#320` fixture 当前使用以下 canonical refs：

- Provider offer evidence：`fr-0025:offer-manifest-fixture-validator:content-detail-by-url-hybrid`
- Adapter binding evidence：`fr-0021:adapter-provider-port-boundary:adapter-owned-provider-port`
- Resource profile evidence：`fr-0027:profile:content-detail-by-url-hybrid:account-proxy`
- Resource profile evidence：`fr-0027:profile:content-detail-by-url-hybrid:account`

这些 refs 的解释边界：

- `fr-0025:*` 证明 offer manifest / validator / SDK docs 采用同一 `ProviderCapabilityOffer` carrier。
- `fr-0021:*` 证明 provider 只通过 Adapter-owned provider port 进入系统。
- `fr-0027:*` 证明 resource profile tuple、approved execution slice 与 reference adapter coverage，不能替代 `FR-0026` decision。

## 作者迁移口径

Adapter 作者从旧 provider port 文档迁移到 `ProviderCapabilityOffer` 时，应按以下顺序处理：

1. 保留 Adapter 作为唯一 Syvert 接入入口；不要把 provider 注册到 Core。
2. 为每个 Adapter-bound provider offer 填写 `provider_key`、`adapter_binding`、`capability_offer`、`resource_support`、`error_carrier`、`version`、`evidence`、`lifecycle`、`observability` 与 `fail_closed`。
3. 保证 `adapter_binding.provider_port_ref` 使用当前 Adapter 前缀，例如 `xhs:adapter-owned-provider-port`。
4. 使用 `FR-0027` approved profile proof refs 填写 `resource_support.supported_profiles[*].evidence_refs`，并确认 proof 覆盖当前 Adapter。
5. 保证 provider 错误只能经 Adapter 映射到既有 Adapter / runtime failed envelope。
6. 把 `declared` offer 交给后续 `FR-0026` compatibility decision，不在 offer 文档中声明 `matched`、selector、priority、score 或 fallback。

## 禁止证据来源

- provider 私有注释
- 临时运行日志
- marketplace 文案
- 未经批准的真实 provider 产品材料
- Core registry discovery 输出
- Core routing、TaskRecord 或 resource lifecycle provider 字段
- Playwright、CDP、Chromium、browser profile、network tier 或 transport 技术字段

## 后续消费

- `#322` 父 FR closeout 可以引用本文档说明 `FR-0025` 已具备 SDK docs / evidence 口径。
- `FR-0026` 只能把合法 offer 作为 Provider-side input 消费；若 offer validator 返回 invalid，decision 必须输出 `invalid_contract + invalid_provider_offer_contract`，不得构造匹配结果。
