# CHORE-0417 v1.4 comment collection runtime carrier 执行计划

## 关联信息

- item_key：`CHORE-0417-v1-4-comment-collection-runtime`
- Issue：`#417`
- item_type：`CHORE`
- release：`v1.4.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#404`
- 关联 spec：`docs/specs/FR-0404-comment-collection-contract/spec.md`
- 关联 decision：
- 关联 PR：
- 状态：`active`
- active 收口事项：`CHORE-0417-v1-4-comment-collection-runtime`

## 目标

- 实现 `comment_collection` runtime carrier，承载 comment target、page continuation、reply cursor、comment item envelope、visibility status 与 hierarchy linkage。
- 将 `comment_collection + content + single + paginated` 升级为 `v1.4.0` stable runtime taxonomy slice。
- 保持 `FR-0403` 的 `content_search_by_keyword` / `content_list_by_creator` public behavior 不变。
- 覆盖 fake carrier happy path、fail-closed path、request cursor 互斥、reply linkage 与 comment visibility unit tests。

## 范围

- 本次纳入：
  - `syvert/read_side_collection.py`
  - `syvert/operation_taxonomy.py`
  - `tests/runtime/test_comment_collection.py`
  - 相关 taxonomy admission/runtime 测试修正。
- 本次不纳入：
  - TaskRecord / result query / runtime admission / compatibility consumer migration（#418）。
  - sanitized fake/reference evidence artifact 与 replay tests（#419）。
  - `v1.4.0` published truth、tag、GitHub Release 或 closeout（#420）。
  - `#405` creator profile / media asset read contract。

## 当前停点

- Issue `#417` 正在 runtime carrier 实施收口。
- Worktree key：`issue-417-404-v1-4-0-comment-collection-runtime`
- Branch：`issue-417-404-v1-4-0-comment-collection-runtime`
- 最新基线提交：`e74f18dbfa45aa43df38416175550ad9491ef5c8`

## 下一步动作

- 完成 runtime carrier 与 taxonomy stable slice 验证。
- 创建 PR 并通过 code review / guardian / runtime gates。
- 合入后从主干进入 `#418` consumer migration；不得在本 PR 中提前实施 #418/#419/#420。

## 当前 checkpoint 推进的 release 目标

- 为 `v1.4.0` comment collection slice 提供首个 runtime carrier 与 taxonomy runtime-delivery truth。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`#404` runtime carrier 执行子切片。
- 阻塞：在 #417 合入前，不得进入 #418 consumer migration。

## 已验证项

