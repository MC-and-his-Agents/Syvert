# CHORE-0423 v1.5 media asset fetch runtime carrier 执行计划

## 关联信息

- item_key：`CHORE-0423-v1-5-media-asset-fetch-runtime`
- Issue：`#423`
- item_type：`CHORE`
- release：`v1.5.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#405`
- 关联 spec：`docs/specs/FR-0405-creator-profile-media-asset-read-contract/spec.md`
- 关联 decision：
- 关联 PR：`#439`（`https://github.com/MC-and-his-Agents/Syvert/pull/439`）
- 状态：`active`
- active 收口事项：`CHORE-0423-v1-5-media-asset-fetch-runtime`

## 目标

- 实现 `media_asset_fetch_by_ref` runtime carrier。
- 将 `media_asset_fetch + media_ref + single + direct` 升级为 stable runtime delivery。
- 覆盖 media ref、content type、fetch policy/outcome、metadata-only、source-ref-preserved、downloaded-bytes metadata、source ref lineage、raw payload ref、normalized media descriptor 与 no-storage boundary 的 fail-closed 行为。
- 保持 `content_detail_by_url`、`content_search_by_keyword`、`content_list_by_creator` 与 `comment_collection` 回归路径不变。

## 范围

- 本次纳入：
  - `syvert/operation_taxonomy.py`
  - `syvert/runtime.py`
  - `syvert/task_record.py`
  - `syvert/registry.py`
  - `tests/runtime/test_operation_taxonomy.py`
  - `tests/runtime/test_runtime.py`
  - `tests/runtime/test_task_record.py`
  - 本 exec-plan
- 本次不纳入：
  - `creator_profile_by_id` runtime carrier（#422）。
  - TaskRecord/result query/runtime admission 与 Adapter/Provider compatibility consumer migration（#424）。
  - sanitized fake/reference evidence matrix（#425）。
  - `#405` closeout、release tag、GitHub Release 或 Phase `#381` closeout（#426）。
  - raw payload files、local media storage、private media fields、source names 或 local paths。

## 当前停点

- `#404/#420` 已关闭，`v1.4.0` 已发布。
- `#404` conflict-risk clearance locator：PR `#438`。
- Canonical spec input：`#421` / PR `#428`。
- Worktree key：`issue-423-405-v1-5-0-media-asset-fetch-runtime`
- Branch：`issue-423-405-v1-5-0-media-asset-fetch-runtime`
- 当前实现已落地并提交到 PR `#439`。
- PR guardian 首轮 findings 已处理：fetch policy 请求对象、`result_status`/`fetch_outcome` 分离、`source_ref_lineage`、downloaded-bytes public metadata、permission/auth failure classifications 均已按 FR-0405 对齐。
- PR guardian 第二轮 findings 已处理：结果绑定原始请求 fetch policy、stable media content type 收窄为 `image`/`video`、media metadata 改为公共白名单字段。
- PR guardian 第三轮 findings 已处理：`unsupported_content_type` failed carrier 可表达非 stable shape、`max_bytes`/`download_required` policy boundary 已执行、complete success 必须包含 `raw_payload_ref`。
- PR guardian 第四轮 findings 已处理：默认 fetch policy 参与结果校验、`download_required` 不接受 metadata/source-ref 降级、非法 `allowed_content_types` fail-closed、failed/unavailable carrier 必须显式 `media: null`。
- PR guardian 第五轮 findings 已处理：nullable media carrier 字段必须显式存在、`media_asset_fetch` resource slot resolution 尊重 V1/V2 account-only declarations。
- PR guardian 第六轮 findings 已处理：`provider_or_network_blocked` 强制 `raw_payload_ref=null` 与 blocked-path alias，source refs/lineage/provider_path 增加值级脱敏校验。
- PR guardian 第七轮 findings 已处理：`fetch_policy` 严格公共字段白名单、公共 content type 被请求 policy 排除时必须 `fetch_policy_denied`、非下载 outcome 不得记录下载字节数。
- PR guardian 第八轮 findings 已处理：request/target/lineage media ref 均做值级脱敏校验，`no_storage` 改为严格公共白名单载体。
- PR guardian 第九轮 findings 已处理：`MediaAssetTarget` 公共字段改为 formal `media_ref`，`download_required` 被 policy 阻止时 failed carrier 必须 `fetch_policy_denied`。
- PR guardian 第十轮 findings 已处理：`target_not_found` 纳入 media unavailable vocabulary，非 stable media shape 必须 `unsupported_content_type`，Issue `#423` integration metadata 已对齐 PR integration_check。
- PR guardian 第十一轮 findings 已处理：按 FR-0405 移除 media `target_not_found`，`source_trace`/`audit` 改为公共字段白名单并增加下载 audit proof 校验，Issue/PR `merge_gate` 已对齐 `integration_check_required`。
- PR guardian 第十二轮 findings 已处理：`target`、`media`、`source_ref_lineage` 嵌套对象均改为公共字段白名单并补私有字段回归。
- PR guardian 第十三轮后执行系统性合同核对：按 FR-0405 重新核对 public field whitelist、`MediaAssetTarget.media_ref`、result status/error mapping、fetch policy decision matrix、raw/normalized/audit split、source trace/lineage/no-storage 脱敏六类不变量；runtime 与 TaskRecord 均已按同一不变量收敛。
- 系统性核对补正：TaskRecord `unknown + parse_failed + raw_payload_ref` 回放顺序与 runtime 对齐，并增加 durable round-trip 回归，防止合法 parse_failed carrier 在持久化/回放路径崩溃。

