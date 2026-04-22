# FR-0013 执行计划（requirement container）

## 关联信息

- item_key：`FR-0013-adapter-resource-requirement-declaration`
- Issue：`#189`
- item_type：`FR`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 spec：`docs/specs/FR-0013-adapter-resource-requirement-declaration/`
- 关联 PR：`#200`
- 状态：`inactive requirement container`

## 说明

- `FR-0013` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- 当前 formal spec closeout 由 `docs/exec-plans/CHORE-0138-fr-0013-formal-spec-closeout.md` 承担，当前受审 PR 为 `#200`；formal spec 收口、review-sync 与后续 PR 元数据必须统一回写到该 Work Item，而不是在 requirement container 中混入执行态细节。
- `FR-0013` 只冻结 `AdapterResourceRequirementDeclaration` 的最小声明 contract：`adapter_key`、`capability`、`resource_dependency_mode`、`required_capabilities[]`、`evidence_refs[]`，以及它与 `FR-0015` 已批准共享能力词汇 / 共享证据之间的绑定关系。
- `FR-0013` 不重写 `FR-0010` 的资源生命周期主 contract，也不重写 `FR-0012` 的 Core 注入 bundle 与 Adapter 资源边界；后续实现 Work Item 只能消费这些既有边界之上的声明层 contract。
- `FR-0013` 不得被 `FR-0014`、`FR-0015` 反向改写主语义；若后续事项需要扩张声明 carrier、共享能力词汇或共享证据真相，必须通过新的 formal spec 显式推进，而不是在相邻 FR 中侧写回填。
- 当前 formal spec 只服务 `v0.5.0` 的“在双参考适配器共同语义下声明资源依赖”目标；`preferred_capabilities`、`optional_capabilities`、`fallback`、`priority`、`provider_selection` 以及 Playwright/CDP/Chromium 一类技术字段都不属于本 FR。
- 当前分支已形成最新 formal spec 语义 checkpoint `1199c85cfeb57c9f8d6a17f3c4ba70f44cca25e6`；其后若只追加当前受审 PR、checks 或 checkpoint metadata，只作为 review-sync follow-up，不改写 requirement 语义。

## 最近一次 checkpoint 对应的 head SHA

- `1199c85cfeb57c9f8d6a17f3c4ba70f44cca25e6`
