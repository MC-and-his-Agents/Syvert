# CHORE-0326-fr-0026-docs-evidence-migration 执行计划

## 关联信息

- item_key：`CHORE-0326-fr-0026-docs-evidence-migration`
- Issue：`#326`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 父 FR：`#298`
- 关联 spec：`docs/specs/FR-0026-adapter-provider-compatibility-decision/`
- active 收口事项：`CHORE-0326-fr-0026-docs-evidence-migration`
- 状态：`active`

## 目标

- 补齐 `FR-0026` compatibility decision 的 SDK 文档、docs evidence、迁移说明与 fail-closed 示例。
- 让 Adapter 作者能区分 `ProviderCapabilityOffer.declared`、`AdapterProviderCompatibilityDecision.matched`、`unmatched` 与 `invalid_contract`。
- 给 `#327` 父 FR closeout 提供可引用的 docs / evidence 输入。

## 范围

- 本次纳入：
  - `adapter-sdk.md`
  - `docs/exec-plans/CHORE-0326-fr-0026-docs-evidence-migration.md`
  - `docs/exec-plans/artifacts/CHORE-0326-fr-0026-compatibility-decision-evidence.md`
  - `docs/releases/v0.8.0.md`
  - `docs/sprints/2026-S21.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `scripts/**`
  - `docs/specs/FR-0026-adapter-provider-compatibility-decision/**`
  - provider selector / router / fallback / priority / ranking
  - 真实 provider 产品支持
  - 父 FR `#298` closeout

## 当前停点

- worktree：`/Users/mc/code/worktrees/syvert/issue-326-fr-0026-compatibility-decision`
- 分支：`issue-326-fr-0026-compatibility-decision`
- worktree 创建基线：`d1577d6e620a43010c40e81f3a8c05b413dbc04f`
- 已确认 `#324` runtime decision 与 `#325` no-leakage guard 已合入主干，父 FR `#298` 仍 open。
- 当前 checkpoint：PR `#341` 已创建，head `740698e13245708cc3c527e5e2a6a5c45c5a144a` 已通过本地 docs class gates、相关 runtime 对齐测试与 GitHub checks。首轮 guardian 因外部 `429 Too Many Requests` 未产出 verdict；第二轮 guardian 返回 `REQUEST_CHANGES`，指出本 exec-plan 的下一步 / 待验证状态未与当前 PR 状态对齐。当前已修正为 merge gate 前状态。

## 下一步动作

- 复跑 docs class 必要门禁以验证本 metadata-only 修正。
- 在当前 head 上重新运行 guardian review。
- guardian `APPROVE` 且同一 head 的 GitHub checks 全绿后使用受控 merge。
- 合并后确认 `#326` closeout，更新父 FR `#298` comment，清理 worktree 并退役分支。

## 已验证项

- `python3 scripts/create_worktree.py --issue 326 --class docs`
  - 结果：通过；创建 worktree `/Users/mc/code/worktrees/syvert/issue-326-fr-0026-compatibility-decision`，分支 `issue-326-fr-0026-compatibility-decision`，基线 `d1577d6e620a43010c40e81f3a8c05b413dbc04f`。
- `#324` / PR `#339`
  - 结果：已合入主干，提供 `syvert.adapter_provider_compatibility_decision` runtime truth。
- `#325` / PR `#340`
  - 结果：已合入主干，提供 `syvert.provider_no_leakage_guard` runtime truth。
- `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard`
  - 结果：通过，51 tests。
- `git diff --check`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-326-fr-0026-compatibility-decision`
  - 结果：通过。
- 提交前 `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：首次运行因新增文件尚未进入 Git diff，返回“当前分支相对基线没有变更”；提交后复跑。
- 最终提交后 `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard`
  - 结果：通过，51 tests。
- 最终提交后 `git diff --check`
  - 结果：通过。
- 最终提交后 `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- 最终提交后 `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- 最终提交后 `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- 最终提交后 `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-326-fr-0026-compatibility-decision`
  - 结果：通过。
- 最终提交后 `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`docs`，变更类别=`docs`。

## 待验证项

- 当前 metadata-only 修正后的 docs class gate 复跑。
- 当前 head 的 guardian `APPROVE`。
- 受控 merge、`#326` closeout、父 FR `#298` comment、worktree cleanup 与 branch retirement。

## 风险

- 若文档把 `matched` 写成 selected provider、Core routing 或 provider 产品支持，会越过 `FR-0026` formal boundary。
- 若文档直接复制 runtime private evidence 为 Core-facing author surface，会破坏 no-leakage 口径。

## 回滚方式

- 使用独立 revert PR 撤销 docs / evidence 增量。
- 若发现 SDK 文档需要改变 formal boundary，回到 `FR-0026` spec Work Item，不在 docs PR 中改写规约。

## 最近一次 checkpoint 对应的 head SHA

- worktree 创建基线：`d1577d6e620a43010c40e81f3a8c05b413dbc04f`
- docs / evidence checkpoint：`d967c323b381c55814ee0ecb792d6077e0f78f46`
- final gate checkpoint：`d41329aabde3a62f0e984b6a7827d1d28198a732`
