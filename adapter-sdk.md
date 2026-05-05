# Syvert Adapter SDK

## 目标

本文件定义 Syvert Adapter SDK 的职责、最小接口和实现约束。

Adapter SDK 的目标是：

- 让平台接入变成标准化工作
- 让 Core 与平台实现彻底解耦
- 让适配器开发者只关注平台逻辑
- 让任务、资源和数据治理由 Core 统一负责


## 适配器的职责

适配器只负责平台接入，不负责系统治理。

适配器负责：

- 将标准任务输入转换为平台请求
- 使用 Core 提供的资源上下文执行请求
- 处理平台响应
- 返回原始结果与标准化结果
- 将平台特定错误映射为标准错误

适配器不负责：

- 创建任务
- 推进任务状态
- 管理资源生命周期
- 直接写数据库
- 直接暴露 HTTP API
- 决定租户隔离规则


## 设计原则

- 单一职责：适配器只做平台接入
- 显式契约：输入、输出、错误必须结构化
- 资源注入：适配器只能消费 Core 提供的资源，不自己找资源
- 无副作用落盘：适配器不直接持久化共享内容数据
- 可测试：每个适配器都必须支持独立测试

## v0.7.0 兼容性基线

`v0.7.0` 稳定的是 Core-facing Adapter contract，而不是外部 provider contract。当前主干的最小运行时表面为：

- `adapter_key`
- `supported_capabilities`
- `supported_targets`
- `supported_collection_modes`
- `resource_requirement_declarations`
- `execute(request: AdapterExecutionContext) -> dict`

当前 approved capability metadata 仍只覆盖双参考验证切片：

- public operation：`content_detail_by_url`
- adapter-facing capability family：`content_detail`
- target type：`url`
- collection mode：`hybrid`
- reference adapters：`xhs`、`douyin`
- required resource capabilities：`account`、`proxy`
- success payload：`{"raw": ..., "normalized": ...}`

`content_detail_by_url` 是 Core/public operation id；进入 Adapter 前继续投影为 `content_detail` capability family。Adapter 作者不得把 `content_detail_by_url`、`xsec_token`、`verify_fp`、`ms_token`、browser page state、sign service 或 provider key 写入 `supported_capabilities` / `resource_requirement_declarations`。

## Adapter-Owned Provider Port

`FR-0021` 批准的 provider port 是 adapter-owned 内部执行边界：

```text
Core Runtime
  -> Adapter.execute(AdapterExecutionContext)
      -> Adapter-owned Provider Port
          -> Native Provider
      -> Adapter normalizer
```

该边界只允许 Adapter 把已验证 URL、已解析 target、已消费 resource bundle 后得到的平台 session config 与 legacy transport hooks 交给 native provider。Native provider 返回 raw platform payload 与 platform detail object；normalized result 仍由 Adapter 生成。

该边界明确不提供：

- 外部 provider SDK
- provider plugin registration
- Core provider registry
- provider selector
- provider fallback priority
- provider resource supply model

`provider=` constructor seam 只允许作为仓内测试/本地注入 seam；它不能被声明为第三方 provider 接入能力，也不能替代现有 `sign_transport`、`detail_transport`、`page_transport`、`page_state_transport` 等 legacy transport hooks。

## v1.0 前开放接入目标

`v1.0.0` 前，Adapter SDK 需要把两类接入路径解释清楚：

- Adapter-only：第三方直接实现 Syvert Adapter，承担目标系统语义、输入校验、资源需求、错误映射与 `raw + normalized` 输出责任。
- Adapter + Provider：Adapter 仍是 Syvert 接入入口，provider 只作为 Adapter 内部可替换执行能力，通过兼容性判断后被绑定。

Provider 产品若已经封装目标系统语义，可以选择构建 Adapter；若只提供浏览器、远程执行、CLI、agent 或其他通用执行能力，则应通过 Adapter-bound provider offer 接入。Syvert 不把 provider 直接接入 Core，也不要求某一个 provider 覆盖所有 Adapter capability。

`v1.0.0` 前需要冻结的最小判断模型是：

```text
Adapter capability requirement
  x Provider capability offer
  -> compatibility decision
```

该判断至少需要能表达：

