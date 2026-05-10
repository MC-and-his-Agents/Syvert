# CHORE-0426 v1.5 creator media closeout

## 关联信息

- item_key：`CHORE-0426-v1-5-creator-media-closeout`
- Issue：`#426`
- item_type：`CHORE`
- release：`v1.5.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#405`
- 关联 spec：`docs/specs/FR-0405-creator-profile-media-asset-read-contract/`
- 关联 PR：待创建
- 状态：`active`
- active 收口事项：`CHORE-0426-v1-5-creator-media-closeout`

## 目标

- Work Item：`#426`
- Parent FR：`#405`
- Scope：在 `#425` evidence 完成前，先把 `#439/#440/#441` 的 post-merge audit truth 固定为 closeout 输入，避免对已合入实现的质量状态反复猜测。
- Out of scope：`v1.5.0` final published truth、`#405` 关闭、Phase `#381` 关闭、tag / GitHub Release。

## 改动记录

- 新增 `#405` post-merge audit artifact，记录 `#439/#440/#441` 的 merge provenance、补做回归命令、结果和 residual risk。
- 明确这三次 merge 没有通过仓库标准的 `scripts/pr_guardian.py merge-if-safe` 完整入口，但合入前使用了 head-pinned squash merge，并在 merged `origin/main` 上补做了针对性回归。
- 固化回滚触发门槛：只有 merged `origin/main` 上复现 shared runtime regression、FR-0405 public contract drift、creator/media result envelope drift，或 compatibility decision 读取 result carrier 时，才进入 remediation / revert Work Item。

## 验证记录

- `python3 -m unittest tests.runtime.test_operation_taxonomy tests.runtime.test_runtime tests.runtime.test_task_record tests.runtime.test_platform_leakage`
  - 在 detached audit worktree `/tmp/syvert-postmerge-audit.hJQM5O`、`origin/main@508c5a5223d75169f374a7db4c15dd7a825702fd` 上执行；结果：通过，311 tests。
- `python3 -m unittest tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_http_api tests.runtime.test_cli`
  - 在 detached audit worktree `/tmp/syvert-postmerge-audit.hJQM5O`、`origin/main@508c5a5223d75169f374a7db4c15dd7a825702fd` 上执行；结果：通过，177 tests。
- `git diff --check`
  - 结果：通过。

## Review finding 处理记录

- 发现：本地 `main` checkout 停留在 `05c4bfb`，不包含 `#439/#440/#441`，不能作为 post-merge 质量判断基线。
- 处理：使用 detached audit worktree 挂到 `origin/main@508c5a5223d75169f374a7db4c15dd7a825702fd`，只在 merged main 上重跑高价值回归。
- 发现：本地 `scripts/pr_guardian.py review <pr>` 会卡在内部再起的 `codex exec`，无法稳定产出 guardian verdict。
- 处理：在 closeout truth 中显式记录该流程偏差，不把它伪装成标准 `merge-if-safe` provenance。

## 未决风险

- `#425` evidence 仍未合入，当前 audit 只证明 runtime/consumer 行为在 merged main 上未复现 blocker，不等于 `v1.5.0` release criteria 已满足。
- `#426` 当前只记录 closeout 输入，不宣布 `#405` 已完成，也不宣布 Phase `#381` 已满足关闭条件。

## 回滚方式

- 若 merged `origin/main` 上出现 shared runtime regression、public contract drift 或 consumer drift，则创建独立 remediation / revert Work Item；不要直接在 closeout PR 中混入实现修复。
- 若只是 guardian provenance 缺口或 closeout truth 漏写，使用独立 docs / GitHub truth 修正 PR 补齐，不回滚已合入实现。

## 最近一次 checkpoint 对应的 head SHA

- `508c5a5223d75169f374a7db4c15dd7a825702fd`