- `python3 -m unittest tests.runtime.test_comment_collection tests.runtime.test_read_side_collection tests.runtime.test_operation_taxonomy tests.runtime.test_operation_taxonomy_admission_evidence tests.runtime.test_platform_leakage tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_version_gate`
- `python3 -m unittest tests.runtime.test_comment_collection tests.runtime.test_read_side_collection tests.runtime.test_operation_taxonomy tests.runtime.test_operation_taxonomy_admission_evidence tests.runtime.test_runtime tests.runtime.test_task_record tests.runtime.test_registry tests.runtime.test_platform_leakage tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_version_gate`（380 tests）
- `python3 -m unittest tests.runtime.test_models tests.runtime.test_comment_collection tests.runtime.test_read_side_collection tests.runtime.test_operation_taxonomy tests.runtime.test_operation_taxonomy_admission_evidence tests.runtime.test_runtime tests.runtime.test_task_record tests.runtime.test_registry tests.runtime.test_platform_leakage tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_version_gate`（402 tests）
- `python3 -m unittest tests.runtime.test_models tests.runtime.test_comment_collection tests.runtime.test_read_side_collection tests.runtime.test_operation_taxonomy tests.runtime.test_operation_taxonomy_admission_evidence tests.runtime.test_runtime tests.runtime.test_task_record tests.runtime.test_registry tests.runtime.test_platform_leakage tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_version_gate tests.runtime.test_third_party_adapter_contract_entry`（450 tests）
- `python3 -m unittest tests.runtime.test_models tests.runtime.test_comment_collection tests.runtime.test_read_side_collection tests.runtime.test_operation_taxonomy tests.runtime.test_operation_taxonomy_admission_evidence tests.runtime.test_runtime tests.runtime.test_task_record tests.runtime.test_registry tests.runtime.test_platform_leakage tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_version_gate tests.runtime.test_third_party_adapter_contract_entry`（449 tests）
- `python3 -m unittest tests.runtime.test_models tests.runtime.test_comment_collection tests.runtime.test_read_side_collection tests.runtime.test_operation_taxonomy tests.runtime.test_operation_taxonomy_admission_evidence tests.runtime.test_runtime tests.runtime.test_task_record tests.runtime.test_registry tests.runtime.test_platform_leakage tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_version_gate tests.runtime.test_third_party_adapter_contract_entry`（453 tests）
- `python3 -m unittest tests.runtime.test_models tests.runtime.test_comment_collection tests.runtime.test_read_side_collection tests.runtime.test_operation_taxonomy tests.runtime.test_operation_taxonomy_admission_evidence tests.runtime.test_runtime tests.runtime.test_task_record tests.runtime.test_registry tests.runtime.test_platform_leakage tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_version_gate tests.runtime.test_third_party_adapter_contract_entry`（455 tests）
- `python3 -m unittest tests.runtime.test_models tests.runtime.test_comment_collection tests.runtime.test_read_side_collection tests.runtime.test_operation_taxonomy tests.runtime.test_operation_taxonomy_admission_evidence tests.runtime.test_runtime tests.runtime.test_task_record tests.runtime.test_registry tests.runtime.test_platform_leakage tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_version_gate tests.runtime.test_third_party_adapter_contract_entry`（457 tests）
- `python3 -m unittest tests.runtime.test_models tests.runtime.test_comment_collection tests.runtime.test_read_side_collection tests.runtime.test_operation_taxonomy tests.runtime.test_operation_taxonomy_admission_evidence tests.runtime.test_runtime tests.runtime.test_task_record tests.runtime.test_registry tests.runtime.test_resource_capability_evidence tests.runtime.test_platform_leakage tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_version_gate tests.runtime.test_third_party_adapter_contract_entry`（484 tests）
- `python3 - <<'PY' ... validate_frozen_resource_capability_evidence_contract() ... PY`
- `python3 -m unittest tests.runtime.test_registry tests.runtime.test_runtime.RuntimeExecutionTests.test_validate_success_payload_rejects_comment_reply_thread_drift_against_dataclass_cursor tests.runtime.test_runtime.RuntimeExecutionTests.test_validate_success_payload_rejects_comment_reply_thread_drift_against_request_cursor`
- `python3 scripts/spec_guard.py --mode ci --all`
- `python3 scripts/spec_guard.py --mode ci --base-sha f66136f9772bea348b7ad48ccc766467bc1569ba --head-sha HEAD`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/version_guard.py --mode ci`
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
- `python3 scripts/governance_gate.py --mode ci --base-sha f66136f9772bea348b7ad48ccc766467bc1569ba --head-sha HEAD --head-ref issue-417-404-v1-4-0-comment-collection-runtime`
- `python3 -m py_compile syvert/read_side_collection.py syvert/operation_taxonomy.py syvert/runtime.py syvert/task_record.py syvert/registry.py tests/runtime/test_comment_collection.py tests/runtime/test_runtime.py tests/runtime/contract_harness/validation_tool.py tests/runtime/contract_harness/third_party_entry.py`
- `python3 - <<'PY' ... run_platform_leakage_check(version='v1.4.0', repo_root='.') ... PY`
- `git diff --check`

## Review finding 处理记录

- PR `#429` guardian finding：`comment_collection` 已声明 stable runtime slice，但 runtime success path 仍按 content-detail payload 校验。
  - 处理：已将 `comment_collection` 接入 runtime capability map、`content` target、success payload validator、success envelope serializer、resource requirement admission、TaskRecord terminal envelope validation，并新增 focused runtime tests。
- PR `#429` guardian finding：reply-window `next_continuation.resume_comment_ref` 不应要求 root comment 出现在当前 reply page items。
  - 处理：已移除该错误约束，保留 target 绑定校验，并新增“后续 reply page 仅返回 replies，但 continuation 绑定原 root comment”的 focused test。
- PR `#429` guardian finding：reply-window `next_continuation.resume_comment_ref` 仍必须防止漂移到另一 comment thread。
  - 处理：已把 reply-window continuation 绑定到当前 reply page items 的 `root_comment_ref`，并新增 cross-comment continuation drift regression。
- PR `#429` guardian finding：runtime path 未携带或校验 `CommentRequestCursor`。
  - 处理：已把 `comment_request_cursor` 加入 `TaskInput` / `CoreTaskRequest` / `AdapterTaskRequest` 的 runtime path，进入 Adapter 前执行互斥与 target binding 校验，并新增 cursor propagation 与 mixed-cursor fail-closed tests。
- PR `#429` guardian finding：`validate_success_payload` 新签名破坏现有 content-detail helper 调用方。
  - 处理：已恢复 content-detail 旧调用兼容；collection/comment collection 调用仍在传入 capability 时校验 target context，并补充 `tests.runtime.test_models` 验证证据。
- PR `#429` guardian finding：请求侧 cursor fail-closed 返回了通用 failed envelope，而不是 comment collection result carrier。
  - 处理：已在 adapter 执行前为 `signature_or_request_invalid` / `cursor_invalid_or_expired` 构造 `comment_collection` fail-closed result carrier，返回 `result_status=complete`、对应 `error_classification`、`items=[]`、`has_more=false`、`next_continuation=null`。
- PR `#429` guardian finding：`CoreTaskRequest` 上的无效 comment cursor 仍返回通用 failed envelope。
  - 处理：已让 `comment_collection_request_error_envelope` 同时支持 `TaskRequest` 与 `CoreTaskRequest`，并新增 `CoreTaskRequest` mixed-cursor fail-closed regression。