- Adapter 需要的执行能力、资源前提、错误证据、生命周期与观测要求
- Provider 提供的执行能力、资源消费方式、错误 carrier、版本与 evidence 能力
- 不兼容、缺能力、版本不匹配或资源前提不满足时的 fail-closed 原因

`v0.8.0` 的 Provider offer 声明承载面固定为 `ProviderCapabilityOffer`。它可以出现在 Adapter / Provider 包文档、manifest 或 contract-test fixture 中，但不进入 AdapterRegistry discovery、Core routing、TaskRecord 或 resource lifecycle surface。

Adapter 作者需要同时准备两类输入：

- `AdapterCapabilityRequirement`：由 Adapter 声明自己需要什么能力、资源 profile 与 evidence，作为 `FR-0024` requirement-side input。
- `ProviderCapabilityOffer`：由 Adapter-bound provider 声明自己在某个 Adapter-owned provider port 下能提供什么能力、资源 profile 支持、错误映射、版本与 evidence，作为 `FR-0025` offer-side input。

`ProviderCapabilityOffer` 的合法声明必须满足：

- `adapter_binding.binding_scope` 固定为 `adapter_bound`。
- `adapter_binding.provider_port_ref` 必须以当前 `adapter_key:` 为前缀，例如 `xhs:adapter-owned-provider-port`；不得借用其它 Adapter、Core、global、marketplace、registry 或 routing port。
- 当前 approved slice 只允许 `content_detail + content_detail_by_url + url + hybrid`。
- `resource_support.supported_profiles[*].evidence_refs` 必须唯一命中 `FR-0027` approved profile proof，且该 proof 的 `reference_adapters` 覆盖当前 `adapter_key`。
- `error_carrier` 必须要求 Adapter 映射 provider 错误，不新增 Core-facing provider failed envelope。
- `version.contract_version` 固定为 `v0.8.0`，并回指 `FR-0024`、`FR-0027` 与 `FR-0021`。
- `lifecycle.core_discovery_allowed=false`、`lifecycle.invoked_by_adapter_only=true`、`fail_closed=true`。

Requirement-side 示例必须直接消费 `FR-0024` 的 canonical `AdapterCapabilityRequirement`，例如 `tests/runtime/adapter_capability_requirement_fixtures.py::valid_adapter_capability_requirement()`；本文不维护第二套 requirement-side carrier。

Provider-side 最小 manifest / fixture 形态应与 `tests/runtime/provider_capability_offer_fixtures.py::valid_provider_capability_offer()` 对齐：

```python
PROVIDER_CAPABILITY_OFFER = {
    "provider_key": "native_xhs_detail",
    "adapter_binding": {
        "adapter_key": "xhs",
        "binding_scope": "adapter_bound",
        "provider_port_ref": "xhs:adapter-owned-provider-port",
    },
    "capability_offer": {
        "capability": "content_detail",
        "operation": "content_detail_by_url",
        "target_type": "url",
        "collection_mode": "hybrid",
    },
    "resource_support": {
        "supported_profiles": [
            {
                "profile_key": "account_proxy",
                "resource_dependency_mode": "required",
                "required_capabilities": ["account", "proxy"],
                "evidence_refs": [
                    "fr-0027:profile:content-detail-by-url-hybrid:account-proxy"
                ],
            },
            {
                "profile_key": "account",
                "resource_dependency_mode": "required",
                "required_capabilities": ["account"],
                "evidence_refs": [
                    "fr-0027:profile:content-detail-by-url-hybrid:account"
                ],
            },
        ],
        "resource_profile_contract_ref": "FR-0027",
    },
    "error_carrier": {
        "invalid_offer_code": "invalid_provider_offer",
        "provider_unavailable_code": "provider_unavailable",
        "contract_violation_code": "provider_contract_violation",
        "adapter_mapping_required": True,
    },
    "version": {
        "contract_version": "v0.8.0",
        "requirement_contract_ref": "FR-0024",
        "resource_profile_contract_ref": "FR-0027",
        "provider_port_boundary_ref": "FR-0021",
    },
    "evidence": {
        "provider_offer_evidence_refs": [
            "fr-0025:offer-manifest-fixture-validator:content-detail-by-url-hybrid"
        ],
        "resource_profile_evidence_refs": [
            "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
            "fr-0027:profile:content-detail-by-url-hybrid:account",
        ],
        "adapter_binding_evidence_refs": [
            "fr-0021:adapter-provider-port-boundary:adapter-owned-provider-port"
        ],
    },
    "lifecycle": {
        "invoked_by_adapter_only": True,
        "core_discovery_allowed": False,
        "consumes_adapter_execution_context": True,
        "uses_existing_resource_bundle_view": True,
        "adapter_error_mapping_required": True,
    },
    "observability": {
        "offer_id": (
            "xhs:native_xhs_detail:content_detail:"
            "content_detail_by_url:url:hybrid:v0.8.0"
        ),
        "provider_key": "native_xhs_detail",
        "adapter_key": "xhs",
        "capability": "content_detail",
        "operation": "content_detail_by_url",
        "profile_keys": ["account_proxy", "account"],
        "proof_refs": [
            "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
            "fr-0027:profile:content-detail-by-url-hybrid:account",
        ],
        "contract_version": "v0.8.0",
        "validation_outcome_fields": [
            "validation_status",
            "error_code",
            "failure_category",
        ],
    },
    "fail_closed": True,
}
```

