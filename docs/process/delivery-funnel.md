# Syvert 交付漏斗

Syvert 的唯一默认交付路径如下：

`Roadmap / 阶段目标 -> GitHub backlog -> 候选项 -> spec / contract -> spec review -> implementation PR -> PR review -> squash merge`

## 阶段解释

1. `Roadmap / 阶段目标`
   - 先确认事项是否属于当前阶段边界
2. `GitHub backlog`
   - 在 GitHub Issues / Projects 中确认事项本体、状态和优先级
3. `候选项`
   - 明确事项属于轻量事项、中等事项或核心事项
4. `spec / contract`
   - 核心事项必须先形成正式规约或等价契约工件
   - 若事项本身是在 `main` 首次建立治理/规约基础设施，可暂以 `Issue + decision + exec-plan` 形成 bootstrap contract
5. `spec review`
   - 根据 [spec_review.md](../../spec_review.md) 收口边界、风险和验收
6. `implementation PR`
   - 在独立分支上推进实现，不直推 `main`
7. `PR review`
   - 根据 [code_review.md](../../code_review.md) 判断阻断项与 merge-ready 状态
8. `squash merge`
   - 只有满足 [code_review.md](../../code_review.md) 定义的 merge gate，并通过受控入口校验后，才可 Squash Merge

## 分流规则

- 轻量事项
  - 不强制正式 `spec`
  - 仍必须走分支、PR、review、squash merge
- 中等事项
  - 进入实现前必须冻结目标、影响面、验证方式与回滚方式
- 核心事项
  - 必须先建立正式 `spec` 套件并完成 `spec review`
  - 默认与实现 PR 分离
  - 治理 bootstrap 例外：在正式规约机制尚未落地前，可先按 bootstrap contract 进入 `governance` PR；PR 不得混入业务实现代码

## 与自动化门禁的关系

- `commit-msg` hook 与 `commit-check` CI：保证中文 Conventional Commits
- `docs-guard`：保证 Markdown 链接、仓内路径引用和治理脚本基础可用
- `spec-guard`：保证正式规约区结构与边界不漂移
- `workflow-guard`：保证 `WORKFLOW.md` 与必需流程文档结构合法
- `governance-gate`：保证治理脚本、测试和 workflow 本身可回归
- `pr_guardian` + `merge_pr`：保证 merge gate 不被裸命令绕过

## Repo Harness 补充

- 任务运行契约唯一来源：[WORKFLOW.md](../../WORKFLOW.md)
- 长任务协议唯一来源：[agent-loop.md](./agent-loop.md)
- workspace 生命周期唯一来源：[worktree-lifecycle.md](./worktree-lifecycle.md)
- 状态面统一读取 `$CODEX_HOME/state/syvert/`：
  - `guardian.json`
  - `review-poller.json`
  - `worktrees.json`
