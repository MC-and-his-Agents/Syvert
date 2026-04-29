# FR-0021 risks

| 风险 | 影响 | 缓解 | 回滚 |
| --- | --- | --- | --- |
| provider port 被建模成 Core-facing provider SDK | Core 会开始感知站点/工具 provider，破坏 Core / Adapter 边界 | formal spec 固定 provider port 为 adapter-owned internal boundary，并在 `#269` 测试 registry / Core 不暴露 provider 字段 | revert provider SDK / Core registry 相关增量 |
| native provider 拆分改变当前 `content_detail_by_url` 行为 | 双参考 adapter baseline 失效，`v0.7.0` 范围从稳定化变成行为变更 | `#269` 保持 Adapter surface、constructor hooks、raw / normalized result 兼容；`#271` 单独跑 evidence | revert runtime split，回到当前内嵌逻辑 |
| 外部 provider 接入被混入 `v0.7.0` | 范围失控，提前引入 provider selector、fallback 与外部依赖 | spec 明确 WebEnvoy / OpenCLI / bb-browser / agent-browser 不在范围；后续必须另建 FR | 拆出独立后续 FR，撤销外部 provider 代码 |
| 新站点能力借 provider port 名义落地 | 小红书/抖音 capability approval 被绕过 | spec 固定当前只覆盖 `content_detail_by_url` approved slice | revert 新 capability 相关文档/代码/测试 |
| provider result 承担 normalized result | Adapter 目标系统语义被 provider 替代，后续 provider 兼容性边界混乱 | data model 固定 provider result 只含 raw payload 与 platform detail object | 将 normalized 逻辑移回 Adapter |
| 现有测试 seam 被破坏 | 大量 adapter 回归失效，拆分成本扩大 | 要求 legacy constructor transport hooks 与 default helper import path 保持兼容 | re-export helper 或恢复 constructor 参数 |

## Review checklist

- [ ] Core / registry / TaskRecord / resource lifecycle 没有 provider 字段
- [ ] 没有外部 provider 接入
- [ ] 没有新增小红书/抖音业务能力
- [ ] 没有新增资源类型或 provider resource supply model
- [ ] Adapter public metadata 保持兼容
- [ ] normalized result 仍由 Adapter 生成
- [ ] 双参考回归证据在 `#271` 中可追溯
