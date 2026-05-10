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
- 关联 PR：
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
- 当前实现已落地，等待 PR / guardian / merge gate。

## 下一步动作

- 通过完整本地 guard 后创建 PR，PR 只绑定 `#423` 与本 runtime carrier 范围。
- 合入后进入 `#424` consumer migration；不得在本 PR 中提前实施 #424/#425/#426。

## 当前 checkpoint 推进的 release 目标

- 为 `v1.5.0` 的 `#405` release candidate 提供 media asset fetch runtime slice。
- `v1.5.0` 仍是 `#405` 的显式 release candidate，不因 Phase `#381` 剩余工作自动发布。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`#405` media asset fetch runtime carrier 执行子切片。
- 阻塞：在 #423 合入前，不得进入 #424 consumer migration 中对 `media_asset_fetch_by_ref` 的公开消费路径。

## 已验证项

- `python3 -m unittest tests.runtime.test_operation_taxonomy tests.runtime.test_runtime tests.runtime.test_task_record`
  - 结果：通过，135 tests。
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
