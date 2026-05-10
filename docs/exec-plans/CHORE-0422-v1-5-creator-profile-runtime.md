# CHORE-0422 v1.5 creator profile runtime carrier 执行计划

## 关联信息

- item_key：`CHORE-0422-v1-5-creator-profile-runtime`
- Issue：`#422`
- item_type：`CHORE`
- release：`v1.5.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#405`
- 关联 spec：`docs/specs/FR-0405-creator-profile-media-asset-read-contract/spec.md`
- 关联 PR：待创建
- 状态：`active`
- active 收口事项：`CHORE-0422-v1-5-creator-profile-runtime`

## 目标

- 实现 `creator_profile_by_id` runtime carrier。
- 将 `creator_profile + creator + single + direct` 升级为 stable runtime delivery。
- 覆盖 creator ref、normalized public profile、public count 白名单、raw payload ref、source trace、unavailable/failed 分类与 fail-closed 脱敏边界。
- 保持 `content_detail_by_url`、`content_search_by_keyword`、`content_list_by_creator`、`comment_collection` 与 `media_asset_fetch_by_ref` 已冻结行为不回退。

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
  - `media_asset_fetch_by_ref` runtime carrier追加修改，除非为 creator/media 共享合同冲突修复所必需。
  - TaskRecord/result query/runtime admission 与 compatibility consumer migration（#424）。
  - sanitized evidence matrix（#425）。
  - `#405` closeout、release tag、GitHub Release 或 Phase `#381` closeout（#426）。
  - raw payload files、source names、local paths、private creator fields。

## 当前停点

- `#421 / PR #428 / f66136f9772bea348b7ad48ccc766467bc1569ba` 已冻结 `#405` formal spec。
- `#423 / PR #439 / e2e62f8667784d0b746a6c086f259c5268d8430c` 已合入，作为 creator/media shared runtime base。
- `#404` conflict-risk clearance locator：PR `#438`。
- Worktree key：`issue-422-405-v1-5-0-creator-profile-runtime`
- Branch：`issue-422-405-v1-5-0-creator-profile-runtime`

## FR-0405 creator carrier 不变量核对

- public carrier 字段必须白名单：`target`、`profile`、`profile.public_counts`、`source_trace`、`audit` 不接受未定义扩展字段。
- target 使用 formal `CreatorProfileTarget.creator_ref`；`creator_ref`、`target_display_hint`、`policy_ref` 必须是脱敏 opaque ref/hint。
- `result_status` 与 `error_classification` 使用 creator-only 映射：success 为 `complete/null`，`target_not_found/profile_unavailable/permission_denied` 为 `unavailable`，creator failed 分类不接受 media-only `media_unavailable/unsupported_content_type/fetch_policy_denied`。
- raw/normalized/audit split 固定：complete 必须有 raw ref；`provider_or_network_blocked` 必须 raw null；`audit` 只能为空对象。
- privacy boundary 固定：target/profile/source_trace 均拒绝 URL、平台名、账号池、本地路径、credential/session。

## 下一步动作

- 创建 `#422` PR，进入 guardian review。

## 已验证项

- `python3 -m unittest tests.runtime.test_operation_taxonomy tests.runtime.test_runtime tests.runtime.test_task_record`
  - 结果：通过，200 tests。
- `python3 -m unittest tests.runtime.test_operation_taxonomy tests.runtime.test_runtime tests.runtime.test_task_record tests.runtime.test_platform_leakage`
  - 结果：通过，311 tests。
- `python3 -m unittest discover -s tests -p 'test*.py'`
  - 结果：通过，527 tests。
- `python3 -m py_compile syvert/operation_taxonomy.py syvert/registry.py syvert/runtime.py syvert/task_record.py tests/runtime/test_operation_taxonomy.py tests/runtime/test_runtime.py tests/runtime/test_task_record.py`
  - 结果：通过。
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
- `git diff --check`
  - 结果：通过。

## 最近一次 checkpoint 对应的 head SHA

- `a5a41631851d57f4a3c8692195a19eaf353841c7`

## 未决风险

- `#424` 尚未迁移 TaskRecord/result query/runtime admission 与 compatibility consumers，当前只交付 creator runtime carrier。
- `#425` 尚未补 evidence matrix，当前不声明 `#405` release criteria 满足。
- `#426` 必须单独完成 closeout 与 explicit release decision。

## 回滚方式

- 使用独立 revert PR 撤销本 Work Item 对 runtime、TaskRecord、registry、taxonomy、tests 与本 exec-plan 的增量修改。
