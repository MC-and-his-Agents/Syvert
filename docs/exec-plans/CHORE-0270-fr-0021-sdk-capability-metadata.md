# CHORE-0270 FR-0021 SDK capability metadata 执行计划

## 关联信息

- item_key：`CHORE-0270-fr-0021-sdk-capability-metadata`
- Issue：`#270`
- item_type：`CHORE`
- release：`v0.7.0`
- sprint：`2026-S20`
- 关联 spec：`docs/specs/FR-0021-adapter-provider-port-boundary/`
- 关联 decision：
- 关联 PR：`#284`
- active 收口事项：`CHORE-0270-fr-0021-sdk-capability-metadata`
- 状态：`active`

## 目标

- 基于 `FR-0021` formal spec 与 `#269` runtime implementation，补齐 Adapter SDK 兼容性、capability metadata 与迁移约束说明。
- 明确 provider port 是 adapter-owned 内部执行边界，不是 Core-facing provider SDK。
- 同步 `v0.7.0` release / sprint 索引，使 GitHub truth、主干实现与仓内文档一致。

## 范围

- 本次纳入：
  - 更新 `adapter-sdk.md` 的 `v0.7.0` 兼容性说明。
  - 更新 `docs/releases/v0.7.0.md`。
  - 更新 `docs/sprints/2026-S20.md`。
- 本次不纳入：
  - runtime provider port 实现变更。
  - 外部 provider 接入。
  - 新业务能力或资源类型。
  - 双参考 evidence closeout。
  - FR parent closeout。

## 当前停点

- `#268` formal spec 已由 PR `#282` 合入主干。
- `#269` runtime implementation 已由 PR `#283` 合入主干。
- 当前 worktree 绑定 `#270`，基线为 `de2e3aaf3e83554a9241e1ae28fac14599359fbc`。

## 下一步动作

- 更新 SDK compatibility / capability metadata 说明。
- 同步 release / sprint 索引。
- 运行 docs / workflow / governance gates。
- 创建 docs PR 并通过 guardian / merge gate。

## 当前 checkpoint 推进的 release 目标

- 推进 `v0.7.0` adapter surface 稳定化：让 SDK 文档明确当前 Core / Adapter contract 不因 native provider 拆分而改变。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S20` 中 `FR-0021` 的 SDK compatibility / capability metadata Work Item。
- 阻塞：`#272` FR parent closeout 需要消费本事项合入后的文档真相。

## 已验证项

- `python3.11 scripts/create_worktree.py --issue 270 --class docs`
  - 结果：通过，创建 worktree `issue-270-fr-0021-sdk`。
- `python3.11 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `python3.11 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3.11 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3.11 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `python3.11 scripts/pr_guardian.py review 284 --post-review --json-output /tmp/syvert-pr-284-guardian.json`
  - 结果：REQUEST_CHANGES。guardian 指出 `adapter-sdk.md` 仍有旧 `adapter_id` / `platform_name` / `collect()` 叙述、未批准 capability 示例，以及 exec-plan 未写入 PR 编号。
  - 处理：已统一 SDK 文档为 `adapter_key` / `resource_requirement_declarations` / `execute()` 当前表面，能力示例收敛到 `content_detail` + `url` + `hybrid` + `account/proxy`，并补齐 PR `#284` 关联。
- `python3.11 scripts/pr_guardian.py review 284 --post-review --json-output /tmp/syvert-pr-284-guardian-r2.json`
  - 结果：REQUEST_CHANGES。guardian 指出缺少 SDK contract id / compatibility declaration、第三方 adapter 最小迁移说明，以及资源契约把 cookie/user-agent 等内部执行材料误读成 Core resource capability。
  - 处理：已新增 `syvert-adapter-sdk/v0.7` compatibility declaration 格式、`v0.7.0` 最小迁移说明，并收紧资源契约为 `account` / `proxy` only。

## 未决风险

- 若 SDK 文档把 provider port 描述成外部 provider SDK，会扩大 `FR-0021` 范围。
- 若 capability metadata 误新增搜索、评论、发布、互动等能力，会绕过 approved capability 流程。
- 若 release/sprint 仍停留在 planning truth，会阻塞后续 `#272` parent closeout。

## 回滚方式

- 使用独立 revert PR 撤销本次文档与索引增量，不回滚 `#268/#269` 已合入的 formal spec / runtime 实现。

## 最近一次 checkpoint 对应的 head SHA

- `de2e3aaf3e83554a9241e1ae28fac14599359fbc`
- worktree 创建基线：`de2e3aaf3e83554a9241e1ae28fac14599359fbc`
- 说明：该 checkpoint 对应 `#269` runtime implementation 合入后的 `#270` docs 起点。
