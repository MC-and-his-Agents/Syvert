# CHORE-0118-fr-0007-version-gate-orchestrator 执行计划

## 关联信息

- item_key：`CHORE-0118-fr-0007-version-gate-orchestrator`
- Issue：`#118`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0007-release-gate-and-regression-checks/`
- 关联 decision：
- 关联 PR：`#122`
- 状态：`active`
- active 收口事项：`CHORE-0118-fr-0007-version-gate-orchestrator`

## 目标

- 在 `FR-0007` 范围内落地版本 gate orchestration 与统一结果模型。
- 让版本级 gate 能统一消费 harness、双参考适配器真实回归、平台泄漏检查三类输入，并对缺失输入、结果不完整或结论不可信保持 fail-closed。
- 为后续 closeout / release gate 提供可直接消费且可追溯的统一 verdict / summary。

## 范围

- 本次纳入：
  - `syvert/version_gate.py`
  - `tests/runtime/test_version_gate.py`
  - 当前 active `exec-plan`
- 本次不纳入：
  - 双参考适配器真实回归执行器本体
  - 平台泄漏检查器本体
  - `FR-0004` / `FR-0005` / `FR-0006` formal spec 或 contract 重定义
  - `v0.3.0+` 能力扩展
  - `docs/releases/v0.2.0.md` 与 `docs/sprints/2026-S15.md` 的旧叙事清理

## 当前停点

- 当前执行现场为独立 worktree：`/Users/mc/code/worktrees/syvert/issue-118-fr-0007-gate`
- 当前执行分支：`issue-118-fr-0007-gate`
- `FR-0007` formal spec 已作为当前 Work Item 的 formal input 入库，`open_pr` 对 `CHORE` implementation 项要求 active exec-plan 显式绑定 formal spec。
- 仓内尚无版本级 gate / release gate 现成实现；`FR-0006` 当前已提供可复用的 harness validation 输出，但仍停留在样例级 verdict 层。
- 当前代码已新增 `syvert.version_gate` 与 `tests/runtime/test_version_gate.py`，并通过相关 runtime 测试。
- 当前受审 PR：`#122`
- GitHub 侧当前已对齐：
  - `#118` 正文已更新为 `进行中（PR #122）`
  - 父 FR `#67` 正文已补齐 `#118/#119/#120/#121` 四个子 Work Item
- guardian 首轮审查已返回 `REQUEST_CHANGES`；当前已按审查结论补齐三项 contract 修复：
  - `v0.2.0` reference pair 固定为 `xhs` / `douyin`
  - orchestrator 对 source report 做 source-specific 复验，不再信任伪造 pass wrapper
  - harness verdict 与 runtime 观测的一致性改为强校验
- guardian 第二轮审查已返回 `REQUEST_CHANGES`；当前已按审查结论补齐两项 contract 修复：
  - frozen reference pair 改为按集合而非顺序匹配
  - `reference_pair` / `evidence_refs` / `boundary_scope` / `required_sample_ids` 等字符串序列字段改为拒绝 mapping-shaped malformed payload
- guardian 第三轮审查已返回 `REQUEST_CHANGES`；当前已按审查结论补齐一项 contract 修复：
  - 未知版本在缺少 formal-spec 冻结 reference pair 时改为 fail-closed
- guardian 第四轮审查已返回 `REQUEST_CHANGES`；当前已按审查结论补齐一项 contract 修复：
  - real regression 在 orchestrator 二次校验时改为强制绑定 `content_detail_by_url` 最小矩阵，不再回显 source report 自报 `operation`

## 下一步动作

