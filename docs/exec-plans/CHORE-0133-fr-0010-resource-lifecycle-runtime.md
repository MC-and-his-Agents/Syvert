# CHORE-0133 执行计划

## 关联信息

- item_key：`CHORE-0133-fr-0010-resource-lifecycle-runtime`
- Issue：`#175`
- item_type：`CHORE`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 spec：`docs/specs/FR-0010-minimal-resource-lifecycle/`
- 关联 PR：`#176`
- active 收口事项：`CHORE-0133-fr-0010-resource-lifecycle-runtime`

## 目标

- 在不改 `execute_task` 主执行链的前提下，落地 `FR-0010` 最小资源生命周期子系统。
- 提供独立的 `acquire / release` contract、本地原子快照存储与最小 bootstrap API。
- 通过单测冻结资源状态迁移、整包 acquire、release 幂等与失败 envelope 回填行为。

## 范围

- 本次纳入：
  - `syvert/resource_lifecycle.py`
  - `syvert/resource_lifecycle_store.py`
  - `tests/runtime/test_resource_lifecycle.py`
  - `tests/runtime/test_resource_lifecycle_store.py`
  - 视需要最小补充当前 active `exec-plan`
- 本次不纳入：
  - `syvert/runtime.py` 主执行路径接线
  - 资源 CLI / API
  - `FR-0011` tracing / usage log
  - `FR-0012` resource bundle 注入与 reference adapter 改造

## 当前停点

- `FR-0010` formal spec 已由 PR `#170` 合入主干，当前执行入口切到真实 Work Item `#175`。
- 当前分支已经落地独立的 `resource_lifecycle` / `resource_lifecycle_store` 模块、原子快照存储与生命周期单测，且保持 `runtime.execute_task()`、CLI 与 reference adapter 主路径不变。
- guardian 首轮 review 已指出 3 个阻断点：快照 stale-write 覆盖、无 active lease 的 `IN_USE` 资源、损坏快照时异常泄漏；当前分支已补 revision CAS、反向状态不变量与 store-failure envelope 回退。
- guardian 第二轮 review 已把阻断收敛到真正的 CAS/互斥写问题；当前分支已把快照 revision 检查与 `os.replace` 放进文件锁保护区，并补并发同基线写入争用测试。
- guardian 第三轮 review 已把阻断收敛到并发同语义 `release` 的幂等 no-op 语义；当前分支已在 release 写入期 CAS 冲突后回读最新 lease，并对“同目标状态 + 同 reason”返回同一 settled `ResourceLease`。
- guardian 第四轮 review 已把阻断收敛到 `release` 非法输入分类与 `INVALID` 资源终态保护；当前分支已把 release 字段解析切到 `invalid_resource_release` 路径，并禁止 `seed_resources()` 把既有 `INVALID` 资源写回可分配状态。
- guardian 第五轮 review 已把阻断收敛到并发不同语义 `release` 的冲突分类；当前工作树已把 CAS 冲突回读后的“已 settled 但语义不一致”路径收口为 `resource_release_conflict`，并补并发冲突 release 回归。
- guardian 第六轮 review 已把阻断收敛到 store bootstrap / 持久化异常边界；当前工作树已把 `seed_resources()` 收紧为“仅允许同值重播，不得覆写既有资源 truth”，并把锁文件准备、`flock`、原子写临时文件等 `OSError` 统一包成 `ResourceLifecyclePersistenceError`。
- guardian 第七轮 review 已把阻断收敛到 durable snapshot 语义校验；当前工作树已让 `validate_snapshot()` 同时校验最新 settled lease 与当前资源 truth 的一致性，并禁止 `INVALID` 终态之后再出现任何后续 lease。
- guardian 第八轮 review 已把阻断收敛到 post-commit unlock 伪失败、同秒序列排序与 `requested_slots` 非法输入；当前工作树已把 `LOCK_UN` 失败降为 best-effort、把 lifecycle 时间戳提到微秒并用“时间戳 + durable lease 顺序”判定最新 truth，同时把 slot 校验改成逐项验证后再去重。
- guardian 第九轮 review 已把阻断收敛到快照时间排序与历史语义完整性；当前工作树已把所有 lease 事件排序切到解析后的 UTC datetime、补齐 `released_at >= acquired_at` 与同资源 lease 区间不重叠校验，并把 `material` 归一失败统一收口为资源生命周期 contract 错误。
- guardian 第十轮 review 已把阻断收敛到 failure carrier 与 bootstrap replay 语义；当前工作树已移除失败路径上的 synthetic `task_id` 生成，并让 `seed_resources()` 对 active durable truth 支持同值 replay 幂等。
- 参考 adapter 仍直接读取本地 session 文件，这属于 `FR-0012` 处理边界，本事项不触碰。