Provider offer manifest validator 只回答 offer carrier 是否可信：

- `declared`：offer 合法，只代表 Provider offer declared。
- `invalid`：offer 不可信，必须 fail-closed，并映射为 `runtime_contract + invalid_provider_offer`。

后续 `FR-0026` contract test / decision 入口才允许同时消费 requirement 与 offer，并产出 `compatibility decision`：

- `matched`：provider offer 满足该 Adapter capability requirement，可以进入绑定验证。
- `unmatched`：provider offer 不满足 requirement，必须 fail-closed，并给出缺失能力、版本或资源前提。
- `invalid_contract`：声明本身不可信，必须 fail-closed，不得继续执行 provider。

这些声明只能用于 Adapter-bound compatibility test 与 evidence artifact。Core registry discovery 仍只暴露 Adapter public metadata；TaskRecord、resource lifecycle 与 runtime envelope 不新增 provider key、provider priority 或 provider selector 字段。

该模型不代表：

- 指定 provider 产品获得正式支持
- Core 可以发现、选择或排序 provider
- provider 可以绕过 Adapter 生成 Syvert normalized result
- provider 可以绕过 Core 注入资源包自行获取账号、代理或会话资源
- `declared` offer 已经等同于 `matched`、selected provider、fallback candidate 或真实 provider 产品支持

## v0.8.0 FR-0026 AdapterProviderCompatibilityDecision

`FR-0026` 把 `AdapterCapabilityRequirement x ProviderCapabilityOffer` 的兼容性判断落到 `AdapterProviderCompatibilityDecision`。它只消费 `FR-0024` requirement、`FR-0025` offer 与 `FR-0027` resource profile proof；不定义新的 provider carrier，不改写 resource requirement / offer manifest，也不引入 Core provider discovery 或 routing。

作者侧应按以下顺序理解：

1. Adapter 声明 `AdapterCapabilityRequirement`。
2. Adapter-bound provider 声明 `ProviderCapabilityOffer`，validator 只给出 `declared` / `invalid`。
3. `AdapterProviderCompatibilityDecision` 同时验证两侧 carrier、adapter binding、approved execution slice 与 `FR-0027` proof。
4. Decision 输出 `matched`、`unmatched` 或 `invalid_contract`，并始终 `fail_closed=true`。

### matched

`matched` 只表示合法 requirement 与合法 Adapter-bound offer 在同一 Adapter、同一 approved execution slice 下，至少一个 resource profile canonical tuple 完全一致。

```text
requirement.profile=account_proxy
offer.supported_profile=account_proxy
proof=fr-0027:profile:content-detail-by-url-hybrid:account-proxy
decision_status=matched
```

`matched` 不表示 selected provider、Core routing、priority、score、fallback、marketplace listing、SLA 或真实 provider 产品支持。

### unmatched

`unmatched` 表示 requirement 与 offer 都合法，但 offer 没有满足任何 requirement profile。它必须 fail-closed，不得自动尝试其它 provider。

```text
requirement.profile=account_proxy
offer.supported_profile=account
decision_status=unmatched
error=null
fail_closed=true
```

`unmatched` 不表示 requirement 或 offer 违法，也不触发 provider fallback。

