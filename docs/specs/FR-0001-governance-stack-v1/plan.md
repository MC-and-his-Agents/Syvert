# FR-0001 实施计划

## 实施目标

- 为治理栈 v1 建立从正式输入、脚本实现到受控 merge 的完整闭环，并保证该闭环可被本地与 CI 回归验证。

## 分阶段拆分

- 阶段 1：收敛治理文档、正式规约模板与 policy 单一规则源。
- 阶段 2：落地 hook、CI、PR scope guard、spec guard、governance gate。
- 阶段 3：落地 `pr_guardian` / `merge_pr`，并把 guardian 审查与受控 merge 入口串起来。
- 阶段 4：补齐治理核心事项的 GitHub Issue、formal spec 与回归测试，收口 merge-ready 条件。

## 实现约束

- 不允许触碰的边界：
  - 不把平台特定实现写入治理栈
  - 不把 AI guardian 绑定进 GitHub-hosted CI
  - 不把 backlog / sprint 正文镜像回仓库
- 与上位文档的一致性约束：
  - merge gate 必须统一引用 `code_review.md`
  - 核心治理事项必须具备 Issue 与 formal spec 输入
  - `governance` 与 `implementation` 改动必须分离

## 测试与验证策略

- 单元测试：
  - `tests/governance/test_commit_check.py`
  - `tests/governance/test_docs_guard.py`
  - `tests/governance/test_pr_guardian.py`
  - `tests/governance/test_pr_scope_guard.py`
  - `tests/governance/test_spec_guard.py`
- 集成/契约测试：
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - `python3 scripts/pr_guardian.py review <pr-number> --post-review`
  - `python3 scripts/merge_pr.py <pr-number>`
- 手动验证：
  - 检查 PR body 已正确关联 Issue、Closing 语义与验证证据
  - 检查 branch protection 的 required checks 与仓库文档口径一致

## TDD 范围

- 先写测试的模块：
  - PR scope guard
  - spec guard
  - guardian verdict 复用与 merge gate 逻辑
- 暂不纳入 TDD 的模块与理由：
  - 需要真实 GitHub / Codex 认证环境的命令交互，仅保留 smoke test 与手动验证

## 并行 / 串行关系

- 可并行项：
  - 文档口径收敛
  - guard 单元测试补齐
  - GitHub 仓库手工设置核对
- 串行依赖项：
  - formal spec 与 Issue 先闭环，再确认当前治理 PR 满足正式输入要求
  - guardian 审查通过后，才能进入受控 merge
- 阻塞项：
  - 缺少 `gh` / `codex` 认证
  - guardian 对当前 PR 给出阻断性结论

## 进入实现前条件

- [x] `spec review` 输入已形成并进入版本控制
- [x] 关键风险已记录并有缓解策略
- [x] 关键依赖可用
- [ ] guardian 对当前 `head SHA` 给出 `APPROVE`
- [ ] 当前 PR 满足 `merge-ready` 条件
