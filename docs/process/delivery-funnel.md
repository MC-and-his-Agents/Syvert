# Syvert 交付漏斗

Syvert 的唯一默认交付路径如下：

`Roadmap / 阶段目标 -> GitHub backlog -> 候选项 -> spec / contract -> spec review -> implementation PR -> PR review -> squash merge`

## 阶段解释

1. `Roadmap / 阶段目标`
   - 先确认事项是否属于当前阶段边界
   - 确认事项服务的 `release` 目标
2. `GitHub backlog`
   - 在 GitHub Issues / Projects 中确认事项本体、状态和优先级
   - `release` 与 `sprint` 语义来自执行绑定，不在仓库内维护状态镜像
3. `候选项`
   - 明确事项属于轻量事项、中等事项或核心事项
   - 明确事项在当前 `sprint` 中的角色：阻塞项、并行项或收尾项
4. `spec / contract`
   - 核心事项必须先形成正式规约或等价契约工件
   - 若事项本身是在 `main` 首次建立治理/规约基础设施，可暂以 `Issue + decision + exec-plan` 形成 bootstrap contract
5. `spec review`
   - reviewer 根据 [spec_review.md](../../spec_review.md) 的 rubric 收口边界、风险、验收与进入实现前条件
   - review 输入优先采用当前事项所需的最小必要上下文，不默认要求审查器重复探索整仓历史
6. `implementation PR`
   - 在独立分支上推进实现，不直推 `main`
7. `PR review`
   - reviewer 根据 [code_review.md](../../code_review.md) 的 rubric 判断阻断项、风险、验证充分性与是否达到 `merge-ready` 质量
   - review 输入优先采用当前事项所需的最小必要上下文，不默认要求审查器重复探索整仓历史
8. `squash merge`
   - 只有满足 [code_review.md](../../code_review.md) 定义的 merge gate，并通过受控入口校验后，才可 Squash Merge
   - 合并后若源分支不再承担活跃事项，应进入分支归档/退役流程

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

## 事项上下文绑定

- 每个进入执行回合的事项必须绑定：`Issue`、`item_key`、`item_type`、`release`、`sprint`
- `Issue` 仍是任务状态真相源的入口；`item_key`、`release`、`sprint` 只用于执行、恢复与交付映射
- 新事项与新长任务必须显式声明完整事项上下文；存量事项可在进入新的执行回合时补齐
- `item_type` 当前约定为：`FR` / `HOTFIX` / `GOV` / `CHORE`
- `item_key` 固定命名为 `<item_type>-<4-digit>-<slug>`

## 与自动化门禁的关系

- `commit-msg` hook 与 `commit-check` CI：保证中文 Conventional Commits
- `docs-guard`：保证 Markdown 链接、仓内路径引用和治理脚本基础可用
- `spec-guard`：保证正式规约区结构与边界不漂移
- `workflow-guard`：保证 `WORKFLOW.md` 与必需流程文档结构合法
- `governance-gate`：保证治理脚本、测试和 workflow 本身可回归
- reviewer：根据 rubric 判断实现或规约是否存在阻断问题
- `pr_guardian`：针对当前 PR head 执行合并前审查，产出 `verdict` 与 `safe_to_merge`
- `merge_pr`：消费 guardian 结论、checks 与 head 一致性，执行受控 merge

## 审查职责分层

- reviewer
  - 负责：基于 rubric 做实质审查，识别阻断项、风险与验证缺口
  - 不负责：替代 CI 执行自动化检查；替代 `merge_pr` 执行合并
- guardian
  - 负责：围绕当前 PR head 做 merge gate 审查，并绑定最新有效 `head SHA`
  - 不负责：替代 reviewer 定义或重写 rubric；替代 CI 跑自动化门禁
- CI
  - 负责：执行自动化检查、测试与结构校验
  - 不负责：替代 reviewer 给出语义审查结论；替代 guardian 给出 `safe_to_merge`
- merge gate
  - 负责：综合 guardian verdict、`safe_to_merge`、GitHub checks、PR 状态与 head 一致性，决定是否允许进入受控合并
  - 不负责：替代 reviewer rubric 判断实现/规约质量

## 最小必要上下文原则

- reviewer 与 guardian 默认只消费当前事项、当前 diff、当前 head 所需的最小必要上下文。
- 优先上下文包括：Issue、active `exec-plan`、相关 formal spec / bootstrap contract、PR 描述、风险与验证证据、与当前改动直接相关的流程文档。
- 若现有输入已足以判断，不应要求审查器无限制重复探索仓库历史或相邻事项。

## Repo Harness 补充

- 任务运行契约唯一来源：[WORKFLOW.md](../../WORKFLOW.md)
- 长任务协议唯一来源：[agent-loop.md](./agent-loop.md)
- workspace 生命周期唯一来源：[worktree-lifecycle.md](./worktree-lifecycle.md)
- 分支归档/退役唯一来源：[branch-retirement.md](./branch-retirement.md)
- 状态面统一读取 `$CODEX_HOME/state/syvert/`：
  - `guardian.json`
  - `review-poller.json`
  - `worktrees.json`
