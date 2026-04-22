# FR-0013 Research

## 目的

- 本文只补充“声明面如何映射到 `FR-0015` 共享证据”，不另建第二套证据真相，不重述 runtime 或 adapter 实现细节。

## `FR-0015` 共享事实映射

- `FR-0015` 已批准的共享能力词汇只有：
  - `account`
  - `proxy`
- `FR-0015` 已批准的双参考适配器共享声明基线只有：
  - `xhs + content_detail -> required [account, proxy]`
  - `douyin + content_detail -> required [account, proxy]`
- 因此 `FR-0013` 的 `required_capabilities[]` 只能引用 `account`、`proxy`，且当前 baseline declaration 不得出现第三个共享能力值。

## 声明 carrier 与共享证据的关系

- `AdapterResourceRequirementDeclaration.evidence_refs[]` 的作用不是描述“为什么觉得这样合理”，而是把每条声明绑定到 `FR-0015` 已批准共享证据。
- `FR-0013` 不生产新的 evidence truth；它只消费 `FR-0015` 已批准共享证据，并要求声明 carrier 对这些证据保持稳定引用。
- 若后续出现新的共享能力或新的共享声明基线，必须先在 `FR-0015` 或新的 formal spec 中被批准，再由 `FR-0013` 的后继事项受控消费。

## 当前 formal contract 的直接结论

- `resource_dependency_mode=required` 的 baseline declaration 只能落在：
  - `xhs / content_detail / [account, proxy]`
  - `douyin / content_detail / [account, proxy]`
- `resource_dependency_mode=none` 必须被 carrier 允许，是为了给未来经共享证据批准后的非资源路径保留 canonical 表达；它不是当前双参考适配器 baseline 已验证出的主路径。
- 任何想把 provider、技术栈、fallback、优先级写进 declaration 的诉求，都不属于“共享证据映射”，而属于另一个 formal spec 议题。
