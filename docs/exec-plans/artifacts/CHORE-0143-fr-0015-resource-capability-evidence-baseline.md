# CHORE-0143 FR-0015 Resource Capability Evidence Baseline

本文件把 `#197 / CHORE-0143` 已落地的 `FR-0015` machine-readable evidence baseline 摘出来，供 code review、closeout 与后续 `#195/#196` 直接消费。

本文件不改写 [`docs/specs/FR-0015-dual-reference-resource-capability-evidence/`](../../specs/FR-0015-dual-reference-resource-capability-evidence/) 的 requirement；canonical requirement 仍以 formal spec 为准，canonical implementation carrier 以 `syvert/resource_capability_evidence.py` 为准。

## evidence ref registry

| evidence_ref | source_file | source_symbol | summary |
| --- | --- | --- | --- |
| `fr-0015:runtime:content-detail-by-url-hybrid:requested-slots` | `syvert/runtime.py` | `RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE` | 共享 Core 路径在 `content_detail_by_url + hybrid` 上统一请求 `account`、`proxy` 两个受管资源 slot |
| `fr-0015:xhs:content-detail:url:hybrid:account-material` | `syvert/adapters/xhs.py` | `build_session_config_from_context` | `xhs` adapter 在共享路径上从 `resource_bundle.account.material` 消费 `cookies`、`user_agent`、`sign_base_url`、`timeout_seconds` |
| `fr-0015:douyin:content-detail:url:hybrid:account-material` | `syvert/adapters/douyin.py` | `build_session_config_from_context` | `douyin` adapter 在共享路径上从 `resource_bundle.account.material` 消费 `cookies`、`user_agent`、`verify_fp`、`ms_token`、`webid`、`sign_base_url`、`timeout_seconds` |
| `fr-0015:regression:xhs:managed-proxy-seed` | `syvert/real_adapter_regression.py` | `seed_reference_regression_resources` | `xhs` 真实适配器回归基线在共享路径上同时种入 `account` 与 `proxy` |
| `fr-0015:regression:douyin:managed-proxy-seed` | `syvert/real_adapter_regression.py` | `seed_reference_regression_resources` | `douyin` 真实适配器回归基线在共享路径上同时种入 `account` 与 `proxy` |

## canonical evidence records

| adapter_key | capability | execution_path | resource_signals | candidate_abstract_capability | shared_status | decision | evidence_refs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `xhs` | `content_detail` | `operation=content_detail_by_url, target_type=url, collection_mode=hybrid` | `runtime_requested_slots=account,proxy`; `adapter_consumes_account_material=cookies,user_agent,sign_base_url,timeout_seconds` | `account` | `shared` | `approve_for_v0_5_0` | `fr-0015:runtime:content-detail-by-url-hybrid:requested-slots`; `fr-0015:xhs:content-detail:url:hybrid:account-material` |
| `douyin` | `content_detail` | `operation=content_detail_by_url, target_type=url, collection_mode=hybrid` | `runtime_requested_slots=account,proxy`; `adapter_consumes_account_material=cookies,user_agent,verify_fp,ms_token,webid,sign_base_url,timeout_seconds` | `account` | `shared` | `approve_for_v0_5_0` | `fr-0015:runtime:content-detail-by-url-hybrid:requested-slots`; `fr-0015:douyin:content-detail:url:hybrid:account-material` |
| `xhs` | `content_detail` | `operation=content_detail_by_url, target_type=url, collection_mode=hybrid` | `runtime_requested_slots=account,proxy`; `regression_seeded_resources=account,proxy` | `proxy` | `shared` | `approve_for_v0_5_0` | `fr-0015:runtime:content-detail-by-url-hybrid:requested-slots`; `fr-0015:regression:xhs:managed-proxy-seed` |
| `douyin` | `content_detail` | `operation=content_detail_by_url, target_type=url, collection_mode=hybrid` | `runtime_requested_slots=account,proxy`; `regression_seeded_resources=account,proxy` | `proxy` | `shared` | `approve_for_v0_5_0` | `fr-0015:runtime:content-detail-by-url-hybrid:requested-slots`; `fr-0015:regression:douyin:managed-proxy-seed` |
| `douyin` | `content_detail` | `operation=content_detail_by_url, target_type=url, collection_mode=hybrid` | `adapter_private_account_field=verify_fp` | `verify_fp` | `adapter_only` | `keep_adapter_local` | `fr-0015:douyin:content-detail:url:hybrid:account-material` |
| `douyin` | `content_detail` | `operation=content_detail_by_url, target_type=url, collection_mode=hybrid` | `adapter_private_account_field=ms_token` | `ms_token` | `adapter_only` | `keep_adapter_local` | `fr-0015:douyin:content-detail:url:hybrid:account-material` |
| `douyin` | `content_detail` | `operation=content_detail_by_url, target_type=url, collection_mode=hybrid` | `adapter_private_account_field=webid` | `webid` | `adapter_only` | `keep_adapter_local` | `fr-0015:douyin:content-detail:url:hybrid:account-material` |
| `xhs` | `content_detail` | `operation=content_detail_by_url, target_type=url, collection_mode=hybrid` | `technical_binding_field=sign_base_url` | `sign_base_url` | `rejected` | `reject_for_v0_5_0` | `fr-0015:xhs:content-detail:url:hybrid:account-material` |
| `douyin` | `content_detail` | `operation=content_detail_by_url, target_type=url, collection_mode=hybrid` | `technical_binding_field=sign_base_url` | `sign_base_url` | `rejected` | `reject_for_v0_5_0` | `fr-0015:douyin:content-detail:url:hybrid:account-material` |
| `xhs` | `content_detail` | `operation=content_detail_by_url, target_type=url, collection_mode=hybrid` | `technical_binding_candidate=browser_state` | `browser_state` | `rejected` | `reject_for_v0_5_0` | `fr-0015:xhs:content-detail:url:hybrid:account-material` |
| `douyin` | `content_detail` | `operation=content_detail_by_url, target_type=url, collection_mode=hybrid` | `technical_binding_candidate=browser_state` | `browser_state` | `rejected` | `reject_for_v0_5_0` | `fr-0015:douyin:content-detail:url:hybrid:account-material` |

## approved vocabulary

| capability_id | status | approval_basis_evidence_refs |
| --- | --- | --- |
| `account` | `approved` | `fr-0015:runtime:content-detail-by-url-hybrid:requested-slots`; `fr-0015:xhs:content-detail:url:hybrid:account-material`; `fr-0015:douyin:content-detail:url:hybrid:account-material` |
| `proxy` | `approved` | `fr-0015:runtime:content-detail-by-url-hybrid:requested-slots`; `fr-0015:regression:xhs:managed-proxy-seed`; `fr-0015:regression:douyin:managed-proxy-seed` |

## downstream consumption rule

- `#195 / FR-0013` 只能从 `syvert.resource_capability_evidence.approved_resource_capability_ids()` 读取批准能力名，并从 frozen registry / approved vocabulary 条目读取 `evidence_refs`。
- `#196 / FR-0014` 只能消费同一份 approved capability baseline，不得自行复制 `account`、`proxy` 或重写 evidence ref 字符串。
- `adapter_only` / `rejected` 候选只允许作为 fail-closed 反例保留在 registry 中，不得被下游实现提升为 matcher / declaration 的合法能力名。
