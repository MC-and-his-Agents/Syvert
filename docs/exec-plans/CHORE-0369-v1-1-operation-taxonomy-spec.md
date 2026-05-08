# CHORE-0369 v1.1 operation taxonomy spec 执行计划

## 关联信息

- item_key：`CHORE-0369-v1-1-operation-taxonomy-spec`
- Issue：`#369`
- item_type：`CHORE`
- release：`v1.1.0`
- sprint：`2026-S23`
- Parent Phase：`#367`
- Parent FR：`#368`
- 关联 spec：`docs/specs/FR-0368-operation-taxonomy-contract/spec.md`
- 状态：`active`

## 目标

- 新增 `FR-0368` operation taxonomy formal spec suite。
- 明确 `v1.1.0` 只稳定 taxonomy foundation，不交付候选 runtime capability。

## 范围

- 本次纳入：
  - `docs/specs/FR-0368-operation-taxonomy-contract/spec.md`
  - `docs/specs/FR-0368-operation-taxonomy-contract/data-model.md`
  - `docs/specs/FR-0368-operation-taxonomy-contract/contracts/README.md`
  - `docs/specs/FR-0368-operation-taxonomy-contract/plan.md`
  - `docs/specs/FR-0368-operation-taxonomy-contract/risks.md`
  - `docs/exec-plans/CHORE-0369-v1-1-operation-taxonomy-spec.md`
- 本次不纳入：
  - runtime / Adapter / Provider / SDK 实现
  - 新 executable public operation
  - release closeout

## 当前停点

- Phase `#367`：open。
- FR `#368`：open。
- Work Item `#369`：open。
- 主仓 baseline：`841c223865ff0c64f04cbd1ab9118e832ddc27fc`。

## 验证计划

- `python3 scripts/spec_guard.py --mode ci --all`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-369-v1-1-operation-taxonomy-formal-spec`

## 风险

- 候选能力被误解为已交付 runtime capability。
- spec 范围越过 `#369`，提前设计实现细节。

## 回滚方式

- 使用独立 revert PR 撤销本 Work Item 新增的 spec suite 与 exec-plan。

## 最近一次 checkpoint 对应的 head SHA

- `841c223865ff0c64f04cbd1ab9118e832ddc27fc`