### invalid_contract

`invalid_contract` 表示输入、proof、adapter binding、execution slice、decision context 或 no-leakage 任一 contract violation。常见来源包括：

- requirement 不满足 `FR-0024` 或其 profile 不满足 `FR-0027`。
- offer 不满足 `FR-0025` 或其 supported profile 不满足 `FR-0027`。
- requirement 与 offer 的 `adapter_key`、capability、operation、target type 或 collection mode 不一致。
- 任一 side 越过当前 approved slice：`content_detail + content_detail_by_url + url + hybrid`。
- decision 或 Core-facing surface 出现 provider selector、routing、priority、score、fallback、marketplace、provider lifecycle、resource supply 或 runtime technical 字段。

`invalid_contract` 必须映射为 runtime contract 口径，例如：

```text
decision_status=invalid_contract
error.failure_category=runtime_contract
error.error_code=invalid_requirement_contract | invalid_provider_offer_contract | invalid_compatibility_contract | provider_leakage_detected
fail_closed=true
```

### No-leakage

Provider identity 只允许留在 Adapter-bound decision evidence 中，用于审查当前 offer 来源。以下 Core-facing surface 不得携带 provider 信息：

- Core projection / routing surface
- AdapterRegistry discovery
- TaskRecord
- resource lifecycle snapshot / bundle
- runtime failed envelope category

`#325` 的 no-leakage guard 已覆盖 provider identity、provider metadata、decision carrier、selector / routing / fallback / priority、marketplace / product support、resource lifecycle / supply、runtime technical 字段与 provider-specific failure value。文档证据见 `docs/exec-plans/artifacts/CHORE-0326-fr-0026-compatibility-decision-evidence.md`。

### 迁移提示

从 `ProviderCapabilityOffer` 迁移到 compatibility decision 时，不要把 `declared` 直接写成 `matched`。`declared` 只说明 offer carrier 合法；是否满足某个 Adapter requirement，必须交给 `AdapterProviderCompatibilityDecision` 判定。

真实 provider 样本、provider 产品支持、SLA、marketplace 文案与 runtime 技术细节不属于 `v0.8.0` 的 SDK 承诺范围，留到后续版本以独立 Work Item 验证。


## v0.8.0 Third-party Adapter Contract Entry

`FR-0023` 与 `#310` 已把第三方 Adapter 的 Adapter-only contract test entry 落到 `tests/runtime/contract_harness/third_party_entry.py`，主要入口是 `run_third_party_adapter_contract_test()`、`validate_third_party_adapter_manifest()` 与 `validate_third_party_adapter_fixtures()`，可复用样例放在 `tests/runtime/contract_harness/third_party_fixtures.py`。第三方作者不需要修改 Core；需要提交一个 Adapter manifest、一组 deterministic fixtures，并让 Adapter 对象的 public metadata 与 manifest 完全一致。

当前 contract entry 只验证 Adapter-only 的 `content_detail_by_url -> content_detail` slice：

- manifest `adapter_key` 必须是真实第三方 Adapter identity，例如 `community_detail`；不得使用 `xhs`、`douyin`、provider 产品名、账号、环境、租户或 routing strategy。
- manifest 与 Adapter public metadata 必须同时声明 `sdk_contract_id`、`supported_capabilities`、`supported_targets`、`supported_collection_modes`、`resource_requirement_declarations`、`resource_proof_admission_refs`、`resource_proof_admissions`、`result_contract`、`error_mapping`、`fixture_refs` 与 `contract_test_profile`。
- `supported_capabilities` 当前只允许 `content_detail`；`supported_targets` 当前只允许 `url`；`supported_collection_modes` 当前只允许 `hybrid`。
- success payload 必须返回 mapping，并只把 Adapter 业务结果放在 `raw` 与 `normalized` 内；不得覆盖 runtime envelope 字段，例如 `task_id`、`adapter_key`、`capability`、`status` 或 `error`。
- error mapping 必须把平台错误映射成 runtime 会保留的 `invalid_input` 或 `platform` 分类，并绑定 fixture 中的 `source_error`。
- Adapter public metadata、manifest、fixture nested carrier 与 result contract 均不得携带 provider、selector、fallback、priority、compatibility decision 或 marketplace 字段。

