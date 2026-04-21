# CHORE-0136 执行计划

## 关联信息

- item_key：`CHORE-0136-fr-0012-runtime-adapter-closeout`
- Issue：`#181`
- item_type：`CHORE`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 spec：`docs/specs/FR-0012-core-injected-resource-bundle/`
- 关联 decision：
- 关联 PR：`#182`
- active 收口事项：`CHORE-0136-fr-0012-runtime-adapter-closeout`

## 目标

- 在 Core 主执行链中落地 `FR-0012` 的 canonical `AdapterExecutionContext` 与 host-side `ResourceBundle` 注入边界。
- 冻结 hybrid 资源路径的 acquire / host-side bundle 校验 / release 收口语义，确保 acquire 成功后的任一失败分支都会先 settle lease。
- 把 xhs / douyin reference adapter 改造为只消费注入的 `resource_bundle`，并完成 runtime、CLI、contract harness、real adapter regression、version gate 的回归闭环。

## 范围

- 本次纳入：
  - `syvert/runtime.py`
  - `syvert/adapters/xhs.py`
  - `syvert/adapters/douyin.py`
  - `tests/runtime/resource_fixtures.py`
  - runtime / CLI / contract harness / real adapter regression / version gate 相关回归
  - 当前 active `exec-plan`
- 本次不纳入：
  - `FR-0012` formal spec 改写
  - `FR-0011` tracing / usage log
  - 新 proxy provider / 深度网络栈接入
  - 资源 DSL 或能力匹配扩展

## 当前停点

- 当前执行现场：`/Users/mc/code/worktrees/syvert/issue-181-fr-0012-core-reference-adapter`
- 当前执行分支：`issue-181-fr-0012-core-reference-adapter`
- 当前 Work Item：`#181`
- 当前受审 PR：`#182`
- 当前实现 checkpoint：`062567d75c883ef6067e81c2bd6fe9c61b20026b`
- 当前代码已完成以下收口：
  - `execute_task_internal()` 现在由 Core 持有 hybrid 资源策略、`acquire()`、host-side bundle 校验、adapter-facing capability projection、`resource_disposition_hint` 消费与统一 `release()` 收口。
  - lifecycle truth 的 `capability` 固定保持 `content_detail_by_url`；adapter-facing request 仅在进入 adapter 前投影为 `content_detail`。
  - `release()` 失败会覆盖原始 adapter success / failure；非法 hint 与 pre-adapter bundle 校验失败都会先 settle 已 acquire 的 lease。
  - xhs / douyin reference adapter 已改为只接受 `AdapterExecutionContext`，执行材料只从 `resource_bundle.account.material` 派生。
  - runtime / CLI / contract harness / reference regression / version gate 均已接入 host-side resource store seed，避免 hybrid canonical 路径在测试中漂移到 `resource_unavailable`。
  - guardian 首轮 review 指出的两条阻断已收口：
    - host-side bundle 校验现在会绑定 live active lease truth，并在 cleanup 时始终 release 解析出的真实 lease，而不是盲信注入 bundle 的 `lease_id`
    - 非法 `resource_disposition_hint` 已统一回到 `invalid_input / invalid_resource_disposition_hint`
  - guardian 第二轮 review 指出的两条阻断已收口：
    - host-side bundle 校验现在会同时绑定 `acquired_at` 与 slot `ResourceRecord` 全量 truth，拒绝被篡改的执行材料进入 adapter
    - `run_real_adapter_regression()` 与 `run_contract_harness_automation()` 已改为在 clean environment 下显式创建临时 lifecycle store 并 seed 必需资源，不再依赖环境里的隐式 host truth
  - guardian 第三轮 review 指出的阻断已收口：
    - 新增 `syvert/resource_bootstrap.py` 与 `scripts/bootstrap_resource_lifecycle_store.py`，为真实 host-side 执行面提供受支持的 managed resource bootstrap / migration 路径
    - bootstrap 入口允许两种 account 来源：直接提供 canonical account material JSON，或读取 legacy `xhs` / `douyin` session 文件并迁移为 canonical account.material；两种路径都会在写入 store 前按 adapter runtime contract 做 host-side 校验
    - bootstrap 入口只在 host-side 解析默认 lifecycle store；adapter 层仍只消费 Core 注入的 `resource_bundle`，不重新打开 session-file 执行来源面
