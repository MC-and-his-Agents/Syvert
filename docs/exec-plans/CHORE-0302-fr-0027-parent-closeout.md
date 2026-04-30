# CHORE-0302-fr-0027-parent-closeout 执行计划

## 关联信息

- item_key：`CHORE-0302-fr-0027-parent-closeout`
- Issue：`#303`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0027-multi-profile-resource-requirement-contract/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0302-fr-0027-parent-closeout`
- 状态：`active`

## 目标

- 汇总 `FR-0027` formal spec、profile evidence、matcher/runtime 与 reference adapter migration 的主干事实，完成父 FR `#294` closeout，并把它作为后续 `FR-0024` / `FR-0026` 的正式前置 truth。

## 范围

- 本次纳入：
  - `docs/exec-plans/FR-0027-multi-profile-resource-requirement-contract.md`
  - `docs/exec-plans/CHORE-0302-fr-0027-parent-closeout.md`
  - `docs/releases/v0.8.0.md`
  - `docs/sprints/2026-S21.md`
- 本次不纳入：
  - formal spec 正文修改
  - runtime / adapter 行为修改
  - `v0.8.0` Phase closeout
  - 后续 `FR-0024` / `FR-0026` formal spec 或实现工作

## 当前停点

- `#299` / PR `#304` 已合入：formal spec closeout，merge commit `9feb47387c655e1d0b50474249fed577637654c8`。
- `#300` / PR `#305` 已合入：FR-0015 profile evidence truth，merge commit `8414b0625ec0b9c4f17be135cb47d75998765056`。
- `#301` / PR `#306` 已合入：matcher/runtime V2 contract，merge commit `431c4b0f9182f3a14d3b642a315bd266986e5923`。
- `#302` / PR `#307` 已合入：reference adapter declaration migration，merge commit `d6f1e7f08ad967b147a8e4be8a24f2e2c42432cb`。
- GitHub issue `#299/#300/#301/#302` 均已关闭；父 FR `#294` 当前仍 open，等待本 closeout PR 合入后写 closeout comment 并关闭。

## 下一步动作

- 运行 docs / governance 门禁。
- 提交并创建 `#303` 受控 PR。
- PR 合入后，在 `#294` 写 closeout comment 并关闭 FR。
- 核对 `#303` 自动关闭状态；若未自动关闭，使用 GitHub REST 补关闭。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 固定 FR-0027 已完成的 multi-profile resource requirement 主干 truth，使后续开放接入相关 FR 不再绑定旧单声明模型。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0027` 的 parent closeout Work Item。
- 阻塞：
  - `#296`、`#298` 后续 formal freeze / implementation rollout 可以把 `#294` 作为已关闭前置 truth 消费。

## 已验证项

- 已通过 GitHub REST / PR view 核对 `#304/#305/#306/#307` 均已 merged，且 `#299/#300/#301/#302` 均已 closed。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-303-fr-0027`
  - 结果：通过。

## 未决风险

- 本 PR 合入前不关闭 `#294`；否则 GitHub 状态会早于仓内 closeout truth。
- 本 closeout 不代表 `v0.8.0` Phase 已完成，也不替代 `FR-0024` / `FR-0026` 后续工作。

## 回滚方式

- 使用独立 revert PR 撤销本事项对 requirement container、closeout exec-plan 与 release / sprint 索引的 metadata 修改。
- 若关闭后发现事实不一致，重新打开 `#294` 或新建修复 Work Item。

## 最近一次 checkpoint 对应的 head SHA

- `ffb35a1e18bf21487eb9462bd828f8dd5588518e`
- 说明：该 checkpoint 首次把 FR-0027 parent closeout requirement container、active closeout exec-plan 与 release / sprint 索引同步落盘；后续若只补 PR / guardian / merge gate 元数据，则作为 review-sync follow-up，不把版本化 exec-plan 退化为 live head 状态面。