最小 manifest 形状如下；字段名与当前 contract fixture 保持一致：

```python
from tests.runtime.contract_harness.third_party_fixtures import (
    THIRD_PARTY_ACCOUNT_ADMISSION_REF,
    THIRD_PARTY_ACCOUNT_PROXY_ADMISSION_REF,
)

THIRD_PARTY_ADAPTER_MANIFEST = {
    "adapter_key": "community_detail",
    "sdk_contract_id": "syvert-adapter-runtime-v0.8.0",
    "supported_capabilities": ("content_detail",),
    "supported_targets": ("url",),
    "supported_collection_modes": ("hybrid",),
    "resource_requirement_declarations": (
        {
            "adapter_key": "community_detail",
            "capability": "content_detail",
            "resource_requirement_profiles": (
                {
                    "profile_key": "account_proxy",
                    "resource_dependency_mode": "required",
                    "required_capabilities": ("account", "proxy"),
                    "evidence_refs": ("fr-0027:profile:content-detail-by-url-hybrid:account-proxy",),
                },
                {
                    "profile_key": "account",
                    "resource_dependency_mode": "required",
                    "required_capabilities": ("account",),
                    "evidence_refs": ("fr-0027:profile:content-detail-by-url-hybrid:account",),
                },
            ),
        },
    ),
    "resource_proof_admission_refs": (
        THIRD_PARTY_ACCOUNT_PROXY_ADMISSION_REF,
        THIRD_PARTY_ACCOUNT_ADMISSION_REF,
    ),
    "resource_proof_admissions": (...,),
    "result_contract": {
        "success_payload_fields": ("raw", "normalized"),
        "normalized_owner": "adapter",
    },
    "error_mapping": {
        "content_not_found": {
            "category": "platform",
            "code": "content_not_found",
            "message": "content is unavailable or deleted",
        },
    },
    "fixture_refs": (
        "third-party-content-detail-success",
        "third-party-content-detail-error-mapping",
    ),
    "contract_test_profile": "adapter_only_content_detail_v0_8",
}
```

`resource_proof_admissions` 是 `FR-0023` 为真实第三方 `adapter_key` 提供的 manifest-owned proof bridge。它不改写 `FR-0027` approved shared profile proof；它只证明当前第三方 Adapter 在同一 execution slice 下，可以用当前 manifest、contract profile 与 fixtures 覆盖 `FR-0027` 已批准的 profile tuple。

每条 admission 必须满足：

- `admission_ref` 必须被 manifest `resource_proof_admission_refs` 唯一引用。
- SDK 文档不重新定义 admission ref 字符串命名；作者应使用当前 manifest-owned admission entry 的稳定 `admission_ref`，并保持它与 fixture / contract entry 常量一致。
- `adapter_key` 必须等于 manifest、resource declaration 与 fixture `manifest_ref`。
- `base_profile_ref` 必须指向当前 `FR-0027` approved shared profile proof。
- `capability`、`execution_path`、`resource_dependency_mode` 与 `required_capabilities` 必须和 manifest / declaration / fixture 完全一致。
- `admission_evidence_refs` 必须至少覆盖当前 manifest、当前 contract profile、一个 success fixture 与一个 error_mapping fixture，格式分别为 `fr-0023:manifest:{adapter_key}:{contract_test_profile}`、`fr-0023:contract-profile:{adapter_key}:{contract_test_profile}` 与 `fr-0023:fixture:{adapter_key}:{fixture_id}`。
- `decision` 当前固定为 `admit_third_party_profile_for_contract_test_v0_8_0`。

最小 fixture 组合必须同时覆盖 success 与 error_mapping，并且每个声明的 resource profile 都必须被至少一个 fixture 实际执行覆盖：

```python
THIRD_PARTY_ADAPTER_FIXTURES = (
    {
        "fixture_id": "third-party-content-detail-success",
        "manifest_ref": "community_detail",
        "case_type": "success",
        "input": {
            "operation": "content_detail_by_url",
            "capability": "content_detail",
            "target_type": "url",
            "target_value": "https://contract-host/third-party/success",
            "collection_mode": "hybrid",
            "resource_profile_key": "account_proxy",
        },
        "expected": {
            "status": "success",
            "required_payload_fields": ("raw", "normalized"),
        },
    },
    {
        "fixture_id": "third-party-content-detail-error-mapping",
        "manifest_ref": "community_detail",
        "case_type": "error_mapping",
        "input": {
            "operation": "content_detail_by_url",
            "capability": "content_detail",
            "target_type": "url",
            "target_value": "https://contract-host/third-party/content-not-found",
            "collection_mode": "hybrid",
            "resource_profile_key": "account",
        },
        "expected": {
            "status": "failed",
            "error": {
                "source_error": "content_not_found",
                "category": "platform",
                "code": "content_not_found",
            },
        },
    },
)
```

