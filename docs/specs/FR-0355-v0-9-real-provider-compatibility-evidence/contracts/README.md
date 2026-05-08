# FR-0355 Contracts

## Contract Surface

`FR-0355` 不新增 Core public contract。它定义 `v0.9.0` release closeout 必须消费的 evidence contract，并复用以下已批准 contract：

- `FR-0024`：Adapter capability requirement。
- `FR-0025`：Provider capability offer。
- `FR-0026`：Adapter / Provider compatibility decision。
- `FR-0027`：multi-profile resource requirement proof。
- `FR-0351`：`v1.0.0` Core stable release gate。

## Required Evidence

- `external_provider_sample`：必须证明样本不是仓内 native provider 自证。
- `matched_case`：必须证明合法 external offer 与合法 requirement 可以得到 `matched`。
- `unmatched_case`：必须证明合法但不兼容输入得到 `unmatched`。
- `invalid_contract_case`：必须证明非法或越界输入得到 `invalid_contract`。
- `provider_no_leakage`：必须证明 provider identity 不进入 Core-facing surfaces。
- `dual_reference_baseline`：必须证明小红书和抖音 `content_detail_by_url` regression 仍通过。
- `third_party_adapter_entry`：必须证明第三方 Adapter-only SDK + contract test 路径仍可独立解释。
- `api_cli_same_core_path`：必须证明 API 与 CLI 仍共享 Core path。

## Forbidden Interpretations

- `matched` 不等于 selected provider。
- external provider sample 不等于指定 provider 产品正式支持。
- provider sample 不批准 provider selector、fallback、priority、ranking、marketplace 或 Core provider registry。
- provider sample 不替代双参考基线。
- provider sample 不扩大 approved slice 到 search/list/comment/batch/dataset 或发布能力。
