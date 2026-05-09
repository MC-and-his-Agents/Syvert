# CHORE-0408 v1.3 read-side collection runtime carrier 执行计划

## 关联信息

- item_key：`CHORE-0408-v1-3-0-read-side-collection-runtime`
- Issue：`#408`
- item_type：`CHORE`
- release：`v1.3.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#403`
- 关联 spec：`docs/specs/FR-0403-read-side-collection-result-cursor-contract/spec.md`
- 关联 decision：
- 关联 PR：`#412`
- 状态：`active`
- active 收口事项：`CHORE-0408-v1-3-0-read-side-collection-runtime`

## 目标

- 实现 #408 指定的 read-side collection runtime carrier，共享 result/continuation/item envelope。
- 将 `content_search_by_keyword` 与 `content_list_by_creator` 作为 runtime stable operation 纳入 taxonomy。
- 将新 carrier 纳入 platform leakage 扫描和 version_gate 证据基线。
- 覆盖对应 runtime fake/adaptor 回归测试。

## 范围

- 本次纳入：
  - `syvert/read_side_collection.py`
  - `syvert/operation_taxonomy.py`
  - `syvert/platform_leakage.py`
  - `syvert/version_gate.py`
  - `tests/runtime/test_read_side_collection.py`
  - 相关 runtime/platform/leakage/version-gate 测试修正。
- 本次不纳入：
  - TaskRecord/result query/compatibility consumers 迁移（#409）
  - fixture/evidence closeout（#410）
  - release/sprint/FR closeout（#411）

## 当前停点

- Issue `#408` 仍处于 runtime carrier 实施收口。
- Worktree key：`issue-408-403-v1-3-0-read-side-collection-runtime`
- Branch：`issue-408-403-v1-3-0-read-side-collection-runtime`
- 最新基线提交：`87b783de578d7646d1ab69f27f898f5379579ae0`

## 下一步动作

- 等待 PR #412 完成治理门禁并进入 merge-ready。
- 按链路继续推进 #409/#410/#411。

## 当前 checkpoint 推进的 release 目标

- 为 `v1.3.0` 首批 read-side collection runtime contract 提供 carrier 契约与扫描基线对齐。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`#403` run-time carrier 执行子切片。
- 阻塞：在 #409/#410/#411 审批前，不得将此 PR 合并进主线。

## 已验证项

- `python3 -m unittest tests.runtime.test_read_side_collection tests.runtime.test_operation_taxonomy tests.runtime.test_platform_leakage tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path`
- `python3 -m unittest tests.runtime.test_version_gate`
- `python3 scripts/spec_guard.py --mode ci --all`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/version_guard.py --mode ci`
- `git diff --check`

## 未决风险

- 缺少 #409/#410/#411 的执行快照会导致 `#408` 不能直接声明全量完成。
- #412 若受限于外部 GitHub issue 上下文（如 exec-plan 授权）可导致受控合并被阻断。

## 回滚方式

- 使用 revert PR 回退本 PR 所有 runtime 实现与扫描/测试变更。

## 最近一次 checkpoint 对应的 head SHA

- `87b783de578d7646d1ab69f27f898f5379579ae0`