作者侧验证顺序建议固定为：

1. 先让 Adapter object 的 public metadata 与 manifest 完全对齐。
2. 用 deterministic fixtures 覆盖 success payload、error mapping 与每个 resource profile。
3. 运行 third-party contract entry，确认 manifest shape、public metadata、resource declarations、resource proof admissions、fixture coverage 与 `execute()` 行为都 fail-closed。
4. 再接入真实平台回归；真实平台回归不得替代 deterministic contract fixtures。


## 最小能力面

一个适配器最少必须声明：

- `adapter_key`
- `supported_capabilities`
- `supported_targets`
- `supported_collection_modes`
- `resource_requirement_declarations`

其中：

- `supported_capabilities` 表示它支持哪些任务类型
- `supported_targets` 表示它支持哪些输入目标
- `supported_collection_modes` 表示它支持哪些采集模式
- `resource_requirement_declarations` 表示 Core 进入该 capability 前必须注入哪些共享资源能力


## 核心接口

以下接口是建议的最小 SDK 形态。

```python
from __future__ import annotations

from typing import Any, Protocol

from syvert.runtime import AdapterExecutionContext


class PlatformAdapter(Protocol):
    adapter_key: str
    supported_capabilities: frozenset[str]
    supported_targets: frozenset[str]
    supported_collection_modes: frozenset[str]
    resource_requirement_declarations: tuple[object, ...]

    def execute(self, request: AdapterExecutionContext) -> dict[str, Any]:
        ...
```


## 输入契约

Core 调用适配器时，只应传入一个 `AdapterExecutionContext`。

其中：

- `request` 描述 adapter-facing capability、target type、target value 与 collection mode
- `resource_bundle` 描述 Core 已 acquire 并注入给 Adapter 的资源包
- `task_id`、resource trace 与 failure envelope 由 Core 继续拥有

适配器不得自行推断：

- 当前租户是谁
- 当前任务是谁创建的
- 当前该用哪个资源池

这些信息必须由 Core 显式提供。


## 输出契约

适配器必须返回 `dict` success payload。

输出应至少包含：

- `raw`
- `normalized`

### raw

保存平台原始结果，用于：

- 审计
- 调试
- 回放
- 二次解析

### normalized

返回当前 capability family 的标准化结果。

在 `v0.7.0` 当前 approved slice 中，`normalized` 仍是 `content_detail` 结果对象，至少覆盖 `platform`、`content_id`、`content_type`、`canonical_url`、`title`、`body_text`、`published_at`、`author`、`stats` 与 `media`。


## 错误契约

适配器不能随意抛出底层异常到 Core。

所有平台错误都必须映射成 `PlatformAdapterError`。

错误最少需要提供：

- `code`
- `message`
- `category`
- `details`

这样 Core 才能统一处理：

- 状态推进
- 重试策略
- 失败分类
- 资源状态回写


## 资源契约

资源由 Core 提供，适配器只消费。

当前 `v0.7.0` approved resource capabilities 只有：

- account
- proxy

`cookies`、`user_agent`、`headers`、`xsec_token`、`verify_fp`、`ms_token`、browser page state 与 sign request 参数只能作为 Adapter 从 account material 或站点解析结果中抽取出的内部执行材料。它们不得进入：

- `resource_requirement_declarations`
- Adapter registry discovery
- Core routing metadata
- TaskRecord public envelope
- resource lifecycle state

适配器不可以：

- 自己从数据库查账号
- 自己决定租户隔离
- 自己修改资源所有权
- 自己写资源状态

如果平台执行中发现资源失败，适配器应通过标准错误或诊断信息告诉 Core，由 Core 回写资源状态。


## 生命周期

一个标准适配器调用流程应为：

