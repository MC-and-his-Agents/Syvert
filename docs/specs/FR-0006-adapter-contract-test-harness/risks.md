# FR-0006 风险清单

## 风险项

| 风险 | 影响 | 缓解策略 | 回滚策略 |
| --- | --- | --- | --- |
| fake adapter 语义膨胀为平台影子实现 | harness 复杂度失控，FR 边界漂移到真实平台测试 | formal spec 限定 fake adapter 只承载 contract 所必需的最小行为；实现审查时拒绝引入真实平台前置 | 回退超范围样例或 fake adapter 行为，把实现收缩回受控 contract 样例 |
| harness 通过绕过标准 adapter 宿主路径获取“绿色结果” | 无法证明 Core 真正承载统一 adapter contract | formal spec 要求 fake adapter 通过与真实 adapter 同类的宿主/发现入口进入 Core；实现验证必须覆盖标准执行路径 | 回退绕过宿主路径的实现，恢复到统一 adapter 执行入口 |
| contract violation 与合法失败 envelope 混淆 | 验证结论失真，后续实现无法准确归因 | 验证工具输出至少区分通过、contract violation、执行前置失败；实现测试覆盖三类最小分支 | 回退结果分类改动，恢复上一版稳定判定逻辑 |
| 将真实平台回归或版本 gate 语义写入 harness 主体 | 本 FR 与相邻事项交叉污染，后续 PR 范围失控 | spec 中显式排除真实平台测试、双参考适配器回归与版本门禁编排 | 回退超范围文档或实现，拆回独立后续事项 |

## 合并前核对

- [x] 高风险项已有缓解策略
- [x] 回滚路径可执行
