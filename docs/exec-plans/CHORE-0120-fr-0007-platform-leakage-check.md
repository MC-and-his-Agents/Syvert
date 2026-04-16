# CHORE-0120-fr-0007-platform-leakage-check 执行计划

## 关联信息

- item_key：`CHORE-0120-fr-0007-platform-leakage-check`
- Issue：`#120`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0007-release-gate-and-regression-checks/`
- 关联 PR：`#123`
- 状态：`active`
- active 收口事项：`CHORE-0120-fr-0007-platform-leakage-check`

## 目标

- 落地 `FR-0007` 平台泄漏检查器，并让结果可直接被 `validate_platform_leakage_source_report()` 与 `orchestrate_version_gate()` 消费。
- 固定扫描面为 `syvert/runtime.py`、`syvert/registry.py`、`syvert/version_gate.py` 三个共享层文件。
- 对平台名硬编码分支、平台专属字段泄漏、单平台共享语义分叉维持 fail-closed。

## 范围

- 本次纳入：
  - `syvert/platform_leakage.py`
  - `tests/runtime/test_platform_leakage.py`
  - `tests/runtime/test_version_gate.py`
  - 当前 active `exec-plan`
- 本次不纳入：
  - adapter 私有实现
  - browser bridge / research 文档
  - `FR-0007` formal spec 改写
  - release / sprint closeout 索引

## 当前停点

- 当前执行现场为独立 worktree：`/Users/mc/code/worktrees/syvert/issue-120-fr-0007`
- 当前执行分支：`issue-120-fr-0007`
- 当前受审 PR：`#123`
- 当前受审 runtime head：`1979bafd014495cb7cf866edd31b1118358ec17e`
- 基线真相：`origin/main@eb5bbc3d0bf0dc5b91fe64a8a63aa24c34ba8479`
- 当前 runtime-affecting 实现 checkpoint：`1979bafd014495cb7cf866edd31b1118358ec17e`
- 当前实现约束：
  - 默认不改 `syvert/version_gate.py`
  - 公开入口先验形再验值，缺失即 fail-closed
  - 允许例外仅限 `normalized.platform`、统一 `error.details`、冻结 reference pair
- 当前代码停点：
  - 已新增 `syvert.platform_leakage`，固定扫描 `runtime.py` / `registry.py` / `version_gate.py`
  - 已补 `tests/runtime/test_platform_leakage.py`
  - 已在 `tests/runtime/test_version_gate.py` 增加真实 checker 输出进入 orchestrator 的接入回归
  - 已修复 guardian 最新阻断：
    - 平台泄漏扫描不再只看 `if` / `match` / 赋值；`return` / `raise` / 任意表达式语句中的 `adapter_key == "xhs"` 一类比较也会直接命中 `hardcoded_platform_branch`
    - 目标文件 AST parse 失败时，不再退回“只扫平台字段”的低保真路径，而是产出 `scan_parse_failure` finding 并显式 fail-closed
    - 共享层平台集合/常量现在按 fail-closed 处理，`SUPPORTED_PLATFORMS = {"xhs", "douyin"}` 一类平台集合常量不再漏报
    - 共享层字符串字面量中的平台特定 selector / url / signature 片段现在按 fail-closed 处理，不再只依赖字段名命中
    - 平台比较主体不再局限于 `adapter_key/platform/reference_pair` 白名单；`adapter == "xhs"` 这类语义等价别名也会 fail-closed 命中
    - 硬编码平台分支只接受真实平台 marker，不再把 `adapter_key == "unknown"` 这类任意字符串比较误判成平台泄漏
    - `error.details["platform"]` / `error.details.get("platform")` 被固定为允许承载、禁止分支：共享层可携带统一错误详情字段，但一旦用它对真实平台名做 `if` / `match` 分支仍会 fail-closed 命中
    - `aweme-detail` / `a_bogus` / `douyin-browser` 这类平台碎片不再误报为 `hardcoded_platform_branch`，但仍会作为 `platform_specific_field_leak` 保持 fail-closed
    - 平台别名传播现在按 fail-closed 处理，`current = adapter_key; if current == "xhs"` 这类中性 alias 分支不再漏报
    - loop target 的平台别名传播现在也按 fail-closed 处理，`for current in [adapter_key]: if current == "xhs"` 不再绕过分支检测
    - 普通常量名里的单平台共享语义现在按 fail-closed 处理，`PRIMARY = "xhs"` 这类不再依赖语义关键字命中
    - 平台特定错误说明已进入共享语义扫描；`raise RuntimeError("xhs only")` 这类平台专属错误解释会被 fail-closed 命中
    - docstring 等说明性文本不再进入平台特定字段扫描面，避免把研究性或注释性字符串误判为共享层泄漏
  - 当前已提交的运行时语义锚定在实现 checkpoint `1979bafd014495cb7cf866edd31b1118358ec17e`
  - 当前剩余动作只包括：把 exec-plan / PR / issue 当前事实同步到同一对象后重发 guardian；若通过，再进入 merge gate

## 实现要点

- 新增 `syvert.platform_leakage`，固定 `boundary_scope` 为六个共享边界，并把 caller 输入与 payload surface 绑定到同一份 boundary scope。
- 扫描结果直接输出为 `platform_leakage` source report payload，再由公开 validator 收口。
- 当前实现把平台泄漏命中面固定在三类 AST/语句级 finding：
  - 平台上下文里的硬编码分支 / 比较，包括 `if` / `match` / `return` / `raise` / 任意表达式语句
  - 平台专属字段或平台特定 selector / url / signature 字符串碎片渗入共享层
  - 带共享语义语境的平台字面量赋值，以及显式平台集合/常量