```text
Core creates task
    -> Core resolves target and policy
    -> Core acquires resource bundle
    -> Core builds AdapterExecutionContext
    -> Adapter.execute()
    -> Adapter returns {"raw": ..., "normalized": ...} or PlatformAdapterError
    -> Core updates task state
    -> Core persists results
    -> Core releases resources
```

适配器只处在中间执行环节。


## 能力声明

适配器必须显式声明自己支持什么。

例如：

```python
from syvert.registry import baseline_required_resource_requirement_declaration


class ExampleAdapter(PlatformAdapter):
    adapter_key = "example"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = (
        baseline_required_resource_requirement_declaration(
            adapter_key=adapter_key,
            capability="content_detail",
        ),
    )
```

Core 可以基于这些声明做：

- 路由
- 参数校验
- 兼容性检查
- 能力发现


## 适配器注册

Core 应支持适配器注册机制。

建议最小接口：

```python
class AdapterRegistry:
    @classmethod
    def from_mapping(cls, adapters: Mapping[str, object]) -> "AdapterRegistry": ...
    def lookup(self, adapter_key: str) -> AdapterDeclaration | None: ...
    def discover_capabilities(self, adapter_key: str) -> frozenset[str] | None: ...
    def discover_targets(self, adapter_key: str) -> frozenset[str] | None: ...
    def discover_collection_modes(self, adapter_key: str) -> frozenset[str] | None: ...
    def discover_resource_requirements(
        self,
        adapter_key: str,
    ) -> tuple[AdapterResourceRequirementDeclaration, ...] | None: ...
```

原则：

- `adapter_key` 是 Core-facing adapter lookup identity
- registry discovery 只返回 Adapter public metadata
- registry 不暴露 provider key、provider priority、native provider 或 provider resource requirement
- 多 adapter / 多 capability 扩展必须先获得新的 formal spec 批准
- provider 兼容性判断不得改写 registry discovery 为 provider selector 或 provider 产品目录


## 版本兼容

Adapter SDK 必须有清晰版本边界。

`v0.7.0` 的兼容性声明：

- Adapter SDK contract id：`syvert-adapter-sdk/v0.7`
- Core runtime compatibility range：`>=0.7,<1.0`
- `#269` native provider 拆分不改变 Core / Adapter runtime contract。
- Adapter public metadata、resource requirement declaration、`execute()` 输入输出、`raw + normalized` success payload 与错误分类保持兼容。
- 小红书、抖音当前 only-approved capability baseline 仍是 `content_detail_by_url -> content_detail`。
- registry / TaskRecord / resource lifecycle 不暴露 provider 字段。
- 任何外部 provider 接入、新业务能力、provider selector 或新资源模型都必须通过后续独立 FR。

第三方 adapter 的最小兼容性声明建议写在 adapter 包文档或 manifest 中；`v0.7.0` 不要求 AdapterRegistry 读取这些字段：

```python
ADAPTER_COMPATIBILITY = {
    "adapter_sdk_contract": "syvert-adapter-sdk/v0.7",
    "core_runtime": ">=0.7,<1.0",
    "adapter_surface": "adapter_key+execute+resource_requirement_declarations",
    "capability_baseline": "content_detail_by_url->content_detail",
    "provider_port": "internal-only",
}
```

通用建议：

- Core 主版本变化可以打破 SDK 契约
- Core 次版本变化应保持 SDK 向后兼容
- 适配器应声明自己兼容的 SDK 版本
- provider offer 只能声明可服务的 Adapter capability 范围，不能声明“支持 Syvert 全部能力”


## 测试要求

每个适配器最少应具备以下测试：

1. capability 声明测试
2. 输入校验测试
3. 成功路径测试
4. 平台错误映射测试
5. 认证资源缺失测试
6. 解析失败测试

可选测试：

- 分页测试
- 限流测试
- 降级测试
- 资源失败测试
- Adapter / Provider compatibility decision 测试
- 真实 provider 验证样本的 evidence 回归测试


## 实现约束

为防止适配器侵入 Core，建议强制以下约束：

- 不直接访问 Core 数据库
- 不直接修改任务状态
- 不直接修改资源状态
- 不直接依赖 Entry Layer
- 不直接返回平台私有异常
- 不把平台专有字段扩散到共享模型中


