# Syvert 正式规约区

`docs/specs/` 是正式规约区，不是 backlog 草稿区。

## 适用范围

- 核心事项默认进入正式规约流程
- 中等事项在触及共享契约、共享数据模型或高风险链路时升级到正式规约
- `FR` 是事项类型之一；formal spec 默认围绕 `FR` 组织

## 最小套件

每个 FR 目录至少包含：

- `spec.md`
- `plan.md`
- `TODO.md`

模板见 [./_template](./_template)。

## 可选增强（按触发条件）

- `contracts/`：存在稳定接口或跨进程协议
- `data-model.md`：引入或修改持久化/共享实体
- `risks.md`：涉及安全、账号、写入、迁移、并发或不可逆动作
- `research.md`：存在关键未知项，需要显式记录研究结论

## 审查规则

- 正式规约的审查标准见 [../../spec_review.md](../../spec_review.md)
- 实现 PR 审查标准见 [../../code_review.md](../../code_review.md)
- 交付流程见 [../process/delivery-funnel.md](../process/delivery-funnel.md)

## 命名建议

- 目录命名建议：`FR-XXXX-<slug>`
- `XXXX` 为四位数字，`slug` 使用短横线语义短语
- formal spec 可通过统一 `item_key` 与 `exec-plan`、decision、PR 关联
