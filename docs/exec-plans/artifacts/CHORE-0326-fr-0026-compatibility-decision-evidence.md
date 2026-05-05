# CHORE-0326 FR-0026 compatibility decision docs evidence

## 目的

本文档把 `FR-0026` formal spec、`#324` runtime decision 与 `#325` no-leakage guard 转成 Adapter / Provider 作者可引用的文档证据。它不定义新的 carrier，不修改 formal spec，也不关闭父 FR `#298`。

## 主干事实

- Formal suite：`docs/specs/FR-0026-adapter-provider-compatibility-decision/`
- Runtime truth：`syvert/adapter_provider_compatibility_decision.py`
- No-leakage truth：`syvert/provider_no_leakage_guard.py`
- Runtime regression truth：`tests/runtime/test_adapter_provider_compatibility_decision.py`
- No-leakage regression truth：`tests/runtime/test_provider_no_leakage_guard.py`
- SDK author surface：`adapter-sdk.md` 的 `FR-0026 AdapterProviderCompatibilityDecision` 说明。

## Decision 输入解释

`AdapterProviderCompatibilityDecision` 只消费两类已冻结输入：

- Requirement-side：`FR-0024` 的 `AdapterCapabilityRequirement`。
- Offer-side：`FR-0025` 的 `ProviderCapabilityOffer`。

Decision validation 会同时消费 `FR-0027` approved profile proof。它不复制 requirement / offer / resource profile carrier 本体，也不引入 Core provider discovery、routing、selector、priority、fallback 或 marketplace。

## 状态解释

- `matched`：合法 requirement 与合法 Adapter-bound offer 在同一 Adapter、同一 approved execution slice 下存在至少一个 canonical resource profile tuple 完全一致。
- `unmatched`：合法 requirement 与合法 Adapter-bound offer 没有可满足的 resource profile 交集；这是合法但不兼容，不是输入违法。
- `invalid_contract`：requirement、offer、proof、adapter binding、execution slice、decision context 或 no-leakage 任一 contract violation；必须 fail-closed。

## Fail-closed 示例

### matched

合法 requirement 和 offer 同时覆盖 `content_detail + content_detail_by_url + url + hybrid`，并且 `account_proxy` / `account` profile proof 均命中 `FR-0027` approved profile：

```text
decision_status=matched
matched_profiles=account_proxy, account
error=null
fail_closed=true
```

### unmatched

requirement 只接受 `account_proxy`，offer 只支持 `account`，两侧输入本身合法：

```text
decision_status=unmatched
matched_profiles=[]
error=null
fail_closed=true
```

### invalid_contract

offer 不满足 `FR-0025`、proof 不满足 `FR-0027`、adapter key / execution slice 不一致，或 Core-facing surface 泄漏 provider 字段：

```text
decision_status=invalid_contract
error.failure_category=runtime_contract
error.error_code=invalid_provider_offer_contract | invalid_requirement_contract | invalid_compatibility_contract | provider_leakage_detected
fail_closed=true
```

## No-leakage evidence

`#325` guard 的证据口径：

- Core projection 不携带 `provider_key`、`offer_id` 或完整 Adapter-bound provider evidence。
- Adapter registry discovery 不携带 provider capability、provider registry entry、selector、routing 或 marketplace。
- TaskRecord 不新增 provider-specific public fields。
- Resource lifecycle 不新增 provider-owned lifecycle、resource supply、resource pool、account pool、proxy pool 或 provider lease surface。
- Failed envelope 不新增 Core-facing provider category。
- Runtime technical fields，例如 Playwright、CDP、Chromium、browser profile、network tier、transport、sign service，不进入 Core-facing decision surface。

Adapter-bound evidence 可以保留 provider identity，用于审查 decision 的来源；该 evidence 不得复制到 Core-facing projection、TaskRecord、resource lifecycle 或 registry discovery。

## 作者迁移口径

1. 先声明 `AdapterCapabilityRequirement` 与 `ProviderCapabilityOffer`，不要直接构造 compatibility result。
2. 使用 `FR-0027` approved profile proof refs 绑定 requirement profile 与 offer supported profile。
3. 把 `ProviderCapabilityOffer.declared` 交给 `FR-0026` decision；不要把 `declared` 当成 `matched`。
4. 只把 `matched` 解释为 formal compatibility，不解释为 selected provider、priority、fallback 或 Core routing。
5. 对 `unmatched` 保持 fail-closed，不自动尝试其它 provider。
6. 对 `invalid_contract` 返回 runtime contract 口径，不新增 provider failed envelope category。

## 禁止证据来源

- provider 私有注释
- 临时运行日志
- marketplace 文案
- 未经批准的真实 provider 产品材料
- Core registry discovery 输出
- Core routing、TaskRecord 或 resource lifecycle provider 字段
- Playwright、CDP、Chromium、browser profile、network tier、transport 或 sign service 技术字段

## 后续消费

- `#327` 父 FR closeout 可以引用本文档说明 `FR-0026` 已具备 runtime、no-leakage、SDK docs 与 evidence 口径。
- `v0.9.0` 真实 provider 验证样本可以消费本 decision contract，但不得回写改变 `v0.8.0` 的 no-leakage 边界。