## v0.7.0 到 v0.8.0 最小迁移说明

第三方 adapter 从旧草案迁移到当前 `v0.7.0` Core-facing 表面时，至少需要完成：

1. 将 `adapter_id` / `platform_name` 收敛为单一 `adapter_key`。
2. 将 `collect(request, context)` 改为 `execute(request: AdapterExecutionContext) -> dict`。
3. 将 success result 改为 `{"raw": ..., "normalized": ...}`，不要返回旧 `AdapterResult` / `NormalizedEntity` 列表。
4. 将 capability metadata 收敛到已批准 baseline：`supported_capabilities=frozenset({"content_detail"})`、`supported_targets=frozenset({"url"})`、`supported_collection_modes=frozenset({"hybrid"})`。
5. 新增或确认 `resource_requirement_declarations` 只声明 `account` 与 `proxy`，不得写入 cookie、user-agent、headers、provider key、browser provider、sign service 或 fallback priority。
6. 如果 adapter 内部拆出 provider port，只能作为 adapter-owned 内部边界；Core / registry / TaskRecord / resource lifecycle 不得发现或选择 provider。
7. 保留 legacy transport hooks 的测试注入能力；新增 provider test seam 时必须标注为 internal test seam，不得作为外部 provider 接入文档发布。

进入 `v0.8.0` 的 Adapter-only contract entry 时，还需要补齐：

1. 把 `sdk_contract_id` 升级为 `syvert-adapter-runtime-v0.8.0`，并声明 `contract_test_profile="adapter_only_content_detail_v0_8"`。
2. 新增 manifest-owned `resource_proof_admission_refs` 与 `resource_proof_admissions`；第三方真实 `adapter_key` 不应伪装为 `xhs` 或 `douyin` 来复用 reference adapter proof。
3. 为每个 `resource_requirement_profiles[*]` 提供 fixture coverage，并让 admission evidence refs 覆盖 manifest、contract profile、success fixture 与 error_mapping fixture。
4. 将 success fixture 绑定真实 target input，确保 `normalized.canonical_url` 或等价字段来自 fixture input，而不是静态样本。
5. 将 error_mapping fixture 的 `expected.error.source_error` 与 manifest `error_mapping` 绑定，并在 Adapter 抛出的 `PlatformAdapterError.details.source_error` 中保留同一值。
6. 删除 manifest、public metadata、fixture expected/result contract 中的 provider-facing 字段；Adapter-only 文档不得出现 provider selector、fallback、priority、offer、compatibility decision 或 marketplace。

参考适配器升级时保持相反边界：`xhs` 与 `douyin` 继续作为 reference adapter proof 的 approved sample，不能被第三方 Adapter manifest 借用为真实 identity。参考适配器可以继续拥有 adapter-owned provider port / native provider 内部实现，但这些内部 provider 细节不得进入 Adapter public metadata、registry discovery、TaskRecord、resource lifecycle、第三方 manifest 或 contract test profile。


## 推荐开发流程

接入一个新平台的建议路径：

1. 定义 capability 与 target 支持范围，并确认是否属于当前 approved slice。
2. 定义 manifest、resource requirement profiles、resource proof admissions 与 deterministic fixtures。
3. 定义平台原始结果到当前 `normalized` shape 的映射。
4. 实现 `execute()`，只返回 `{"raw": ..., "normalized": ...}`。
5. 实现错误映射，并把平台 source error 映射到受批准的 runtime category / code。
6. 运行 third-party contract entry，先通过 deterministic Adapter-only contract。
7. 注册到 Core 并用 API/CLI 跑通任务。
8. 补充真实平台回归；真实平台回归只作为下游 evidence，不替代 contract entry。

如果接入方已有 provider 产品：

1. 若产品已具备目标系统语义，优先包装成 Syvert Adapter。
2. 若产品只提供通用执行能力，先声明 Provider capability offer，再绑定到具体 Adapter capability。
3. 任何 Adapter + Provider 绑定都必须产出 compatibility decision 与 evidence。
4. 不得把 provider 产品名写成全局能力承诺；只能声明它通过验证的 Adapter capability 范围。


## 一句话总结

Adapter SDK 的目标是让平台接入成为一项有边界的工程工作：

适配器只负责平台，
Core 负责系统。
