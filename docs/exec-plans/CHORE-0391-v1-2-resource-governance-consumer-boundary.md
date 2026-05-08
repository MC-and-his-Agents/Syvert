# CHORE-0391-v1-2-resource-governance-consumer-boundary 执行计划

## 关联信息

- item_key：`CHORE-0391-v1-2-resource-governance-consumer-boundary`
- Issue：`#391`
- item_type：`CHORE`
- release：`v1.2.0`
- sprint：`2026-S24`
- Parent Phase：`#380`
- Parent FR：`#387`
- 关联 spec：`docs/specs/FR-0387-resource-governance-admission-and-health-contract/`
- 上游依赖：`#390` runtime carrier 已由 PR `#393` 合入并关闭
- 关联 PR：待创建

## 目标

- 在 runtime carrier 合入后，补齐 consumer boundary guard，确保 credential/session 私有字段与 health SLA 语义不得进入 AdapterRequirement、ProviderOffer、CompatibilityDecision、registry discovery 或 TaskRecord public envelope。
- 保持现有 `account` / `proxy` capability、`content_detail_by_url` baseline、provider offer/resource profile 匹配结果不变。

## 范围

- 本次纳入：
  - Adapter capability requirement 禁止 `cookies`、`cookie`、`token`、`xsec_token`、`verify_fp`、`ms_token`、`headers`、`authorization`、`session`、`credential_freshness`、`session_health`、`health_sla` 等字段或 public observability 值。
  - Provider capability offer 禁止同类 credential/session/private health 字段或 public observability 值。
  - Adapter / Provider compatibility decision 对 decision input / context 中的 credential/session/private health metadata fail-closed，不返回 `matched`。
  - Core surface no-leakage guard 覆盖 registry discovery、TaskRecord public envelope、runtime envelope 与 generic core surface 上的 credential/session/private health 字段和值；resource lifecycle material 仍可作为 private resource truth 存在。
- 本次不纳入：
  - #390 runtime carrier 修改。
  - fake/reference/real evidence artifact。
  - release closeout、GitHub Release 或 tag。

## 当前停点

- 已实现 consumer boundary guard 与测试。
- 待完整回归、commit、PR、review、merge closeout。

## 下一步动作

- 跑 #391 范围 consumer 回归与 governance gate。
- 创建 PR，完成 review/merge 后关闭 #391。

## 当前 checkpoint 推进的 release 目标

- `v1.2.0 Resource Governance Foundation` consumer boundary。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：承接 #390 runtime carrier 后的 consumer/public metadata 边界收口。
- 阻塞：#392 evidence 必须等本事项合入后执行。

## 已验证项

- `python3 -m unittest tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard`：99 tests passed。
- `python3 -m unittest tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard tests.runtime.test_platform_leakage tests.runtime.test_operation_taxonomy_consumers tests.runtime.test_reference_adapter_capability_requirement_baseline tests.runtime.test_resource_capability_matcher tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_resource_health`：303 tests passed。
- `python3 -m py_compile syvert/adapter_capability_requirement.py syvert/provider_capability_offer.py syvert/adapter_provider_compatibility_decision.py syvert/provider_no_leakage_guard.py tests/runtime/test_adapter_capability_requirement.py tests/runtime/test_provider_capability_offer.py tests/runtime/test_adapter_provider_compatibility_decision.py tests/runtime/test_provider_no_leakage_guard.py`：通过。
- `python3 scripts/spec_guard.py --mode ci --all`：通过。
- `python3 scripts/docs_guard.py --mode ci`：通过。
- `python3 scripts/workflow_guard.py --mode ci`：通过。

## Review 处理记录

- 暂无。

## 未决风险

- credential/session private health 词表被错误用于 resource lifecycle private material，造成 account material truth 无法表达受管凭据。当前 guard 仅允许 resource lifecycle material 承载 private material，public metadata 仍 fail-closed。
- provider no-leakage 与 credential/session no-leakage 共用 guard 时，必须保持错误证据脱敏，不复制私有字段值。
- compatibility decision 必须先 fail-closed，再进入 matched profile 输出，避免 private health metadata 影响匹配结果。

## 回滚方式

- 使用独立 revert PR 回滚 consumer boundary 词表、tests 与本 exec-plan；#390 runtime carrier 可保留。

## 最近一次 checkpoint 对应的 head SHA

- `80708bda2196cb691089222f8b59d74b3f1132d0`
- Current HEAD may include a metadata-only checkpoint follow-up that records this verified implementation checkpoint.
