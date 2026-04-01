# GOV-0024 执行计划

## 关联信息

- item_key：`GOV-0024-guardian-review-context`
- Issue：`#24`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S14`
- 关联 spec：无（治理脚本事项）
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 关联 PR：`#28`
- active 收口事项：`GOV-0024-guardian-review-context`

## 目标

- 让 guardian reviewer prompt 优先消费结构化 review context，而不是整份 `code_review.md` 与原样 PR 模板正文。
- 拆开 reviewer rubric 与 merge gate 的消费位置，保持现有 guardian 输出 schema、head 绑定和受控 merge 安全性不变。
- 降低 review agent 重复读取治理文档、重复定位 `exec-plan` / decision / Issue / PR 摘要的成本。

## 范围

- 本次纳入：`scripts/pr_guardian.py`、必要的最小 review context helper、相关治理测试、本事项 `exec-plan`
- 本次不纳入：`.github/PULL_REQUEST_TEMPLATE.md`、`open_pr.py`、`merge_pr.py`、`governance_status.py` 的流程改造、`codex review` 内核迁移、#25 的模板/自动化适配

## 当前停点

- PR `#28` 已绑定 Issue `#24` 打开；Issue 摘要已准备冻结到 PR 正文，guardian 迭代阻断已收口到当前 head，当前停在等待最新一轮 GitHub checks、guardian 审查与受控 merge。

## 下一步动作

- 等待 GitHub checks 全绿，并复核最新 guardian 收口没有破坏 review context 契约与 merge gate 安全性。
- 执行 guardian 审查与 `merge_pr` 受控合并，必要时仅在本事项范围内修复阻塞。
- 合并后按分支退役协议清理本地/远端分支、worktree 与 stale state。

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
- 已完成最小改动文件：`scripts/pr_guardian.py`
- 已完成最小改动文件：`tests/governance/test_pr_guardian.py`
- 已完成最小改动文件：`docs/exec-plans/GOV-0024-guardian-review-context.md`
- `python3 -m unittest tests.governance.test_pr_guardian`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/open_pr.py --class governance --issue 24 --item-key GOV-0024-guardian-review-context --item-type GOV --release v0.1.0 --sprint 2026-S14 --title "refactor(governance): 精简 guardian review 上下文注入" --dry-run`
- 已确认 PR：`#28 https://github.com/MC-and-his-Agents/Syvert/pull/28`
- 已补齐 PR 描述中的范围、风险、验证、回滚与 #25 非目标说明
- 已补齐 PR 描述中的 `Issue 摘要` 冻结方案，避免 guardian reviewer 默认依赖远端 issue 漂移
- 已按 guardian 阻断反馈收口：trusted rubric 来源、Issue 摘要注入、模板关键信息保留、raw body fallback 收紧、item context 约束放宽
- 已补齐 trusted rubric source 正向回归测试，并将 Issue contract 注入条件固定为“缺少 `Issue 摘要` 时必须补充”
- 已补齐 guardian state 写入隔离、多 active exec-plan、PR preamble 保留等回归测试
- 已补齐 `Issue 摘要` 嵌套 `Goal/Scope` 段落的真实解析路径回归测试

## 未决风险

- 若 reviewer prompt 继续混入 merge gate 说明，会违背 #22 / #23 已收口的职责边界。
- 若为了复用状态面逻辑直接引入 `pr_guardian -> governance_status` 反向依赖，会形成循环导入。
- 若改动开始触及 PR 模板或更广泛自动化入口，会越界到 #25。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `scripts/pr_guardian.py`、相关测试与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `74c74f27b70b723625125983886cffab50f7a448`
