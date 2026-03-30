# FR-0001 TODO

## 事项上下文

- Issue：`#6`
- item_key：`FR-0001-governance-stack-v1`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S13`

## 状态

- 当前成熟度：`implementation-ready`
- 当前阻塞：
  - 需要对当前 `head SHA` 获得 latest valid guardian verdict

## 实施清单

- [x] 收缩根级 `AGENTS.md` 到宪法与索引
- [x] 新增 `WORKFLOW.md`
- [x] 新增 `docs/process/agent-loop.md`
- [x] 新增 `docs/process/worktree-lifecycle.md`
- [x] 同步 FR-0001 到 v2 repo harness 目标
- [ ] 完成 v2 脚本与测试回归
- [ ] 完成仓库侧设置 dry-run 校验

## 验证清单

- [ ] 治理测试通过
- [ ] `workflow_guard`、`docs_guard`、`spec_guard`、`governance_gate` 通过
- [ ] `sync_repo_settings.py --dry-run` 通过
- [ ] guardian review 对当前 `head SHA` 通过
- [ ] 受控 merge 成功完成

## 会话恢复信息

- 当前停点：v2 文档与脚本已落地，等待完整回归与 guardian 结论。
- 下一步动作：
  - 执行治理测试与门禁命令
  - 通过 `governance_status.py` 核对状态面
  - guardian 通过后执行 `python3 scripts/merge_pr.py <pr-number> --delete-branch`