- 当前回合已进入 `metadata-only closeout follow-up`：本文件用于绑定 Work Item 上下文、checkpoint、review 与 merge gate，不要求其静态 SHA 穷尽到后续纯元数据提交。

## 下一步动作

- 推送包含 bootstrap / migration 入口的新 head，并同步 PR 描述中的 rollout truth。
- 基于 `062567d75c883ef6067e81c2bd6fe9c61b20026b` 重新提交 guardian。
- 若 guardian 转为 `APPROVE`，直接进入受控 `merge_pr`。
- 若仍有阻断，继续优先检查 host-side rollout / lifecycle truth 是否存在新的 contract 漂移。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.4.0` 收口 `FR-0012` 的 Core 注入资源包与 reference adapter 资源消费边界，使 hybrid 执行路径保持单一 lifecycle truth，并为后续 tracing / 资源扩展保留稳定宿主语义。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0012` implementation Work Item，负责把 formal spec 中的 Core ownership、bundle truth 与 reference adapter 边界真正落到运行时主路径。
- 阻塞：待 PR、guardian verdict、GitHub checks 与受控 squash merge 收口。

## 已验证项

- `gh issue create` 已创建 Work Item `#181`
- `python3 -m unittest tests.runtime.test_runtime tests.runtime.test_executor tests.runtime.test_contract_harness_host tests.runtime.test_task_record tests.runtime.test_task_record_store tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter tests.runtime.test_cli tests.runtime.test_real_adapter_regression tests.runtime.test_version_gate`
  - 结果：`Ran 295 tests in 40.994s`，`OK`
- `python3 -m unittest tests.runtime.test_runtime tests.runtime.test_real_adapter_regression tests.runtime.test_contract_harness_automation tests.runtime.test_version_gate`
  - 结果：`Ran 177 tests in 34.528s`，`OK`
- `python3 -m unittest tests.runtime.test_runtime tests.runtime.test_executor tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_automation tests.runtime.test_task_record tests.runtime.test_task_record_store tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter tests.runtime.test_cli tests.runtime.test_real_adapter_regression tests.runtime.test_version_gate`
  - 结果：`Ran 306 tests in 40.860s`，`OK`
- `python3 -m unittest tests.runtime.test_platform_leakage`
  - 结果：`Ran 111 tests in 955.860s`，`OK (skipped=6)`
- `python3 -m unittest tests.runtime.test_resource_bootstrap`
  - 结果：`Ran 5 tests in 0.318s`，`OK`
- `python3 -m unittest tests.runtime.test_runtime tests.runtime.test_executor tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_automation tests.runtime.test_task_record tests.runtime.test_task_record_store tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter tests.runtime.test_cli tests.runtime.test_real_adapter_regression tests.runtime.test_version_gate tests.runtime.test_resource_bootstrap`
  - 结果：`Ran 311 tests in 40.169s`，`OK`
- `python3 -m py_compile syvert/resource_bootstrap.py scripts/bootstrap_resource_lifecycle_store.py tests/runtime/test_resource_bootstrap.py`
  - 结果：通过
- `python3 -m unittest tests.runtime.test_platform_leakage`
  - 结果：`Ran 111 tests in 990.270s`，`OK (skipped=6)`
- `python3 -m unittest tests.runtime.test_runtime`
  - 结果：`Ran 46 tests in 0.123s`，`OK`