## FR-0405 media carrier 不变量核对

- public carrier 字段必须白名单：`target`、`fetch_policy`、`media`、`media.metadata`、`media.source_ref_lineage`、`source_trace`、`audit`、`no_storage` 不接受未定义扩展字段。
- target 使用 formal `MediaAssetTarget.media_ref`；request `media_ref`、target `media_ref` 与 lineage `input_ref` 均必须是脱敏 opaque ref。
- `result_status` 与 `error_classification` 使用 media-only 映射：success 为 `complete/null`，`media_unavailable`/`permission_denied` 为 `unavailable`，media failed 分类不接受 creator-only `target_not_found/profile_unavailable`。
- fetch policy 按 spec matrix 执行：先 content type projection，再 `allowed_content_types`，再 source-ref preservation / download policy；`download_required` 不允许降级为 non-download success。
- raw/normalized/audit split 固定：complete 必须有 raw ref；`provider_or_network_blocked` 必须 raw null；download facts 只进入 public metadata 与 audit proof，非下载 outcome 不携带 audit/download bytes。
- privacy/no-storage 边界固定：source trace、lineage、metadata、audit、no_storage 均拒绝 URL、签名参数、session/credential、provider routing/fallback/selector、bucket/storage/download/local path。

## 下一步动作

- 重新触发 PR guardian review。
- guardian 与 GitHub checks 通过后合入 `#423`。
- 合入后进入 `#424` consumer migration；不得在本 PR 中提前实施 #424/#425/#426。

## 当前 checkpoint 推进的 release 目标

- 为 `v1.5.0` 的 `#405` release candidate 提供 media asset fetch runtime slice。
- `v1.5.0` 仍是 `#405` 的显式 release candidate，不因 Phase `#381` 剩余工作自动发布。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`#405` media asset fetch runtime carrier 执行子切片。
- 阻塞：在 #423 合入前，不得进入 #424 consumer migration 中对 `media_asset_fetch_by_ref` 的公开消费路径。

## 已验证项

- `python3 -m unittest tests.runtime.test_operation_taxonomy tests.runtime.test_runtime tests.runtime.test_task_record`
  - 结果：通过，175 tests。
- `python3 -m unittest tests.runtime.test_adapter_resource_requirement_declaration tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_platform_leakage`
  - 结果：通过，161 tests。
- `python3 -m unittest discover -s tests -p 'test*.py'`
  - 结果：通过，527 tests。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/version_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `python3 -m py_compile syvert/operation_taxonomy.py syvert/registry.py syvert/runtime.py syvert/task_record.py tests/runtime/test_operation_taxonomy.py tests/runtime/test_runtime.py tests/runtime/test_task_record.py`
  - 结果：通过。
- `git diff --check`
  - 结果：通过。
- `python3 -m unittest`
  - 结果：未执行测试；当前仓库默认 unittest discovery 未配置，返回 `NO TESTS RAN`。
- PR `#439`
  - 结果：已创建并绑定 branch/workspace；当前 head SHA 由 PR `headRefOid` 与 guardian merge gate 判定。

## 未决风险

- `#424` 尚未迁移 TaskRecord/result query/runtime admission 与 compatibility consumer，当前只交付 runtime carrier。
- `#425` 尚未补齐双参考 sanitized evidence matrix，当前不声明 release criteria 已满足。
- `#426` 必须单独做 `#405` closeout 与 explicit release decision；不得把 Phase completion 绑定成自动 release。

## 回滚方式

- 使用独立 revert PR 撤销本 Work Item 对 runtime、TaskRecord、registry、taxonomy、tests 与本 exec-plan 的增量修改。
- 保留 `#421` formal spec truth，后续重新拆分 `#423` 修复事项。

## 最近一次 checkpoint 对应的 head SHA

- Initial branch checkpoint：`05c4bfbb2f57a533a637e0659e4054e21b8e86f5`
- Current live PR head will be governed by PR `headRefOid` and guardian merge gate after PR creation.
