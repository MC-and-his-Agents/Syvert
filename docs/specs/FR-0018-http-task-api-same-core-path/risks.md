# FR-0018 风险记录

| 风险 | 影响 | 缓解策略 | 回滚思路 |
| --- | --- | --- | --- |
| HTTP service 直接调用 adapter 或直接写 `TaskRecord` | API 与 CLI 语义分叉，破坏 same-core-path 与 durable truth | formal spec 显式禁止 adapter 直连、旁路写入与影子执行面 | 回滚越界实现/文档，恢复到 transport 仅做 ingress/egress 的最小 contract |
| API 重新定义 success/failed/result carrier | 调用方需要同时适配 CLI/Core/API 三套语义，shared contract 失效 | formal spec 明确要求终态继续复用 shared envelope，非终态结果只能走 `result_not_ready` 的 shared failed 语义 | 回滚 API 私有 envelope，恢复到共享 carrier |
| HTTP 把整个 `platform` category 粗暴视为 retryable，或自行放宽 idempotency safety gate | 非幂等任务被错误重试，控制面与业务面边界漂移 | formal spec 明确 retryable predicate 仅限 `execution_timeout` 或 `error.category=platform && error.details.retryable=true`，且必须继续通过共享 `ExecutionControlPolicy` gate | 回滚 transport 私有重试逻辑，恢复共享 retry 判定 |
| `execution_timeout`、closeout failure、control-state failure 被 HTTP 重新分类 | 调用方无法区分平台瞬态失败与共享真相损坏，后续自动化判断失真 | formal spec 明确 `execution_timeout` 继续投影为 `platform + error.details.control_code=execution_timeout`；closeout/control-state failure 固定为 `runtime_contract` | 回滚错误重分类逻辑，恢复共享分类 truth |
| pre-accepted concurrency rejection 被错误地视为已提交任务 | 客户端误以为存在 durable history，造成重复查询与错误恢复动作 | formal spec 明确该分支投影 `invalid_input`，且无 `TaskRecord` | 回滚 receipt/记录写入逻辑，恢复 pre-accepted fail-closed 语义 |
| post-accepted retry reacquire rejection 改写上一已完成 attempt 的终态 | durable history 被覆盖，导致任务历史与 closeout truth 不可信 | formal spec 明确该 rejection 只能写入 `ExecutionControlEvent/details`，不得改写上一已完成 attempt 的 `error.code/category` | 回滚错误的终态覆盖逻辑，恢复 append-only 控制事实 |
| `status/result` 读取影子缓存而不是 durable `TaskRecord`，或吞掉 `runtime_result_refs` | CLI 与 API 观察到的任务状态、结果与观测证据不一致，回归证据失真 | formal spec 明确 durable `TaskRecord` 是唯一状态/结果真相源，`runtime_result_refs` 必须继续透传 | 回滚影子查询路径与字段裁剪，恢复 durable store 回读 |
| transport 细节侵入共享 request / record contract | 认证、租户、RBAC 或 transport 私有控制字段污染 Core shared model | formal spec 把 transport 身份/权限与私有控制 DSL 明确保留在范围外，不提升为共享任务语义 | 回滚 transport 专属字段与叙述，恢复最小共享 contract |

## 合并前核对

- [x] API 与 CLI same-core-path / durable truth 边界已冻结
- [x] 终态 envelope 复用与 `result_not_ready` 非终态语义已冻结
- [x] `ExecutionControlPolicy` 默认值、retryable predicate 与 pre-accepted failure 边界已冻结
- [x] `execution_timeout`、closeout/control-state failure 与 post-accepted reacquire rejection 的分类风险已记录
- [x] adapter 直连、影子状态、影子结果、观测裁剪与 transport 侵入共享模型的风险已记录
