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
- 关联 decision：`docs/decisions/ADR-CHORE-0416-comment-collection-operation-name.md`
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
- `python3 scripts/spec_guard.py --mode ci --all`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/version_guard.py --mode ci`
- `python3 -m py_compile syvert/read_side_collection.py syvert/operation_taxonomy.py tests/runtime/test_comment_collection.py tests/runtime/contract_harness/validation_tool.py tests/runtime/contract_harness/third_party_entry.py`
- `python3 - <<'PY' ... run_platform_leakage_check(version='v1.4.0', repo_root='.') ... PY`
- `git diff --check`

## 未决风险

- `FR-0404` 继承 `FR-0403` 的必填 `error_classification` 字段，但继承词表没有独立成功态分类；当前 runtime 使用继承兼容 entry 表示 non-failure complete page，后续 #418 consumer migration 必须保持该语义不被解释为 collection-level failure。
- #418 仍需把 TaskRecord/result query/runtime admission/compatibility decision 对齐到 `comment_collection` stable slice，本 PR 不声明 consumer 完成。

## 回滚方式

- 使用 revert PR 回退本 PR 所有 runtime carrier、taxonomy stable slice 与测试变更。

## 最近一次 checkpoint 对应的 head SHA

- `e74f18dbfa45aa43df38416175550ad9491ef5c8`