## 下一步动作

- 提交本轮实现补丁并推送分支。
- 通过受控入口创建 implementation PR，并把 `Issue` / `item_key` / `release` / `sprint` 与 PR carrier 对齐。
- 在 PR head 上继续补 guardian / merge gate 所需的收口验证。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.4.0` 建立最小资源生命周期子系统，使后续 `FR-0011` / `FR-0012` 可以围绕同一套 bundle / lease / state truth 继续实现。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0010` 的 implementation Work Item，负责把 formal spec 中的生命周期 contract 落地为可独立调用的 Core 子系统。
- 阻塞：
  - 不得让本次实现长出 tracing schema 或 adapter 注入边界。
  - 不得破坏当前 `runtime` / `registry` / 参考 adapter 回归基线。

## 已验证项

- `gh issue create` 已创建 Work Item `#175`
- `python3 scripts/create_worktree.py --issue 175 --class implementation`
  - 结果：已创建独立 worktree `/Users/mc/code/worktrees/syvert/issue-175-fr-0010`
- `sed -n '1,260p' docs/specs/FR-0010-minimal-resource-lifecycle/spec.md`
- `sed -n '1,260p' docs/specs/FR-0010-minimal-resource-lifecycle/data-model.md`
- `sed -n '1,220p' docs/specs/FR-0010-minimal-resource-lifecycle/contracts/README.md`
- `python3 -m unittest -q tests.runtime.test_resource_lifecycle tests.runtime.test_resource_lifecycle_store`
  - 结果：通过（42 tests, OK）
- `python3 -m unittest -q tests.runtime.test_executor tests.runtime.test_runtime tests.runtime.test_registry`
  - 结果：通过（48 tests, OK）
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `python3 -m unittest -q tests.runtime.test_platform_leakage.PlatformLeakageTests.test_build_payload_passes_for_current_shared_files tests.runtime.test_platform_leakage.PlatformLeakageTests.test_run_check_passes_for_current_shared_files`
  - 结果：通过（2 tests, OK）
- `python3 -m unittest -q tests.runtime.test_real_adapter_regression.RealAdapterRegressionTests.test_end_to_end_real_adapter_regression_report_feeds_version_gate`
  - 结果：失败；主干 `/Users/mc/dev/syvert` 同样失败，属于既有基线问题，不是本事项引入的回归