- `python3 -m py_compile syvert/runtime.py syvert/adapters/xhs.py syvert/adapters/douyin.py tests/runtime/test_runtime.py tests/runtime/test_xhs_adapter.py tests/runtime/test_douyin_adapter.py tests/runtime/test_cli.py tests/runtime/test_real_adapter_regression.py tests/runtime/test_version_gate.py tests/runtime/resource_fixtures.py`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main`
  - 结果：通过
- `python3 scripts/pr_guardian.py review 182 --post-review`
  - 结果：首轮 `REQUEST_CHANGES`
  - 已修复阻断：
    - host-side bundle 校验新增 live active lease 绑定，拒绝 bundle `lease_id` / `bundle_id` / slot resource ids 与真实 lease 漂移，并在 cleanup 时 release 真实 lease
    - `resource_disposition_hint` 的类型、缺字段、lease mismatch、非法 `target_status_after_release` 统一映射为 `invalid_input / invalid_resource_disposition_hint`
  - 结果：第二轮 `REQUEST_CHANGES`
  - 已修复阻断：
    - host-side bundle 校验新增 `acquired_at` 与完整 slot `ResourceRecord` truth 比对，篡改的 `material` / `acquired_at` 会在进入 adapter 前 fail-closed
    - public harness / regression host 已显式 provision 临时 resource lifecycle store，并新增 clean-environment automation / regression 回归
  - 结果：第三轮 `REQUEST_CHANGES`
  - 已修复阻断：
    - 增加受支持的非测试 bootstrap / migration 路径：`scripts/bootstrap_resource_lifecycle_store.py` 可把 canonical account material JSON 或 legacy session 文件迁移为 host-side managed `account` 资源，并与 `proxy` 资源一起 seed 到默认 lifecycle store
    - 新增 `tests.runtime.test_resource_bootstrap`，覆盖 canonical material 校验、legacy session migration、store seed 与脚本级 bootstrap 回归

## 支持的 rollout / bootstrap 流程

- 对真实 host-side 运行面，先准备一个 `proxy` JSON 文件，再为每个 reference adapter 选择以下任一 account 来源：
  - canonical account material JSON：直接传 `--account-material-file`
  - legacy session 文件迁移：传 `--account-session-file`，脚本会按当前 adapter runtime contract 归一化为 canonical `account.material`
- bootstrap 命令固定通过 host-side 入口执行，例如：
  - `python3 scripts/bootstrap_resource_lifecycle_store.py --adapter xhs --account-resource-id xhs-account-main --account-session-file ~/.config/syvert/xhs.session.json --proxy-resource-id proxy-main --proxy-material-file ./ops/proxy-main.json`
  - `python3 scripts/bootstrap_resource_lifecycle_store.py --adapter douyin --account-resource-id douyin-account-main --account-material-file ./ops/douyin-account.json --proxy-resource-id proxy-main --proxy-material-file ./ops/proxy-main.json`
- store 位置默认继续遵循 `SYVERT_RESOURCE_LIFECYCLE_STORE_FILE` / `~/.syvert/resource-lifecycle.json`；若需要显式切换文件，可追加 `--store-file <path>`。

## 未决风险

- guardian 仍可能继续收敛到 host-side cleanup / carrier 细节；若出现新阻断，应优先检查是否属于同类 lifecycle truth 漂移，而不是在 adapter 侧补影子语义。
- `tests.runtime.test_platform_leakage` 耗时较长；guardian / merge gate 阶段需要保留对慢回归的耐心，避免把长跑误判为卡死。
- 当前实现只冻结 `proxy` 为受管必需 slot 与 bundle truth 的一部分；更深的网络接入能力仍留给后续事项。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对应的 runtime、reference adapter 与测试调整。

## 最近一次 checkpoint 对应的 head SHA

- `44ebe38f2a7e9d13cd239afe130407ee7272c06f`
- 当前回合已进入 `metadata-only closeout follow-up`；后续 PR / review / merge gate 元数据同步不要求该 checkpoint SHA 与最新 HEAD 完全一致。
