# GOV-0028 执行计划

## 关联信息

- item_key：`GOV-0028-harness-compat-migration`
- Issue：`#57`
- item_type：`GOV`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`无（治理文档事项）`
- 关联 decision：`docs/decisions/ADR-0003-github-delivery-structure-and-repo-semantic-split.md`
- 关联 PR：`#60`
- active 收口事项：`GOV-0028-harness-compat-migration`

## 目标

- 让 repo harness、guard、template 与 review 输入适配新的 `Phase -> FR -> Work Item` 治理契约。
- 让 harness、guard、template 与 review 输入优先消费 active `exec-plan`、bootstrap contract 与当前 Work Item 上下文，而不是继续混写到 GitHub 调度层。
- 在不改动 `FR-0003` formal spec 套件契约的前提下，收敛当前 PR 的治理实现范围，并保留对既有 `TODO.md` 的读取 / 回写兼容。

## 范围

- 本次纳入：
  - `scripts/policy/policy.json`
  - `scripts/context_guard.py`
  - `scripts/open_pr.py`
  - `scripts/item_context.py`
  - `scripts/workflow_contract.py`
  - `WORKFLOW.md`
  - `docs/AGENTS.md`
  - `docs/decisions/ADR-0003-github-delivery-structure-and-repo-semantic-split.md`
  - `docs/exec-plans/GOV-0027-governance-contract-rewrite.md`
  - `docs/process/agent-loop.md`
  - `docs/specs/README.md`
  - `docs/exec-plans/README.md`
  - `spec_review.md`
  - `code_review.md`
  - `tests/governance/test_spec_guard.py`
  - `tests/governance/test_context_guard.py`
  - `tests/governance/test_item_context.py`
  - `tests/governance/test_open_pr.py`
  - `tests/governance/test_workflow_guard.py`
  - 本 exec-plan
- 本次不纳入：
  - 删除任何现有 `TODO.md`
  - 大规模改写存量 `exec-plan`
  - 新增项目管理状态页面
  - 任何业务实现代码

## 当前停点

- 最近一次显式实现 checkpoint 对应提交 `f5848d04e09f6bae4a709243ab56849698c7f5e3`。该 checkpoint 已完成第二轮 guardian 收口：bootstrap contract 只接受真实 `docs/decisions/*.md` 决策文档，重复 decision metadata fail-closed，`context_guard` / `open_pr` 对 formal-spec suite scope 使用同一条 fail-closed 规则，且 legacy FR / HOTFIX code-only 实现 PR 已恢复 formal-input 兼容路径。
- 当前工作树在上述 checkpoint 之后补做最终范围收敛：一是撤回本 PR 对 formal spec 最小套件与 `TODO.md` required/optional 语义的改写；二是把 `FR-0003/TODO.md` 与模板 `TODO.md` 的变更从当前 diff 中移出，避免再碰 canonical formal-spec 套件；三是把 `context_guard` 的 formal-spec 授权检查升级为 diff 级校验，阻止在 PR 创建后再夹带无关 FR 套件。
- 当前已解决本轮全部已知阻断：
  - `context_guard` 不再把 bootstrap decision 完整性错误施加到所有 touched `exec-plan`
  - `open_pr` 的 bootstrap fallback 已收紧到“当前事项自己的 active exec-plan + 关联 decision”
  - `open_pr` 的 formal-spec 绑定校验已收紧：一旦 PR 触碰 formal spec 目录，只允许命中当前绑定 suite，且不得混入其他 FR 套件
  - `bootstrap contract` 现在只接受真实 `docs/decisions/*.md` 决策文档，重复 decision metadata 会 fail-closed
  - `context_guard` 已同步 enforce formal-spec suite scope：绑定 suite 与 touched suite 不一致时直接报错
  - legacy FR / HOTFIX 的 code-only 实现 PR 已恢复兼容：已有且有效的本地 formal spec 套件可直接作为 formal input
  - `docs/specs/README.md` 不再把当前 Work Item 完整上下文写成 formal spec 必需输入
  - `docs/specs/README.md` 与 `docs/exec-plans/README.md` 已明确：formal spec 绑定 FR `item_key`，active `exec-plan` 绑定当前 Work Item `item_key`
- 当前待办只剩推送包含最终范围收敛与 diff 级 formal-spec 校验的当前 head，并在该同一 head 上重新运行 guardian / merge gate。

## 下一步动作

- 推送包含本次 exec-plan 对齐的 PR `#60` 最新 head，并核对该 head 对应的 GitHub checks。
- 运行 guardian / merge gate；若结论满足 `APPROVE + safe_to_merge=true` 且 checks 全绿，则通过受控入口合并。
- 合并后按分支/worktree 退役协议收口当前现场。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 的治理收敛回合提供可执行的 harness 契约，使 GitHub 单一调度层与仓内单一语义层在 guard、review 与恢复入口上真正对齐。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0003 / #55` 下的第二个治理 Work Item，负责把上一轮治理契约落到 harness、guard、template 与审查输入上。
- 阻塞：无外部阻塞；必须避免越界到 `#58` 的 legacy `TODO.md` 最终清理。

## 已验证项

- `python3 scripts/create_worktree.py --issue 57 --class governance`
- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`docs/process/agent-loop.md`
- 已核对 GitHub 真相：`#57 -> release=v0.2.0 -> sprint=2026-S15`
- `python3 -m unittest tests/governance/test_item_context.py tests/governance/test_spec_guard.py tests/governance/test_context_guard.py tests/governance/test_open_pr.py tests/governance/test_pr_scope_guard.py tests/governance/test_workflow_guard.py tests/governance/test_pr_guardian.py`
- `python3 scripts/spec_guard.py --all`
- `python3 scripts/context_guard.py`
- `python3 scripts/workflow_guard.py`
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
- `python3 scripts/open_pr.py --class governance --issue 57 --item-key GOV-0028-harness-compat-migration --item-type GOV --release v0.2.0 --sprint 2026-S15 --closing fixes --dry-run`
- 已确认 legacy placeholder `关联 spec：无（治理文档事项）` 会继续走当前事项自己的 bootstrap contract，不再误判为 formal spec 绑定
- 已创建 PR：`#60 https://github.com/MC-and-his-Agents/Syvert/pull/60`
- 已补齐 PR 描述中的 `fixes #57`、`refs #55`、`refs #54`、风险与验证说明
- 已确认 `open_pr` 对当前事项优先消费 active `exec-plan` 的绑定输入：`formal_spec` 模式只认当前 `关联 spec`，`bootstrap` 模式只认当前 `关联 decision`
- 已确认 `context_guard` 对 touched `exec-plan` 按输入模式施加校验：非 `GOV` unbound 路径不再被 bootstrap contract 误伤
- 已确认 bootstrap contract 不再接受 metadata-free ADR；`implementation` formal-input 不再依赖 GitHub title / label heuristics
- 已确认 README 示例链路不再把 FR `item_key` 与 Work Item `item_key` 混写成同一个聚合键

## 未决风险

- 若 review / guardian 仍把 formal spec 套件 contract 与执行回合 contract 混成一层，仍可能要求补充“当前 PR 不改 `required_files` / 不改 `FR-0003` formal-spec 套件”的显式说明。
- 若后续 `#58` 清理 PR 没有延续本轮的 legacy 兼容边界，可能误删仍被历史事项使用的 `TODO.md`。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对治理脚本、治理测试、workflow 与文档模板的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `f5848d04e09f6bae4a709243ab56849698c7f5e3`
