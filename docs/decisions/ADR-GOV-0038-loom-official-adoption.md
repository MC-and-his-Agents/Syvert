# ADR-GOV-0038: 正式引入 Loom governance runtime

## 关联信息

- Issue：`#258`
- item_key：`GOV-0038-loom-official-adoption`
- item_type：`GOV`
- release：`governance-baseline`
- sprint：`loom-official-adoption`

## Status

Accepted

## Context

Loom 已完成 Syvert reverse-consumption smoke 与 runtime parity release judgment。结论是：Loom 可以承接 Syvert 的通用强治理能力，但 Syvert 仍需要保留 repo-specific profile / residue。

Syvert 当前仍在本仓库内维护大量通用治理解释，包括 Work Item admission、gate chain、status surface、closeout / reconciliation 与 GitHub binding 语义。这些能力已经进入 Loom core 与 GitHub profile，继续平行维护会增加漂移风险。

## Decision

Syvert 正式引入 Loom 作为上游 governance runtime 与 canonical governance layer。

本轮采用 Loom `v1.3` 已验证的 vendored runtime 形态：提交 `.loom/bin/*`、`.loom/bootstrap/*` 与 `.loom/companion/*`。这样可以满足当前 `loom_init verify` 对 bootstrapped target runtime 的合同要求。

Syvert 文档不删除既有治理栈，而是把通用治理语义降级为 Loom 指向，并保留 Syvert-specific residue。

## Retained Syvert Residue

- 产品使命、vision、roadmap。
- release / sprint / item_key 业务上下文。
- Syvert guardian 实现与 head SHA 绑定策略。
- `scripts/policy/integration_contract.json` 与 `scripts/integration_contract.py`。
- adapter/runtime/resource lifecycle 业务实现。
- Syvert issue/template 命名与历史 exec-plan 证据。

## Consequences

- Loom-on-Syvert runtime parity 可以在 Syvert main 上直接验证。
- Syvert 后续不应再扩写跨仓通用治理模型；新增通用治理能力应优先进入 Loom。
- `.loom/bin/*` 是当前兼容性选择，存在随 Loom runtime 升级而漂移的维护成本。
- 后续可以在 Loom 支持 external-runtime companion 后，另开迁移事项将 Syvert 从 vendored runtime 降级为 external runtime carrier。

## Validation

- `python3 /Users/mc/dev/Loom/tools/loom_init.py verify --target /Users/mc/dev/syvert-official-loom`
- `python3 /Users/mc/dev/Loom/tools/loom_flow.py governance-profile status --target /Users/mc/dev/syvert-official-loom`
- `python3 /Users/mc/dev/Loom/tools/loom_flow.py runtime-parity validate --target /Users/mc/dev/syvert-official-loom`
- `python3 /Users/mc/dev/Loom/tools/loom_flow.py shadow-parity --target /Users/mc/dev/syvert-official-loom`
- `python3 /Users/mc/dev/Loom/tools/loom_flow.py shadow-parity --target /Users/mc/dev/syvert-official-loom --blocking`
- `python3 /Users/mc/dev/Loom/tools/loom_flow.py flow resume --target /Users/mc/dev/syvert-official-loom --item INIT-0001`
