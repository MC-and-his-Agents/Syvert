# GOV-0401 Decouple Roadmap Phase From Release Minor

## 关联信息

- Issue：`#401`
- item_key：`GOV-0401-decouple-roadmap-phase-from-release-minor`
- item_type：`GOV`
- release：`v1.x`
- sprint：`2026-S24`
- 关联 decision：`docs/decisions/ADR-GOV-0401-decouple-roadmap-phase-from-release-minor.md`
- active 收口事项：`GOV-0401-decouple-roadmap-phase-from-release-minor`
- 状态：`active`

## 目标

- 切断 roadmap capability track 与 release minor 的隐式编号映射。
- 把现有 roadmap / version rule / CI guard 对齐到同一语义。
- 保留 `v1.1.0`、`v1.2.0` 作为历史 release truth，不把它们上升为未来规则。

## 范围

- 本次纳入：
  - `docs/roadmap-v1-to-v2.md`
  - `docs/process/version-management.md`
  - `scripts/version_guard.py`
  - `tests/governance/test_version_guard.py`
  - 当前 GOV bootstrap contract 与 active exec-plan
- 本次不纳入：
  - 新 capability FR 或 implementation
  - 已发布 release truth rewrite
  - 新 release closeout

## 计划

- 把 roadmap 的 numbered phase capability headings 改成 `Capability Track: ...`。
- 在版本管理文档中写死 `track / Phase / FR / Work Item` 不得隐式映射到 `MINOR`。
- 在 `version_guard.py` 中新增 CI 级旧标题回归门禁，并要求保留解耦语义。
- 在治理测试中补齐正反向用例，覆盖标题回归和语义缺失。

## 验证

- `python3 -m unittest tests.governance.test_version_guard`
  - 结果：通过，`Ran 20 tests`
- `python3 scripts/version_guard.py --mode ci`
  - 结果：通过，`version-guard 通过。`
- `python3 .loom/bin/loom_flow.py shadow-parity --target . --blocking`
  - 结果：通过，所有 declared surfaces `match`
- `python3 scripts/governance_gate.py --mode ci --base-sha f6c101e2befe38dffb6194b8b715e40c759b0c16 --head-sha HEAD --head-ref issue-401-decouple-roadmap-phase-from-release-minor`
  - 结果：通过，`governance-gate 通过。`

## 最近一次 checkpoint 对应的 head SHA

- base：`f6c101e2befe38dffb6194b8b715e40c759b0c16`
- 当前回合尚未记录新 checkpoint head；live review head 以后续 PR `headRefOid` 与 guardian / merge gate 为准。

## 回滚方式

- 如本事项判断或文档表述有误，使用独立 revert PR 回滚本次治理改动。