- 新增 `syvert.version_gate` 模块，冻结三类 source report 的最小消费 contract 与顶层 orchestration 入口。
- 新增 `tests/runtime/test_version_gate.py`，覆盖 pass、三类来源失败、malformed payload、缺失输入与 fail-closed 场景。
- 维持当前 PR `#122` 的验证证据与 active exec-plan 一致，并等待 reviewer / guardian / merge gate。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 提供可复用的版本 gate 编排层，使 `FR-0007` 的三类固定 gate 可以在不改写 formal spec 的前提下统一收口。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0007` implementation A 项，负责 orchestration 与统一 verdict model。
- 阻塞：
  - 不能越界实现真实回归执行器本体或平台泄漏检查器本体。
  - 必须保持 `open_pr` 所需的 formal spec 绑定与 active exec-plan 一致。

## 已验证项

- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`docs/specs/FR-0007-release-gate-and-regression-checks/`
- 已核对：`scripts/open_pr.py` 对 `CHORE` implementation 项会校验 active exec-plan 的 formal spec 绑定
- 已创建 worktree：`python3 scripts/create_worktree.py --issue 118 --class implementation`
- `python3 -m py_compile syvert/version_gate.py tests/runtime/test_version_gate.py`
  - 结果：通过
- `python3 -m unittest tests.runtime.test_version_gate`
  - 结果：`Ran 19 tests`，`OK`
- `python3 -m unittest tests.runtime.test_version_gate`
  - 结果：guardian 修复后复跑，`Ran 25 tests`，`OK`
- `python3 -m unittest tests.runtime.test_version_gate`
  - 结果：第二轮 guardian 修复后复跑，`Ran 30 tests`，`OK`
- `python3 -m unittest tests.runtime.test_version_gate`
  - 结果：第三轮 guardian 修复后复跑，`Ran 32 tests`，`OK`
- `python3 -m unittest tests.runtime.test_version_gate`
  - 结果：第四轮 guardian 修复后复跑，`Ran 33 tests`，`OK`
- `python3 -m unittest tests.runtime.test_contract_harness_automation tests.runtime.test_contract_harness_validation_tool tests.runtime.test_runtime tests.runtime.test_registry`
  - 结果：`Ran 66 tests`，`OK`
- `python3 scripts/pr_guardian.py review 122`
  - 结果：guardian 首轮返回 `REQUEST_CHANGES`
  - 已修复阻断：
    - 拒绝非 `xhs` / `douyin` 的完整 reference pair
    - orchestrator 不再接受缺 source-specific 关键字段的伪造 pass report
    - harness `pass` / `legal_failure` / `execution_precondition_not_met` 与 runtime 观测的一致性改为 fail-closed
- `python3 scripts/pr_guardian.py review 122`
  - 结果：guardian 第二轮返回 `REQUEST_CHANGES`
  - 已修复阻断：
    - frozen reference pair 改为顺序无关
    - 所有经 `_normalize_string_list()` 进入的字符串序列字段都拒绝 mapping-shaped malformed payload
- `python3 scripts/pr_guardian.py review 122`
  - 结果：guardian 第三轮返回 `REQUEST_CHANGES`
  - 已修复阻断：
    - 未知版本在缺少 formal-spec 冻结 reference pair 时改为 fail-closed
- `python3 scripts/pr_guardian.py review 122`
  - 结果：guardian 第四轮返回 `REQUEST_CHANGES`
  - 已修复阻断：
    - real regression 在 orchestrator 二次校验时不再接受 forged `operation`
- `python3 scripts/open_pr.py --class implementation --issue 118 --item-key CHORE-0118-fr-0007-version-gate-orchestrator --item-type CHORE --release v0.2.0 --sprint 2026-S15 --title 'feat(runtime): 落地 FR-0007 版本 gate 编排' --closing fixes --dry-run`
  - 结果：已生成 PR carrier 草稿；待当前 head commit 后再结合 `pr_scope_guard` 重跑
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：`通过`
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
  - 结果：`通过`
- `python3 scripts/open_pr.py --class implementation --issue 118 --item-key CHORE-0118-fr-0007-version-gate-orchestrator --item-type CHORE --release v0.2.0 --sprint 2026-S15 --title 'feat(runtime): 落地 FR-0007 版本 gate 编排' --closing fixes --integration-touchpoint check_required --shared-contract-changed yes --integration-ref MC-and-his-Agents/Syvert#67 --external-dependency none --merge-gate integration_check_required --contract-surface raw_normalized --joint-acceptance-needed no --integration-status-checked-before-pr yes`
  - 结果：已创建 PR `#122`
- `gh pr edit 122 --body ...`
  - 结果：PR 描述已补齐目标、主要改动、风险、验证与 integration carrier
- `gh issue edit 118 --body ...`
  - 结果：`#118` 当前状态已更新为 `进行中（PR #122）`
- `gh issue edit 67 --body ...`
  - 结果：父 FR `#67` 已补齐 `#118/#119/#120/#121` 子 Work Item 列表

## 未决风险

- 若 harness 输入 contract 只校验“存在 `reason` 字段”，会把 malformed payload 误判为可信输入。
- 若统一 report 不冻结 evidence refs 生成规则，后续 closeout / release gate 将无法稳定追溯。
- 若把 source-level 失败来源压平成单一结论，会削弱 `FR-0007` 要求的三类来源区分能力。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `syvert/version_gate.py`、`tests/runtime/test_version_gate.py` 与当前 active exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `a20427293cd7c3fb40d2c4e23359f7292c5d4868`
- 说明：该 checkpoint 已覆盖 guardian 四轮前的全部代码修复；当前 follow-up 仅用于把 active exec-plan 与最新代码 checkpoint、PR `#122` 及审查证据对齐，不再改动运行时代码。
