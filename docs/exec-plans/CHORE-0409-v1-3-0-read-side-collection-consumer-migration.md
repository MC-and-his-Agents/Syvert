# CHORE-0409 v1.3.0 read-side collection consumer migration 执行计划

## 关联信息

- item_key：`CHORE-0409-v1-3-read-side-collection-consumer-migration`
- Issue：`#409`
- item_type：`CHORE`
- release：`v1.3.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#403`
- 关联 spec：`docs/specs/FR-0403-read-side-collection-result-cursor-contract/`
- 上游依赖：`#408` runtime carrier 已由 PR `#412` 合入并关闭
- 关联 PR：待创建
- 状态：`active`
- active 收口事项：`CHORE-0409-v1-3-read-side-collection-consumer-migration`

## 目标

- 让 runtime success path、TaskRecord durable truth、result query 与 compatibility consumers 能消费 `FR-0403` collection envelope。
- 保持 `content_detail_by_url` baseline 不变。
- 不扩到 evidence closeout 与 release closeout。

## 范围

- 本次纳入：
  - `syvert/runtime.py`
  - `syvert/task_record.py`
  - `syvert/adapter_capability_requirement.py`
  - `syvert/provider_capability_offer.py`
  - `syvert/registry.py`
  - 对应 runtime / task-record / compatibility / taxonomy consumer tests
- 本次不纳入：
  - `#408` runtime carrier 重写
  - `#410` evidence artifact
  - `#411` release/sprint/FR closeout truth

## 当前停点

- 已完成 collection consumer migration 实现。
- 待补治理验证、commit、PR、review、merge。

## 下一步动作

- 跑 `#409` 范围回归与 guard。
- 创建 PR 并推进受控合并。
- 合入后切到 `#410` evidence artifact。

## 当前 checkpoint 推进的 release 目标

- 为 `v1.3.0` 提供 `#403` collection envelope 的 runtime consumer 与 durable truth 迁移。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：承接 `#408`，为 `#410/#411` 提供可消费的 runtime truth。
- 阻塞：`#410` evidence 必须等本事项合入后执行。

## 已验证项

- `python3 -m unittest tests.runtime.test_task_record tests.runtime.test_runtime tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_operation_taxonomy_consumers tests.runtime.test_provider_no_leakage_guard tests.runtime.test_cli_http_same_path tests.runtime.test_real_adapter_regression`

## 未决风险

- collection resource proof 仍复用既有 `content_detail` 资源 profile 证据基线；当前通过 consumer 侧 fallback 维持 shared resource truth，不在本事项扩张 FR-0015/FR-0027 formal scope。
- `#410` 若 evidence matrix 未覆盖 collection error families，将无法完成 `#403` 收口。

## 回滚方式

- 使用独立 revert PR 回滚本事项 consumer migration 增量；`#408` runtime carrier 保持可独立回归。

## 最近一次 checkpoint 对应的 head SHA

- `672e1c2d1e489089c670f0c09fe991b2924976d4`
