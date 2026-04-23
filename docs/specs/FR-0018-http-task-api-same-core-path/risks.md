# FR-0018 风险记录

| 风险 | 影响 | 缓解策略 | 回滚思路 |
| --- | --- | --- | --- |
| HTTP service 直接调用 adapter 或直接写 `TaskRecord` | API 与 CLI 语义分叉，破坏 same-core-path 与 durable truth | formal spec 显式禁止 adapter 直连、旁路写入与影子执行面 | 回滚越界实现/文档，恢复到 transport 仅做 ingress/egress 的最小 contract |
| API 重新定义 success/failed/result carrier | 调用方需要同时适配 CLI/Core/API 三套语义，shared contract 失效 | formal spec 明确要求终态继续复用 shared envelope，非终态结果只能走 `result_not_ready` 的 shared failed 语义 | 回滚 API 私有 envelope，恢复到共享 carrier |
| `status/result` 读取影子缓存而不是 durable `TaskRecord` | CLI 与 API 观察到的任务状态不一致，回归证据失真 | formal spec 明确 durable `TaskRecord` 是唯一状态/结果真相源，影子缓存不得替代查询 truth | 回滚影子查询路径，恢复到 durable store 回读 |
| transport 细节侵入共享 request / record contract | 认证、租户、RBAC 等超范围字段污染 Core shared model | formal spec 把 transport 身份/权限明确留在范围外，不提升为共享任务语义 | 回滚 transport 专属字段与叙述，恢复最小共享 contract |
| `result` 在非终态时返回伪造成功对象或空结果 | 调用方无法判定结果是否 ready，破坏状态与结果闭环 | formal spec 明确 `accepted/running` 只能返回 `result_not_ready` 的 shared failed 语义 | 回滚宽松结果语义，恢复到可判定非终态 contract |

## 合并前核对

- [x] API 与 CLI same-core-path / durable truth 边界已冻结
- [x] 终态 envelope 复用与 `result_not_ready` 非终态语义已冻结
- [x] adapter 直连、影子状态、影子结果与 transport 侵入共享模型的风险已记录
