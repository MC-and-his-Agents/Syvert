# FR-0001 TODO

## 事项上下文

- Issue：`#6`
- item_key：`FR-0001-governance-stack-v1`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S13`
- exec_plan：`docs/exec-plans/governance-stack-v1.md`（主线前提工件，非 PR `#15` active）
- 事项说明：结构层 active 事项已切换至 `GOV-0014-release-sprint-structure`，本事项在当前轮次仅作为上位前提。

## 状态

- 当前成熟度：`implementation-ready`
- 当前阻塞：
  - 需要完成治理测试回归与仓库侧 dry-run 校验

## 实施清单

- [x] 收缩根级 `AGENTS.md` 到宪法与索引
- [x] 新增 `WORKFLOW.md`
- [x] 新增 `docs/process/agent-loop.md`
- [x] 新增 `docs/process/worktree-lifecycle.md`
- [x] 同步 FR-0001 到 v2 repo harness 目标
- [ ] 完成 v2 脚本与测试回归
- [ ] 完成仓库侧设置 dry-run 校验

## 验证清单

- [x] `workflow-guard`、`docs-guard`、`spec-guard` 通过
- [ ] GitHub checks 全绿
- [ ] 治理测试通过
- [ ] `governance-gate` 通过
- [ ] `sync_repo_settings.py --dry-run` 通过
- [ ] guardian review 对应主线 PR / head 通过
- [ ] 受控 merge 成功完成

## 会话恢复信息

- 当前停点：`FR-0001` 主线事项已形成协议与流程主干，结构层落点改由 `GOV-0014-release-sprint-structure` 独立推进。
- 下一步动作：
  - 继续执行治理测试与仓库侧 dry-run 校验
  - 通过独立事项追踪结构层与后续自动化门禁演进