- guardian `merge_pr.py 176 --refresh-review`
  - 结果：首轮 `REQUEST_CHANGES`
  - 已修复阻断：
    - 快照 write 路径补 revision CAS，拒绝 stale write 覆盖
    - `IN_USE` 资源必须由唯一 active lease 持有
    - 损坏 / 不可读快照统一回退为 canonical failed envelope
  - 第二轮 `REQUEST_CHANGES`
  - 已修复阻断：
    - 快照 write 路径补真实文件锁，把 revision 校验与原子替换收进同一互斥区
    - 新增并发同基线 revision 争用测试，验证一写成功、一写以 `resource_state_conflict` 失败
  - 第三轮 `REQUEST_CHANGES`
  - 已修复阻断：
    - `release()` 在写入期 CAS 冲突后回读最新快照；若 lease 已以相同 `target_status_after_release + reason` settled，则返回该 settled lease
    - 新增并发同语义 `release` 测试，验证两个请求都返回同一份 settled `ResourceLease`
  - 第四轮 `REQUEST_CHANGES`
  - 已修复阻断：
    - `normalize_release_request()` 改用 release 专用字符串提取，确保非字符串 / 缺字段 release 输入统一落到 `invalid_input / invalid_resource_release`
    - `seed_resources()` 禁止把既有 `INVALID` 资源重新写回 `AVAILABLE` 等可分配状态，保持失效终态不可复活
    - 新增非法 release 字段分类测试与 `INVALID` 资源不可复活测试
  - 第五轮 `REQUEST_CHANGES`
  - 已修复阻断：
    - `release()` 在写入期 CAS 冲突后若回读到已 settled 且 `target_status_after_release` / `reason` 与当前请求不一致，统一返回 `resource_release_conflict`
    - 新增并发不同语义 release 回归，验证一方成功、一方 fail-closed 为 `resource_release_conflict`，且快照保留胜出方 settled truth
  - 第六轮 `REQUEST_CHANGES`
  - 已修复阻断：
    - `seed_resources()` 不再允许覆写既有资源 truth；对同一 `resource_id` 仅允许同值重播，任何状态或 material 漂移都 fail-closed 为 `resource_state_conflict`
    - `LocalResourceLifecycleStore` 把锁目录准备、锁文件打开、`flock`、原子写入临时文件等 `OSError` 统一包成 `ResourceLifecyclePersistenceError`，避免 `acquire()` / `release()` 泄漏原始异常
    - 新增已有资源 truth 不可被 `seed_resources()` 覆写、`acquire` 写路径 `OSError` envelope 化、`release` 锁路径 `OSError` envelope 化回归
  - 第七轮 `REQUEST_CHANGES`
  - 已修复阻断：
    - `validate_snapshot()` 新增 latest settled truth 校验：当资源当前不处于 active lease 时，durable resource status 必须与最新 settled lease 的 `target_status_after_release` 一致
    - `validate_snapshot()` 新增 `INVALID` 终态校验：一旦资源被 settled 到 `INVALID`，当前资源状态必须保持 `INVALID`，且不得再出现 `acquired_at` 晚于该 invalid release 的后续 lease
    - 新增 semantically corrupt snapshot 回归，覆盖 store `load_snapshot()` 与 runtime `acquire()` 对“`INVALID` 资源被脏快照复活为 `AVAILABLE`”的 fail-closed 拒绝
  - 第八轮 `REQUEST_CHANGES`
  - 已修复阻断：
    - `_exclusive_lock()` 对 `LOCK_UN` 失败改为 best-effort，不再把已 durable commit 的成功 acquire / release 外翻为失败 envelope
    - `now_rfc3339_utc()` 提升到微秒精度，且 `validate_snapshot()` 以“时间戳 + lease 顺序”推导最新 settled truth，消除同秒多次生命周期转换的错误排序
    - `validate_requested_slots()` 改为逐项校验字符串合法性后再做去重，避免非 hashable slot 直接触发原始 `TypeError`
    - 新增 unlock-after-commit 仍返回成功、同秒 `AVAILABLE -> AVAILABLE -> INVALID` 合法序列、以及非 hashable `requested_slots` 返回 `invalid_resource_request` 回归
  - 第九轮 `REQUEST_CHANGES`
  - 已修复阻断：
    - `validate_snapshot()` 的 lease 事件排序统一改为解析后的 UTC datetime + lease 顺序 marker，消除混合精度 RFC3339 字符串比较带来的错序
    - `validate_resource_lease()` 新增 `released_at >= acquired_at` 约束，`validate_snapshot()` 新增同一资源 lease 区间不得重叠、`INVALID` 终态后不得再有后续 lease 的历史校验
    - `normalize_json_value()` 的 `material` 归一失败通过 `normalize_resource_material()` 统一转成 `ResourceLifecycleContractError`，避免坏快照以 `TaskRecordContractError` 形式逃逸
    - 新增 mixed-precision `INVALID` 后重占用、非法 `material`、`released_at < acquired_at` 与重叠 lease 区间回归
  - 第十轮 `REQUEST_CHANGES`
  - 已修复阻断：
    - `recover_acquire_failure_task_id()` / `recover_release_failure_task_id()` 不再生成 synthetic `task_id`；失败 carrier 只复用请求、task context 或 lease 中已经存在的真实标识
    - `seed_resources()` 对既有 durable truth 只做“同值 replay 允许、任何漂移拒绝”的统一判定，active lease 绑定资源也支持幂等重播
    - 新增“空 context 下失败 carrier 不生成新 task_id”与“active IN_USE 资源允许同值 replay”回归

## 未决风险

- 若 bundle / lease carrier 与 formal spec 漂移，后续 `FR-0011` / `FR-0012` 会被迫建立影子 schema。
- 若本地 store 不是整包原子写入，失败 acquire / release 可能留下半完成 truth。
- `test_platform_leakage` 全集耗时显著高于常规 runtime 回归，后续 guardian / merge gate 阶段应继续把快回归与慢回归拆开记录。
- `tests.runtime.test_real_adapter_regression.RealAdapterRegressionTests.test_end_to_end_real_adapter_regression_report_feeds_version_gate` 当前与主干同样失败；若仓库把它纳入强制 gate，需要独立事项修复 version-gate 与测试 fixture 的不一致。

## 回滚方式

- 使用独立 revert PR 撤销资源生命周期模块、本地 store 与对应测试。

## 最近一次 checkpoint 对应的 head SHA

- `9975baa54f9ab4d5db4bd262a54665802aa7ab97`