- PR `#429` guardian finding：shared contract harness 仍把所有 success payload 当成 `content_detail_by_url`。
  - 处理：已让 harness/validation tool 从 collection target 推导 target context，并对 collection/comment collection success envelope 保留 carrier 字段；新增 comment collection harness success regression，并纳入 `tests.runtime.test_third_party_adapter_contract_entry` 验证。
- PR `#429` guardian finding：`comment_collection` 资源证明被 `content_detail` 基线静默兜底。
  - 处理：已撤销 registry 对 `comment_collection` 的 content-detail proof fallback；`#417` 只保留 runtime carrier、payload validation、request cursor fail-closed carrier，不在本 PR 伪造资源证明。后续 full resource/consumer admission 仍由 `#418` 承接。
- PR `#429` guardian finding：contract harness 使用 payload 自身 target context 会漏掉 collection/comment target drift。
  - 处理：已让 `ContractSampleDefinition` 携带 expected target context，automation / third-party entry 从 fixture/request 传入 target，validation 使用 expected target 校验 payload；新增 comment target drift regression。
- PR `#429` guardian finding：comment cursor fail-closed success carrier 不应绕过 durable TaskRecord。
  - 处理：已让 pre-adapter comment cursor fail-closed carrier 创建 accepted/running/succeeded TaskRecord，并补 `TaskRequest` / `CoreTaskRequest` 回归断言。
- PR `#429` guardian finding：`comment_collection` 有效请求无法通过资源准入。
  - 处理：经后续 guardian 复核，#417 不应提前提升 shared resource profile；已撤回 `comment_collection` approved resource evidence/profile，runtime carrier focused test 改为无资源声明 fake adapter，完整 admission/resource proof 留给后续 evidence/consumer 批次。
- PR `#429` guardian finding：reply hierarchy 没有约束 root/parent/target linkage。
  - 处理：已收紧 reply item hierarchy validation，拒绝 self-root/self-parent 与跨 thread target linkage，并补 malformed hierarchy regression。
- PR `#429` guardian finding：malformed request cursor 仍漏出通用 failed envelope。
  - 处理：已把 request cursor `parse_failed` 也收敛为 `comment_collection` fail-closed carrier，并补 malformed cursor regression。
- PR `#429` guardian finding：成功态未校验请求侧 reply thread 绑定。
  - 处理：已让 `validate_success_payload` 接收 runtime request cursor，并校验返回 items / next continuation 与请求 cursor 的 `resume_comment_ref` 一致；新增 reply-thread drift regression。
- PR `#429` guardian finding：非法 `CoreTaskRequest` 轴会被 fail-closed 分支改写成合法 content/paginated。
  - 处理：已收紧 pre-admission fail-closed 分支，仅对已是 `comment_collection + content + paginated` 的 CoreTaskRequest 生成 comment carrier；非法轴保留通用 failed envelope，并补回归。
- PR `#429` guardian finding：`comment_collection` resource evidence code baseline 与 formal research registry 不一致。
  - 处理：已撤回 #417 中的 shared resource evidence/profile 提升，不修改正式 spec 区；FR-0015 formal alignment 继续只覆盖既有 `content_detail` baseline，避免污染既有 resource governance 基线。
- PR `#429` guardian finding：canonical `CommentRequestCursor` dataclass 可绕过 reply-thread drift 校验。
  - 处理：已让 runtime request cursor thread extraction 同时支持 mapping 与 dataclass carrier，并新增 dataclass cursor drift regression。
- PR `#429` guardian finding：top-level `page_continuation` 可以静默漂移到 reply-thread payload。
  - 处理：已在 `validate_success_payload` 中校验 top-level page cursor 上下文，拒绝 reply items 或携带 `resume_comment_ref` 的 reply continuation，并新增 drift regression。
- PR `#429` guardian finding：shared resource profile 在没有 adapter-side proof 的情况下被提前批准。
  - 处理：已撤回 `comment_collection` shared dual-reference evidence、approved vocabulary 扩展与 `fr-0027:profile:comment-collection-paginated:account-proxy` 暴露；#417 只交付 runtime carrier，不声明 resource profile approved。

## 未决风险

- `FR-0404` 继承 `FR-0403` 的必填 `error_classification` 字段，但继承词表没有独立成功态分类；当前 runtime 使用继承兼容 entry 表示 non-failure complete page，后续 #418 consumer migration 必须保持该语义不被解释为 collection-level failure。
- #418 仍需把 TaskRecord/result query/runtime admission/compatibility decision 对齐到 `comment_collection` stable slice，本 PR 不声明 consumer 完成。

## 回滚方式

- 使用 revert PR 回退本 PR 所有 runtime carrier、taxonomy stable slice 与测试变更。

## 最近一次 checkpoint 对应的 head SHA

- `e74f18dbfa45aa43df38416175550ad9491ef5c8`
