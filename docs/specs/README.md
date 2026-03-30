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

## 事项身份与命名

- `docs/specs/` 中的事项默认使用 `item_key` 作为聚合键。
- FR 目录命名固定为：`FR-XXXX-<slug>`
- 其他事项类型使用统一 `item_key` 规范：`HOTFIX-XXXX-<slug>`、`GOV-XXXX-<slug>`、`CHORE-XXXX-<slug>`
- `XXXX` 为四位数字，`slug` 使用短横线英文短语
- 从 PR2 起，新事项必须在 formal spec、`TODO.md`、`exec-plan`、PR 描述中显式声明同一个 `item_key`
- 历史事项允许沿用既有目录或文件名，不要求在 PR2 中全量迁移
- formal spec 可通过统一 `item_key` 与 `exec-plan`、decision、PR 关联

## 聚合而不嵌套

- `docs/specs/` 只承载正式规约，不与 `exec-plan`、`decision` 混放在同一个事项目录中。
- `release` / `sprint` 信息通过横向索引与 `item_key` 关联，不作为正式规约事实源。
