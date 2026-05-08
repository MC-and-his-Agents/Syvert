# FR-0351 contracts

## release gate contract

`v1.0.0` release gate 必须消费本 FR 定义的 required gate items。缺少任一 required item 或 evidence 时，gate 必须 fail-closed。

## required evidence contract

- `core_adapter_provider_boundary`：必须引用 platform leakage 与 provider no-leakage 证据。
- `dual_reference_baseline`：必须引用双参考 real adapter regression evidence。
- `third_party_adapter_entry`：必须引用第三方 Adapter-only manifest / fixture / contract test entry evidence。
- `provider_compatibility_sample`：必须引用真实外部 provider sample evidence。
- `provider_no_leakage`：必须引用 Core-facing surface no-leakage evidence。
- `api_cli_same_core_path`：必须引用 CLI / API same Core path evidence。
- `release_truth_alignment`：必须引用 `docs/releases/v1.0.0.md`、tag target、GitHub Release URL 与 closeout Issue / PR。
- `application_boundary`：必须引用 roadmap / vision，证明上层应用不属于 `v1.0.0` gate。
- `packaging_boundary`：必须引用 `docs/process/python-packaging.md`，证明 package publish 不是默认 gate。

## forbidden interpretations

- `matched` compatibility decision 不得解释为 selected provider、fallback candidate、provider priority、SLA 或 provider 产品正式支持。
- 真实 provider sample evidence 不得把 provider 产品写成 Syvert 全局支持对象。
- 上层应用可运行不得替代 Core stable release gate。
- Python package publish 不得替代 Git tag / GitHub Release / release index truth。

