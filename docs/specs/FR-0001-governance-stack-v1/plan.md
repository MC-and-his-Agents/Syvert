# FR-0001 实施计划

## 关联信息

- item_key：`FR-0001-governance-stack-v1`
- Issue：`#6`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`

## 实施目标

- 将治理栈从 v1 规则闭环升级到 v2 repo harness 闭环，并保持可执行、可恢复、可回归。

## 分阶段拆分

- 阶段 1：重构文档体系，新增 `WORKFLOW.md`、agent loop、worktree lifecycle。
- 阶段 2：新增 `create_worktree`、`governance_status`、`workflow_guard`、`sync_repo_settings`。
- 阶段 3：升级 `open_pr`、`pr_guardian`、`review_poller`、`governance_gate` 与状态路径。
- 阶段 4：补齐测试与 CI 回归，完成受控 merge 收口。

## 实现约束

- 不允许触碰的边界：
  - 不把平台特定实现写入治理栈
  - 不把 AI guardian 绑定进 GitHub-hosted CI
  - 不引入常驻 daemon 与调度循环
  - 不把 backlog / sprint 正文镜像回仓库
- 与上位文档的一致性约束：
  - 运行契约只在 `WORKFLOW.md` 定义
  - 长任务协议只在 `docs/process/agent-loop.md` 定义
  - merge gate 细则只在 `code_review.md` 定义

## 测试与验证策略

- 单元测试：
  - `tests/governance/test_workflow_guard.py`
  - `tests/governance/test_create_worktree.py`
  - `tests/governance/test_governance_status.py`
  - `tests/governance/test_open_pr.py`
  - `tests/governance/test_commit_check.py`
  - `tests/governance/test_docs_guard.py`
  - `tests/governance/test_pr_guardian.py`
  - `tests/governance/test_pr_scope_guard.py`
  - `tests/governance/test_spec_guard.py`
- 集成/契约测试：
  - `python3 scripts/workflow_guard.py --mode ci`
  - `python3 scripts/sync_repo_settings.py --repo MC-and-his-Agents/Syvert --dry-run`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - `python3 scripts/create_worktree.py --issue <n> --class <class> --dry-run`
  - `python3 scripts/governance_status.py --format json`
- 手动验证：
  - 检查 branch protection 与文档口径一致
  - 检查状态面能展示 latest guardian verdict 与 worktree 映射

## TDD 范围

- 先写测试的模块：
  - workflow guard
  - worktree 创建与复用
  - 状态面聚合与 legacy 兼容
  - open_pr 前置准入
- 暂不纳入 TDD 的模块与理由：
  - 需要真实 GitHub / Codex 认证环境的命令交互，仅保留 smoke test 与手动验证

## 并行 / 串行关系

- 可并行项：
  - 文档契约重构
  - 新入口脚本实现
  - 治理测试补齐
- 串行依赖项：
  - workflow contract 先稳定，再接入 guard 与 hooks
  - 状态路径迁移完成后再做合并门禁回归
- 阻塞项：
  - 缺少 `gh` / `codex` 认证
  - 仓库侧权限不足导致设置同步失败

## 进入实现前条件

- [x] `spec review` 输入已形成并进入版本控制
- [x] 关键风险已记录并有缓解策略
- [x] 关键依赖可用
- [ ] v2 文档契约通过 `workflow_guard`
- [ ] repo harness 新入口通过治理测试
- [ ] guardian 对当前 `head SHA` 给出 `APPROVE`
- [ ] 当前 PR 满足 `merge-ready` 条件
