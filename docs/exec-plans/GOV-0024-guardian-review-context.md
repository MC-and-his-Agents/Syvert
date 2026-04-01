# GOV-0024 执行计划

## 关联信息

- item_key：`GOV-0024-guardian-review-context`
- Issue：`#24`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S14`
- 关联 spec：无（治理脚本事项）
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 关联 PR：待补充
- active 收口事项：`GOV-0024-guardian-review-context`

## 目标

- 让 guardian reviewer prompt 优先消费结构化 review context，而不是整份 `code_review.md` 与原样 PR 模板正文。
- 拆开 reviewer rubric 与 merge gate 的消费位置，保持现有 guardian 输出 schema、head 绑定和受控 merge 安全性不变。
- 降低 review agent 重复读取治理文档、重复定位 `exec-plan` / decision / worktree / checks 的成本。

## 范围

- 本次纳入：`scripts/pr_guardian.py`、必要的最小 review context helper、相关治理测试、本事项 `exec-plan`
- 本次不纳入：`.github/PULL_REQUEST_TEMPLATE.md`、`open_pr.py`、`merge_pr.py`、`governance_status.py` 的流程改造、`codex review` 内核迁移、#25 的模板/自动化适配

## 当前停点

- 已确认 `main` 包含 #22 与 #23；Issue `#24` 已创建独立 worktree，当前进入 guardian review context 冗余梳理与最小实现阶段。

## 下一步动作

- 在 `scripts/pr_guardian.py` 中抽出结构化 review context 构建逻辑。
- 用最小关键规则替代整份 `code_review.md` 注入，并保留 reviewer 必需的 rubric 语义。
- 补齐 prompt/context builder 与 merge gate 回归测试，验证后通过受控入口推进 PR、guardian 与 merge。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 治理基线收紧 guardian 的审查输入边界，减少 reviewer 上下文噪音，同时不削弱受控合并安全闭环。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：父事项 `#21` 下承接 #22 / #23 的治理脚本收口项，负责把“最小必要上下文”真正落实到 guardian reviewer prompt。
- 阻塞：无外部阻塞；需严格避免越界到 #25 的 PR 模板/自动化入口对齐。

## 已验证项

- `gh issue view 24 --repo MC-and-his-Agents/Syvert`
- `git fetch origin --prune`
- 已确认 `main` 与 `origin/main` 一致，且包含 #22 / #23 后续主线提交
- `python3 scripts/create_worktree.py --issue 24 --class governance`
- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/agent-loop.md`
- 已阅读：`docs/process/worktree-lifecycle.md`
- 已阅读：`docs/process/branch-retirement.md`
- 已阅读：`code_review.md`
- 已阅读：`scripts/pr_guardian.py`
- 已阅读：`scripts/governance_status.py`
- 已阅读：`tests/governance/test_pr_guardian.py`

## 未决风险

- 若 reviewer prompt 继续混入 merge gate 说明，会违背 #22 / #23 已收口的职责边界。
- 若为了复用状态面逻辑直接引入 `pr_guardian -> governance_status` 反向依赖，会形成循环导入。
- 若改动开始触及 PR 模板或更广泛自动化入口，会越界到 #25。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `scripts/pr_guardian.py`、相关测试与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `772e2d34e1f2f9ee7321e0b50fcfbdeee0145df6`
