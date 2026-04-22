# CHORE-0146-fr-0015-evidence-closeout-rerun 执行计划

## 关联信息

- item_key：`CHORE-0146-fr-0015-evidence-closeout-rerun`
- Issue：`#211`
- item_type：`CHORE`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 spec：`docs/specs/FR-0015-dual-reference-resource-capability-evidence/`
- 关联 PR：`#212`
- 状态：`active`
- active 收口事项：`CHORE-0146-fr-0015-evidence-closeout-rerun`

## 目标

- 在 `main@b1f918885b751f4278cf2216204cbb90c0e57b2d` 的干净主干上，重新落地 `FR-0015` machine-readable dual-reference resource capability evidence baseline。
- 复用 `#197 / PR #204` 已收敛的实现内容，但在新的合法 Work Item / 分支 / PR 上重新完成 review、guardian 与 merge gate 收口。
- 让 `#195/#196` 后续只能从单一代码 registry 读取 `approved` capability ids 与 traceable `evidence_refs`，不再复制 `account`、`proxy` 或 evidence 字符串。

## 范围

- 本次纳入：
  - 新增 `syvert/resource_capability_evidence.py` 作为 `FR-0015` evidence baseline 的唯一代码入口
  - 新增 `tests/runtime/test_resource_capability_evidence.py` 复验 registry、runtime 事实与 formal research traceability
  - 新增 `docs/exec-plans/artifacts/CHORE-0146-fr-0015-resource-capability-evidence-baseline.md` 作为人类可审 artifact
  - 更新 `docs/exec-plans/FR-0015-dual-reference-resource-capability-evidence.md`，追加 `#211` rerun round 的追溯入口
- 本次不纳入：
  - 修改 `docs/specs/FR-0015-dual-reference-resource-capability-evidence/` formal spec 语义
  - 修改 `syvert/runtime.py`、reference adapter 或 `syvert/version_gate.py` 的运行语义
  - 修改 `#195 / FR-0013`、`#196 / FR-0014` 的实现
  - 修改 release / sprint 索引

## 当前停点

- `#197 / PR #204` 曾把同一实现合入 `main`，merge commit 为 `a8b6ffc87b41afae5d4d9c4e95de74791e521b5b`。
- 由于该次合入未等待 latest guardian 对当前受审 head 给出明确 `APPROVE`，已由 `#209 / PR #210` 回退，回退后 `main` 基线为 `b1f918885b751f4278cf2216204cbb90c0e57b2d`。
- 当前 rerun worktree 为 `/Users/mc/code/worktrees/syvert/issue-211-fr-0015`，最新实现 checkpoint 已推进到 `f8fbb73be3fec6adc4d6a9b98e71c465dc16fbf6`。
- 当前受审 implementation PR 已创建为 `#212`，latest guardian 曾在前一受审 head 上给出 `REQUEST_CHANGES`，阻断点集中在 formal research traceability 未由 carrier 自身强制，以及 id-based 缓存会放过 post-validation drift。
- latest guardian 随后又在后一受审 head 上给出 `REQUEST_CHANGES`，指出 runtime accessor 不应对 `research.md` 与源码 AST checkout 形成硬依赖。
- latest guardian 第三次又在更新后的受审 head 上给出 `REQUEST_CHANGES`，指出 strict validator 对 formal research duplicate rows 没有 fail-closed。
- latest guardian 第四次又在更新后的受审 head 上给出 `REQUEST_CHANGES`，指出 `execution_path` 片段解析仍会放过重复 key。
- latest guardian 第五次又在更新后的受审 head 上给出 `REQUEST_CHANGES`，指出 public accessor 仍需对 evidence entry source pointer drift fail-closed。
- 当前 head `f8fbb73be3fec6adc4d6a9b98e71c465dc16fbf6` 已把 runtime accessor 与 strict validator 分层，并补上 formal research `evidence_ref` / `capability_id` / `(adapter_key, candidate)` 重复行、`execution_path` 重复 key，以及 frozen evidence entry pointer drift 的显式拒绝；后续 GitHub checks、guardian verdict 与 merge gate 结果统一回写到本 exec-plan。

## 下一步动作

- 完成 code / tests / artifact / requirement-container traceability 迁入。
- 执行固定本地验证命令与 PR scope / governance 门禁。
- 等待当前受审 PR `#212` 在最新 head 上的 GitHub checks 回齐。
- 等待 GitHub checks 全绿与 latest guardian `APPROVE`，确认 `safe_to_merge=true` 且 review / merge 绑定同一 head 后，再执行受控 squash merge。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.5.0` 恢复 `FR-0015` 共享资源能力证据基线的可信实现入口，使后续 `FR-0013/FR-0014` 能直接消费同一份批准能力词汇与证据引用。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0015` evidence implementation closeout 的合法 rerun Work Item。
- 阻塞：
  - 在本回合重新合入前，`main` 只有 formal registry truth，没有 machine-readable evidence registry truth。
  - 若再次在未获得 latest guardian `APPROVE` 前合入，会重复同类流程违背。

## 已验证项

- `python3 scripts/create_worktree.py --issue 211 --class implementation`
  - 结果：已创建当前 worktree `/Users/mc/code/worktrees/syvert/issue-211-fr-0015`
  - base SHA：`b1f918885b751f4278cf2216204cbb90c0e57b2d`
