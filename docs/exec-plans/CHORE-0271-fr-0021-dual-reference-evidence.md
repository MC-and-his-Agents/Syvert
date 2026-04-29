# CHORE-0271 FR-0021 dual reference evidence 执行计划

## 关联信息

- item_key：`CHORE-0271-fr-0021-dual-reference-evidence`
- Issue：`#271`
- item_type：`CHORE`
- release：`v0.7.0`
- sprint：`2026-S20`
- 关联 spec：`docs/specs/FR-0021-adapter-provider-port-boundary/`
- 关联 decision：
- 关联 PR：`#285`
- active 收口事项：`CHORE-0271-fr-0021-dual-reference-evidence`
- 状态：`active`

## 目标

- 在 `#269` provider port / native provider 拆分与 `#270` SDK compatibility / capability metadata 合入后，收口小红书、抖音双参考回归证据。
- 证明当前 approved slice 仍保持兼容：public operation `content_detail_by_url`、adapter-facing `content_detail` family、`url` target、`hybrid` mode、`account` + `proxy` resource boundary、raw payload 与 normalized result。
- 给 `#272` FR parent closeout 提供可追溯 evidence artifact。

## 范围

- 本次纳入：
  - 新增 `FR-0021` 双参考回归 evidence artifact。
  - 更新 `v0.7.0` release / `2026-S20` sprint 索引，记录 `#271` evidence closeout。
  - 运行双参考 adapter regression 与相关 runtime / registry / gate 验证命令。
- 本次不纳入：
  - 修改 provider port runtime。
  - 修改 formal spec 语义。
  - 新增外部 provider、provider selector 或 fallback priority。
  - 新增小红书/抖音搜索、评论、账号、发布、通知、互动等业务能力。
  - 关闭 `#265` parent FR 或 `#264` Phase。

## 当前停点

- `#268` formal spec 已由 PR `#282` 合入主干。
- `#269` runtime implementation 已由 PR `#283` 合入主干。
- `#270` SDK compatibility / capability metadata 已由 PR `#284` 合入主干。
- 当前 worktree 绑定 `#271`，基线为 `c707fa8d7468fb4fce398234e4448253b83a8c5a`。

## 下一步动作

- 固化 `FR-0021` 双参考 evidence artifact。
- 运行双参考回归与相关单元测试。
- 运行 docs / workflow / governance / scope gates。
- 创建 docs PR 并通过 guardian / merge gate。
- PR 合入后关闭 `#271`，再进入 `#272` parent FR closeout。

## 当前 checkpoint 推进的 release 目标

- 推进 `v0.7.0` adapter surface 稳定化：证明 native provider 拆分没有改变小红书、抖音当前 approved slice 的行为边界。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S20` 中 `FR-0021` 的双参考 evidence Work Item。
- 阻塞：`#272` FR parent closeout 需要消费本事项合入后的 evidence truth。

## 已验证项

- `python3.11 scripts/create_worktree.py --issue 271 --class docs`
  - 结果：通过，创建 worktree `issue-271-fr-0021`。
- `python3.11 - <<'PY' ... run_real_adapter_regression(version="v0.2.0", adapters=RealAdapterRegressionTests.hermetic_adapters()) ... PY`
  - 结果：通过，source report `verdict=pass`，覆盖 `xhs` / `douyin` 两个 reference adapter 与四个 evidence refs。
- `python3.11 -m unittest tests.runtime.test_real_adapter_regression`
  - 结果：通过，21 tests OK。
- `python3.11 -m unittest tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter`
  - 结果：通过，57 tests OK。
- `python3.11 -m unittest tests.runtime.test_registry tests.runtime.test_version_gate`
  - 结果：通过，112 tests OK。
- `python3.11 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `python3.11 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3.11 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3.11 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `python3.11 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，`PR class=docs`。
- `python3.11 scripts/open_pr.py --class docs --issue 271 --item-key CHORE-0271-fr-0021-dual-reference-evidence --item-type CHORE --release v0.7.0 --sprint 2026-S20 --title 'docs(evidence): 收口 FR-0021 双参考回归证据' --closing fixes --integration-touchpoint none --shared-contract-changed no --integration-ref none --external-dependency none --merge-gate local_only --contract-surface none --joint-acceptance-needed no --integration-status-checked-before-pr no --integration-status-checked-before-merge no`
  - 结果：已创建 PR `#285`。

## 未决风险

- 当前 `real_adapter_regression` helper 的冻结 reference adapter surface 仍绑定 `v0.2.0`。本事项把它作为行为保持证据使用，并用当前 `v0.7.0` worktree head 重新运行；它不声明新增 `v0.7.0` version-gate source schema。
- 若 evidence artifact 把 provider port 描述为外部 provider 支持，会扩大 `FR-0021` 范围。
- 若回归只证明单平台或只证明 success case，会阻塞 `#272` parent closeout。

## 回滚方式

- 使用独立 revert PR 撤销本次 evidence artifact 与 release / sprint 索引增量；若回归暴露 runtime 兼容问题，应回到 `#269` 或新建修复 Work Item，不在本 evidence PR 中隐式改写实现范围。

## 最近一次 checkpoint 对应的 head SHA

- `c707fa8d7468fb4fce398234e4448253b83a8c5a`
- worktree 创建基线：`c707fa8d7468fb4fce398234e4448253b83a8c5a`
- 受审 head：以 GitHub PR `head.sha` 为准。
- 说明：该 checkpoint 对应 `#271` evidence artifact 与 release / sprint 索引增量提交后的受审 head。
