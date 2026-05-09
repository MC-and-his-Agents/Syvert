# CHORE-0410 v1.3.0 read-side collection evidence 执行计划

## 关联信息

- item_key：`CHORE-0410-v1-3-read-side-collection-evidence`
- Issue：`#410`
- item_type：`CHORE`
- release：`v1.3.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#403`
- 关联 spec：`docs/specs/FR-0403-read-side-collection-result-cursor-contract/`
- 上游依赖：`#408` 已由 PR `#412` 合入；`#409` 已由 PR `#413` 合入
- 关联 PR：待创建
- 状态：`active`
- active 收口事项：`CHORE-0410-v1-3-read-side-collection-evidence`

## 目标

- 交付 `#403` 的脱敏 evidence artifact 与可复放 JSON snapshot。
- 证明 `content_search_by_keyword` 与 `content_list_by_creator` 共享同一 collection public surface。
- 不引入 raw payload、外部项目名或本地路径。

## 范围

- 本次纳入：
  - `docs/exec-plans/artifacts/CHORE-0410-v1-3-read-side-collection-evidence.md`
  - `tests/runtime/test_read_side_collection_evidence.py`
  - 对应回归与 guard
- 本次不纳入：
  - runtime / consumer 代码修改
  - release / sprint / FR closeout truth

## 当前停点

- 待实现 evidence artifact、replay test、回归、commit、PR、merge。

## 下一步动作

- 实现 artifact 与 replay test。
- 跑 evidence / leakage / baseline 回归与 governance gate。
- 创建 PR 并推进受控合并，随后进入 `#411`。

## 当前 checkpoint 推进的 release 目标

- 为 `v1.3.0` 的 `#403` collection slice 提供可消费 evidence truth。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：承接 `#408/#409`，为 `#411` closeout 提供证据载体。
- 阻塞：`#411` 必须等本事项合入后执行。

## 已验证项

- 待回归。

## 未决风险

- evidence snapshot 若漂移，会导致 closeout truth 缺乏可复验依据；当前通过独立 replay test 约束。
- 若 evidence 继续引用外部 source name 或本地路径，将直接破坏 `FR-0403` 的 sanitization boundary。

## 回滚方式

- 使用独立 revert PR 回滚 artifact、tests 与本 exec-plan；`#408/#409` 保持独立真相。

## 最近一次 checkpoint 对应的 head SHA

- `6565f13dac14a8bf9bb3ae7241ed9ada33b0bd20`