- `python3 -m py_compile syvert/resource_capability_evidence.py tests/runtime/test_resource_capability_evidence.py`
  - 结果：在 checkpoint `7531e138d8d4d4ea7f5b8fb80ea86918d66f3cb2` 上通过
- `python3 -m unittest tests.runtime.test_resource_capability_evidence tests.runtime.test_real_adapter_regression tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter`
  - 结果：在 checkpoint `7531e138d8d4d4ea7f5b8fb80ea86918d66f3cb2` 上通过，`Ran 92 tests`，`OK`
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：在 checkpoint `7531e138d8d4d4ea7f5b8fb80ea86918d66f3cb2` 上通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：在 checkpoint `7531e138d8d4d4ea7f5b8fb80ea86918d66f3cb2` 上通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：在 checkpoint `7531e138d8d4d4ea7f5b8fb80ea86918d66f3cb2` 上通过
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：在 checkpoint `7531e138d8d4d4ea7f5b8fb80ea86918d66f3cb2` 上通过，`PR class=implementation`
- `python3 scripts/governance_gate.py --mode ci --base-sha \"$(git merge-base origin/main HEAD)\" --head-sha \"$(git rev-parse HEAD)\" --head-ref issue-211-fr-0015`
  - 结果：在 checkpoint `7531e138d8d4d4ea7f5b8fb80ea86918d66f3cb2` 上通过
- `python3 scripts/open_pr.py --class implementation --issue 211 --item-key CHORE-0146-fr-0015-evidence-closeout-rerun --item-type CHORE --release v0.5.0 --sprint 2026-S18 --title 'feat(runtime): 重提 FR-0015 资源能力证据基线' --base main --closing fixes`
  - 结果：已创建当前受审 implementation PR `#212 https://github.com/MC-and-his-Agents/Syvert/pull/212`
- latest guardian review（绑定前一受审 head）
  - 结果：`REQUEST_CHANGES`
  - 阻断摘要：formal research traceability 仅由测试覆盖，未由 carrier 自身强制；id-based 验证缓存会放过 source drift 之后的错误批准结果
- latest guardian review（绑定后一受审 head）
  - 结果：`REQUEST_CHANGES`
  - 阻断摘要：runtime accessor 不应把 `research.md` 与源码 AST checkout 变成运行前提；strict traceability 需要与 runtime 读取边界分层
- latest guardian review（绑定第三个受审 head）
  - 结果：`REQUEST_CHANGES`
  - 阻断摘要：strict validator 必须对 formal research duplicate rows fail-closed，不能让 dict 覆盖隐藏重复输入
- latest guardian review（绑定第四个受审 head）
  - 结果：`REQUEST_CHANGES`
  - 阻断摘要：`execution_path` 解析必须对重复 key fail-closed，不能让后值覆盖前值
- latest guardian review（绑定第五个受审 head）
  - 结果：`REQUEST_CHANGES`
  - 阻断摘要：public accessor 也必须冻结 canonical evidence entry baseline，不能放过 evidence entry source pointer drift
- `python3 -m py_compile syvert/resource_capability_evidence.py tests/runtime/test_resource_capability_evidence.py`
  - 结果：在 checkpoint `f8fbb73be3fec6adc4d6a9b98e71c465dc16fbf6` 上通过
- `python3 -m unittest tests.runtime.test_resource_capability_evidence tests.runtime.test_real_adapter_regression tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter`
  - 结果：在 checkpoint `f8fbb73be3fec6adc4d6a9b98e71c465dc16fbf6` 上通过，`Ran 99 tests`，`OK`
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：在 checkpoint `f8fbb73be3fec6adc4d6a9b98e71c465dc16fbf6` 上通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：在 checkpoint `f8fbb73be3fec6adc4d6a9b98e71c465dc16fbf6` 上通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：在 checkpoint `f8fbb73be3fec6adc4d6a9b98e71c465dc16fbf6` 上通过
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：在 checkpoint `f8fbb73be3fec6adc4d6a9b98e71c465dc16fbf6` 上通过，`PR class=implementation`
- `python3 scripts/governance_gate.py --mode ci --base-sha \"$(git merge-base origin/main HEAD)\" --head-sha \"$(git rev-parse HEAD)\" --head-ref issue-211-fr-0015`
  - 结果：在 checkpoint `f8fbb73be3fec6adc4d6a9b98e71c465dc16fbf6` 上通过

## 未决风险

- 若当前主干事实已偏离 `#197` 收敛实现依赖的 runtime / adapter 证据面，迁入后的 traceability tests 可能暴露 formal spec 与实现真相漂移。
- 若 artifact 与代码 registry 不再一一对应，后续 `#195/#196` 可能再次复制能力名或 evidence ref 字符串，破坏单一事实源。
- 若 guardian 对当前受审 head 提出重复类阻断，必须按系统性根因修复，而不是只做单点补丁。

## 回滚方式

- 若本 rerun round 发现实现与 formal spec 基线冲突，使用独立 Work Item + revert PR 回退当前 implementation PR；不得改写 `#197/#204` 或 `#209/#210` 的历史回合真相。

## 最近一次 checkpoint 对应的 head SHA

- `f8fbb73be3fec6adc4d6a9b98e71c465dc16fbf6`
