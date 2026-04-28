# Spec

## Goal

- 将 Loom 作为 Syvert 的上游 governance runtime / canonical governance layer 正式引入 Syvert `main`。
- 提交可复验的 `.loom` carrier，使 Syvert 能在不删除现有治理栈的前提下消费 Loom 的 Work Item、status、review、merge checkpoint、runtime parity、shadow parity 与 closeout/reconciliation 语义。
- 明确 Syvert-owned residue 仍由 Syvert 维护：guardian、integration contract、release/sprint/item_key 语义、产品愿景与业务运行规则。

## Scope

- In scope:
  - 提交 `.loom/bootstrap/*`、`.loom/bin/*`、`.loom/companion/*`、`.loom/shadow/*`、`.loom/work-items/*`、`.loom/progress/*`、`.loom/status/*`、`.loom/reviews/*` 与 `.loom/specs/*` carrier。
  - 更新 Syvert `AGENTS.md`、`WORKFLOW.md`、`docs/process/delivery-funnel.md`、`docs/AGENTS.md`，声明 Loom consumption boundary。
  - 新增 ADR-GOV-0038，记录正式引入依据、保留 residue 与后续 de-vendor 风险。
  - 让 Syvert governance gate 对 `.loom/**` 做最小结构校验：Python 语法、JSON 语法、必需 locator、review/status/spec 一致性与消费侧 Loom validation chain。
  - 修复 vendored `.loom/bin` 中影响正式使用的 GitHub remote / branch REST 读取边界。
- Out of scope:
  - 不删除 Syvert `AGENTS.md`、`WORKFLOW.md`、guardian、release/sprint 或 integration contract。
  - 不把 Syvert guardian、integration contract、release/sprint 迁移进 Loom core。
  - 不把 Syvert PR template 替换为 Loom template；只保留 Loom-compatible locator/sections。
  - 不引入 external-runtime companion 或 de-vendor，本轮使用 vendored `.loom/bin` 以满足 Loom v1.3 verify contract。

## Key Scenarios

### Scenario 1

Given
- Syvert `main` 已包含 repo-native guardian、integration contract 与 release/sprint 语义。
- Loom carrier 以 vendored `.loom/bin` 和 `.loom/companion` 形式进入仓库。

When
- 维护者运行 `python3 .loom/bin/loom_init.py verify --target .`、`python3 .loom/bin/loom_flow.py governance-profile status --target .`、`python3 .loom/bin/loom_flow.py runtime-parity validate --target .`、`python3 .loom/bin/loom_flow.py shadow-parity --target .` 与 `python3 .loom/bin/loom_flow.py shadow-parity --target . --blocking`。

Then
- Loom runtime 返回 pass，并把 Syvert 识别为 strong governance profile。
- Syvert-owned residue 不被 Loom 覆盖或降级。

### Scenario 2

Given
- `.loom/**` 被 Syvert policy 归类为 governance scope。

When
- PR 修改 `.loom/bin/*.py`、`.loom/**/*.json`、review/status/spec carrier 或 companion locator。

Then
- `scripts/governance_gate.py --mode ci` 必须校验 `.loom` 必需文件、JSON 语法、Python 语法、work item/status/progress/review/spec/shadow 的最小静态一致性。
- runtime parity、shadow parity 与 merge checkpoint 由消费侧验证链 `loom_init verify -> governance-profile status -> runtime-parity validate -> shadow-parity -> shadow-parity --blocking` 与 merge-ready/checkpoint 命令共同验证，不再把源仓 `loom_check` 作为正式 adoption gate。

### Scenario 3

Given
- GitHub remote 使用合法 dotted repo name，例如 `owner/foo.bar.git`。
- 默认分支包含 `/`，例如 `release/main`。

When
- Loom vendored runtime 读取 GitHub control plane。

Then
- repo parser 返回 `owner/foo.bar`。
- branch REST path 使用 URL encoding，不把 `release/main` 误拆成路径段。

## Exceptions And Boundaries

- Failure modes:
  - `.loom/bin` Python 语法错误必须由 Syvert governance gate 阻断。
  - `.loom/**/*.json` 无法解析必须由 Syvert governance gate 阻断。
  - `.loom` merge checkpoint fallback/block 必须由消费侧验证链与 `flow merge-ready` / `checkpoint merge` 阻断。
  - GitHub control-plane 读取失败时，Loom 返回 host-signal/binding failure，不自动降级为已通过。
- Operational boundaries:
  - Syvert guardian 仍是 repo-native merge gate。
  - `scripts/policy/integration_contract.json` 仍是 integration contract 真相源。
  - release / sprint / item_key 仍是 Syvert repo-specific context。
- Rollback or fallback expectations:
  - 若 `.loom` carrier 在 Syvert 上产生不可接受的维护成本，可以通过后续 PR 降级为 external-runtime companion；本 PR 不直接删除 vendored runtime。
  - 若 GitHub host signal 不可读，closeout 和 merge-ready 必须 fallback/block，而不是假定 pass。

## Acceptance Criteria

- [x] Loom carrier 在 Syvert worktree 中通过 `loom_init verify`。
- [x] `governance-profile status` 返回 strong governance profile。
- [x] `runtime-parity validate` 返回 pass。
- [x] `shadow-parity --blocking` 返回 pass。
- [x] `checkpoint merge --item INIT-0001` 返回 pass。
- [x] Syvert governance gate 覆盖 `.loom/**` 结构校验。
- [x] Dotted GitHub repo name 与 slash default branch 有回归测试。
- [x] Syvert-owned guardian、integration contract、release/sprint residue 保持 repo-native authority。
