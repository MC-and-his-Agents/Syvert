# CHORE-0266 v0.7 adapter provider port planning 执行计划

## 关联信息

- item_key：`CHORE-0266-v0-7-adapter-provider-port-planning`
- Issue：`#266`
- item_type：`CHORE`
- release：`v0.7.0`
- sprint：`2026-S20`
- 关联 spec：
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0266-v0-7-adapter-provider-port-planning`
- 状态：`active`

## 目标

- 把 `v0.7.0` 的 provider port 决策同步为 GitHub 与仓内一致真相。
- 明确 `v0.7.0` 只纳入仓内 adapter-owned provider port 边界与 native provider 拆分规划。
- 将外部 provider 接入、更多小红书/抖音能力与 adapter 独立仓库评估明确放到 `v1.0.0` 稳定之后的后续范围。

## 范围

- 本次纳入：
  - 创建 GitHub Phase `#264`、FR `#265` 与 Work Item `#266`。
  - 更新 `docs/roadmap-v0-to-v1.md` 中 `v0.7.0`、`v0.8.0` 到 `v0.9.0`、`v1.0.0` 与 `v1.x` 的范围关系。
  - 新增 `docs/releases/v0.7.0.md` 与 `docs/sprints/2026-S20.md`。
  - 新增本 active exec-plan，记录当前 Work Item 的范围、验证、风险与恢复上下文。
- 本次不纳入：
  - 创建或修改 `FR-0021` formal spec 正文。
  - 实现 provider port runtime 或 native provider 代码拆分。
  - 接入 WebEnvoy、OpenCLI、bb-browser、agent-browser 或其他外部 provider。
  - 批准或实现新的小红书/抖音读写能力。

## 当前停点

- GitHub Phase `#264`、FR `#265` 与 Work Item `#266` 已通过 GitHub REST 建立。
- `create_worktree.py` 受 `gh issue view` GraphQL rate limit 影响无法直接读取新 issue；当前 worktree 已按同一命名规则手动创建并补齐本地 worktree 状态绑定。
- 仓内文档正在当前分支更新，尚未进入 PR review / guardian。

## 下一步动作

- 完成文档修改。
- 执行文档与 workflow 门禁。
- 创建 PR，关联 `#266`，并把 PR 元数据与本 exec-plan 对齐。

## 当前 checkpoint 推进的 release 目标

- 推进 `v0.7.0` 的进入真相：先确定 adapter provider port 边界，再启动 formal spec 与 implementation Work Item。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S20` 的 `v0.7.0` 规划入口 Work Item。
- 阻塞：若本事项不先收口，后续 `FR-0021` formal spec 和实现事项会继续混淆 provider port、外部 provider 接入、新能力批准与 adapter 仓库拆分的时间线。

## 已验证项

- `gh api user --jq .login`
  - 结果：通过，当前 keyring 认证用户为 `mcontheway`。
- `gh api -X GET repos/MC-and-his-Agents/Syvert/issues -f state=open -f per_page=100`
  - 结果：通过，本事项创建前 open issue 列表为空。
- GitHub REST issue 创建：
  - 结果：已创建 Phase `#264`、FR `#265` 与 Work Item `#266`。
- `python3.11 scripts/docs_guard.py --mode ci`
  - 结果：通过，`docs-guard 通过。`
- `python3.11 scripts/workflow_guard.py --mode ci`
  - 结果：通过，`workflow-guard 通过。`
- `python3.11 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，`PR scope 校验通过。`
- `python3.11 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过，`governance-gate 通过。`

## 未决风险

- `gh issue view` GraphQL quota 在当前回合中暂时耗尽；受控脚本中依赖 GraphQL 的步骤需要等待 quota reset 或改用 REST 手动校验。
- 本 PR 只建立规划真相；若后续实现 PR 把外部 provider 或新业务能力混入 `v0.7.0`，仍需在 spec / review 阶段阻断。

## 回滚方式

- 使用独立 revert PR 撤销本事项对 roadmap、release、sprint 与 exec-plan 文档的更新。
- GitHub issue 已创建后不删除历史；若范围需要修正，通过 issue comment 或 edit 追溯更正。

## 最近一次 checkpoint 对应的 head SHA

- `b289bec5af2aa0e1dce7ee72935412d420f647dd`
- worktree 创建基线：`b289bec5af2aa0e1dce7ee72935412d420f647dd`
- 说明：该 checkpoint 对应 `#266` worktree 创建基线；当前 PR head 与门禁结论由后续 PR / guardian 状态绑定。
