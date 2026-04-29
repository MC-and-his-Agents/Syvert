# CHORE-0269 FR-0021 provider port native provider runtime 执行计划

## 关联信息

- item_key：`CHORE-0269-fr-0021-provider-port-native-provider-runtime`
- Issue：`#269`
- item_type：`CHORE`
- release：`v0.7.0`
- sprint：`2026-S20`
- 关联 spec：`docs/specs/FR-0021-adapter-provider-port-boundary/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0269-fr-0021-provider-port-native-provider-runtime`
- 状态：`active`

## 目标

- 在不改变 Core / Adapter public contract 的前提下，为小红书、抖音实现 adapter-owned provider port 与 native provider 拆分。
- 保持 Core 只调用 Adapter，registry / TaskRecord / resource lifecycle 不出现 provider 字段。
- 保持当前小红书、抖音 `content_detail_by_url` approved slice 的输入、资源需求、raw / normalized payload 与错误优先级兼容。

## 范围

- 本次纳入：
  - 新增小红书、抖音 adapter 内部 provider port / native provider 模块。
  - `XhsAdapter` / `DouyinAdapter` 继续暴露既有 metadata、constructor transport hooks 与 `execute()`。
  - Adapter 继续负责 request validation、resource bundle consumption 与 normalized result 生成。
  - Native provider 只接收 Adapter 构造的 provider-internal context、validated URL 与 parsed target/session config。
  - 新增测试证明 Adapter 委托 native provider，且 registry/Core 输出不暴露 provider 字段。
- 本次不纳入：
  - 外部 provider 接入。
  - Core provider registry、provider selector 或 fallback priority。
  - 新增小红书/抖音业务 capability。
  - SDK 文档/capability metadata closeout。
  - 双参考 evidence closeout。

## 当前停点

- `#268` formal spec 已由 PR `#282` 合入主干，merge commit `7a4cbaa72ccd41263ce8d94dbcb7ed8c894dd882`。
- 当前 worktree 绑定 `#269`，基线为 `7a4cbaa72ccd41263ce8d94dbcb7ed8c894dd882`。

## 下一步动作

- 拆出 `syvert/adapters/xhs_provider.py` 与 `syvert/adapters/douyin_provider.py`。
- 调整 `XhsAdapter` / `DouyinAdapter` 使用 native provider，同时保留 legacy transport hook 与 import path。
- 补充 runtime / registry 测试。
- 运行 unit / regression / governance gates。
- 创建 implementation PR 并通过 guardian / merge gate。

## 当前 checkpoint 推进的 release 目标

- 推进 `v0.7.0` 的 adapter surface 稳定化：把 provider-like 执行细节收进 adapter-owned provider port，避免后续外部 provider 讨论污染 Core contract。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S20` 中 `FR-0021` 的 runtime implementation Work Item。
- 阻塞：`#271` evidence 与 `#272` FR parent closeout 依赖本事项合入主干。

## 已验证项

- `python3.11 scripts/create_worktree.py --issue 269 --class implementation`
  - 结果：通过，创建 worktree `issue-269-fr-0021-provider-port-native-provider`。
- `python3.11 -m unittest tests.runtime.test_xhs_adapter`
  - 结果：通过，41 tests OK。
- `python3.11 -m unittest tests.runtime.test_douyin_adapter`
  - 结果：通过，16 tests OK。
- `python3.11 -m unittest tests.runtime.test_registry`
  - 结果：通过，13 tests OK。
- `python3.11 -m unittest tests.runtime.test_real_adapter_regression`
  - 结果：通过，21 tests OK。
- `python3.11 -m unittest tests.runtime.test_version_gate`
  - 结果：通过，99 tests OK。
- `python3.11 -m unittest tests.runtime.test_runtime`
  - 结果：通过，58 tests OK。
- `python3.11 -m py_compile syvert/adapters/xhs.py syvert/adapters/xhs_provider.py syvert/adapters/douyin.py syvert/adapters/douyin_provider.py syvert/registry.py`
  - 结果：通过。
- `python3.11 -m unittest tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter`
  - 结果：通过，57 tests OK。
- `python3.11 -m unittest tests.runtime.test_registry tests.runtime.test_real_adapter_regression tests.runtime.test_version_gate`
  - 结果：通过，133 tests OK。
- `python3.11 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `python3.11 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3.11 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3.11 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。

## 未决风险

- 若 native provider 直接接收 `AdapterExecutionContext` 或 Core resource bundle，会把 resource consumption ownership 从 Adapter 漂移到 provider。
- 若拆分后 `raw` carrier、normalized fields 或 fallback error priority 发生变化，会破坏 `#271` 可复验 evidence。
- 若在 registry/resource requirement 中新增 provider 字段，会违反 `FR-0021` formal spec。

## 回滚方式

- 使用独立 revert PR 撤销本次 provider module、adapter delegation 与测试增量，回到主干当前内嵌执行逻辑。

## 最近一次 checkpoint 对应的 head SHA

- `7a4cbaa72ccd41263ce8d94dbcb7ed8c894dd882`
- worktree 创建基线：`7a4cbaa72ccd41263ce8d94dbcb7ed8c894dd882`
- 说明：该 checkpoint 对应 `#268` formal spec 合入后的 `#269` runtime implementation 起点。