- 新增独立 runtime 测试，覆盖：
  - 真实共享层扫描 clean pass
  - caller boundary scope 缺项 / 越界 fail-closed
  - 三类 finding 的命中行为
  - 多行平台分支与非 `xhs` / `douyin` 平台字面量
  - `SUPPORTED_PLATFORMS` 一类共享平台集合常量
  - 共享平台语义出现在 return value 与函数默认参数时的 fail-closed
  - `adapter == "xhs"` 一类平台比较别名
  - `adapter_key == "unknown"` 不应误报
  - `raise RuntimeError("xhs only")` 一类平台特定错误说明
  - selector / url / signature 字符串碎片
  - docstring 说明文本不参与平台泄漏判定
  - adapter 私有实现与 research 文档不进入扫描面
- 在 `test_version_gate` 补真实 checker 输出进入 orchestrator 的接入回归，覆盖共享平台集合常量经公开入口被收口。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 提供可复用的平台泄漏 gate 输入，使 `FR-0007` 的第三类固定 gate 能以 hermetic 方式进入版本级收口。

## 已验证项

- 已阅读：`syvert/version_gate.py`
- 已阅读：`syvert/runtime.py`
- 已阅读：`syvert/registry.py`
- 已阅读：`tests/runtime/test_version_gate.py`
- `python3 -m py_compile syvert/platform_leakage.py tests/runtime/test_platform_leakage.py tests/runtime/test_version_gate.py`
  - 结果：通过
- `python3 -m unittest tests.runtime.test_platform_leakage`
  - 结果：在 checkpoint `0f3b1b71a0664527804e078198630732890c8c28` 上通过，覆盖 clean pass、boundary fail-closed、三类 expression-level 平台比较命中、parse failure fail-closed 与排除边界用例。
- `python3 -m unittest tests.runtime.test_version_gate`
  - 结果：在 checkpoint `0f3b1b71a0664527804e078198630732890c8c28` 上通过，并新增 parse failure 经 `run_platform_leakage_check()` 收口进 orchestrator 的回归。
- `python3 -m unittest tests.runtime.test_platform_leakage tests.runtime.test_version_gate tests.runtime.test_runtime tests.runtime.test_registry`
  - 结果：在 checkpoint `0f3b1b71a0664527804e078198630732890c8c28` 上通过，`Ran 149 tests`，`OK`
- `python3 -m py_compile syvert/platform_leakage.py tests/runtime/test_platform_leakage.py tests/runtime/test_version_gate.py`
  - 结果：在 checkpoint `bee9b5ff32a533c2e43fdf6cfe66dba12d2c2f52` 上通过
- `python3 -m unittest tests.runtime.test_platform_leakage tests.runtime.test_version_gate`
  - 结果：在 checkpoint `bee9b5ff32a533c2e43fdf6cfe66dba12d2c2f52` 上通过，`Ran 109 tests`，`OK`
- `python3 -m unittest tests.runtime.test_platform_leakage tests.runtime.test_version_gate`
  - 结果：在 checkpoint `5b1a93a443b78672fd1bd98a4309c05e85d9de8e` 上通过，`Ran 112 tests`，`OK`
- `python3 -m unittest tests.runtime.test_platform_leakage tests.runtime.test_version_gate`
  - 结果：在 checkpoint `0acf7d791fe62b385331c642908fc7a8a9e6321e` 上通过，`Ran 115 tests`，`OK`
- `python3 -m unittest tests.runtime.test_platform_leakage`
  - 结果：在 checkpoint `47f944aaa199b6ea45531b7d2663dac2dfd1a20d` 上通过，`Ran 32 tests`，`OK (skipped=2)`
- `python3 -m unittest tests.runtime.test_platform_leakage tests.runtime.test_version_gate tests.runtime.test_runtime tests.runtime.test_registry`
  - 结果：在 checkpoint `47f944aaa199b6ea45531b7d2663dac2dfd1a20d` 上通过，`Ran 165 tests`，`OK (skipped=3)`
- `python3 -m unittest tests.runtime.test_platform_leakage tests.runtime.test_version_gate tests.runtime.test_runtime tests.runtime.test_registry`
  - 结果：在 checkpoint `10ecdad2cbb94109cc1bc7c7dccdcd6efb6f495f` 上通过，`Ran 167 tests`，`OK (skipped=3)`
- `python3 -m unittest tests.runtime.test_platform_leakage tests.runtime.test_version_gate tests.runtime.test_runtime tests.runtime.test_registry`
  - 结果：在 checkpoint `1979bafd014495cb7cf866edd31b1118358ec17e` 上通过，`Ran 168 tests`，`OK (skipped=3)`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：当前受审 head 复跑，通过。
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
  - 结果：当前受审 head 复跑，通过。
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：当前受审 head 复跑，`PR scope` 校验通过。

## 未决风险

- 若扫描范围扩展到 adapter 私有实现、browser bridge 或 research 文档，会把允许的平台语义误判成共享层泄漏。
- 若把共享层中的 `xhs` / `douyin` 字面量一概视为 finding，会误伤 `normalized.platform`、统一 `error.details` 和冻结 reference pair。
- 若 caller `boundary_scope` 与 payload 自带 `boundary_scope` 不保持同一对象，版本 gate ingress 会出现 surface 洗白风险。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `syvert/platform_leakage.py`、相关测试与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- 实现 checkpoint：`1979bafd014495cb7cf866edd31b1118358ec17e`
- 最近一次重跑目标测试的 head：`1979bafd014495cb7cf866edd31b1118358ec17e`
- 当前受审 runtime head：`1979bafd014495cb7cf866edd31b1118358ec17e`
- 若后续只补 metadata-only follow-up，则必须继续把 runtime checkpoint 维持为 `1979bafd014495cb7cf866edd31b1118358ec17e`，不得把 follow-up 误记为新的运行时真相
