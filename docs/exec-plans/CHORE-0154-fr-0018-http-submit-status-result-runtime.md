# CHORE-0154 FR-0018 HTTP submit/status/result runtime 执行计划

## 关联信息

- item_key：`CHORE-0154-fr-0018-http-submit-status-result-runtime`
- Issue：`#230`
- item_type：`CHORE`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 spec：`docs/specs/FR-0018-http-task-api-same-core-path/`
- 关联 decision：
- 关联 PR：`#245`

## 目标

- 在 `FR-0018` 已冻结边界内实现最小 HTTP endpoint surface：`submit`、`status`、`result`。
- HTTP transport 只负责 JSON ingress/egress、canonical method/path routing 与状态码映射。
- 任务执行、adapter 调用、durable `TaskRecord`、success / failed envelope 与结果回读全部复用既有 Core path。

## 范围

- 本次纳入：
  - `POST /v0/tasks`
  - `GET /v0/tasks/{task_id}`
  - `GET /v0/tasks/{task_id}/result`
  - stdlib WSGI adapter
  - endpoint / transport mapping tests
- 本次不纳入：
  - 生产认证、多租户、RBAC、控制台
  - query alias、批量查询、多任务复合路由、私有 result endpoint
  - `FR-0016/#224` execution-control runtime 本体
  - `FR-0017/#227` observability runtime 本体
  - `#231` CLI/API same-path evidence matrix

## 当前停点

- 已确认 `#230` 为 `v0.6.0` / `2026-S19` Work Item，父 FR 为 `#221`。
- 已确认当前主干没有 `packages/`、`apps/` 或现成 HTTP app 层，运行时入口集中在 `syvert/`。
- 已新增 `syvert/http_api.py`，提供薄 HTTP transport 与 WSGI app。
- 已新增 `tests/runtime/test_http_api.py`，覆盖 submit/status/result 与 WSGI routing 的最小 contract。
- 受控 worktree 已创建：`/Users/mc/code/worktrees/syvert/issue-230-fr-0018-http`，分支为 `issue-230-fr-0018-http`。
- guardian 首轮审查要求修复三项阻断：`submit` 请求形状改为 `target`、store root 不可用返回 `500 task_record_unavailable`、缺失 `task_id` 返回 `invalid_input`。三项均已修复并补测试。
- guardian 二轮审查要求继续修复两项阻断：HTTP transport 不得探测 `LocalTaskRecordStore.root` 内部字段、负数 `CONTENT_LENGTH` 必须在 ingress 阶段 fail-closed。已将 store root 可用性收敛到 `LocalTaskRecordStore.load()` 的共享 store contract，并补齐负数 `CONTENT_LENGTH` 测试。
- guardian 三轮审查要求补齐 `wsgi.input.read()` 抛出 `OSError` 时的 fail-closed JSON failed envelope；已修复并补测试。
- guardian 四轮审查要求补齐非法终态 `TaskRecord` / 非 JSON-safe envelope / percent-encoded slash `task_id` 的 fail-closed 分支；已复用共享 `TaskRecord` contract 校验并补测试。
- guardian 五轮审查要求补齐非法 record object、GET 路由错误 `task_id` 语义、public service 非字符串 `task_id` 的 fail-closed 分支；已修复为不伪造 task_id、不触碰非法 record 属性，并补测试。
- guardian 六轮审查指出 `execution_control_policy` 不应整体禁用；已新增共享 `ExecutionControlPolicy` carrier 与 HTTP 形状投影，合法 policy 进入 Core path，非法 policy 仍在 durable `accepted` 前 fail-closed。
- guardian 七轮审查指出 `concurrency.scope` 不得收窄为 `global`；已按 `FR-0016` contract 放开 `global`、`adapter`、`adapter_capability`，并补 HTTP 与 shared runtime 回归。
- guardian 八轮审查要求补齐错 key `TaskRecord`、`store.load()` 合同异常、`store.write()` / `mark_invalid()` 合同异常的 fail-closed 分支；已修复并补 HTTP / store runtime 回归。
- guardian 九轮审查要求补齐普通 store/load/write/mark_invalid 异常与不可 round-trip `task_id` receipt 的 fail-closed 分支；已修复并补测试。
- guardian 十轮审查要求在持久化前校验 HTTP path-safe `task_id`，并保留共享观测 refs；已改为 submit 前预生成/校验 task_id，`TaskRecord` / HTTP status/result 对已有 `runtime_result_refs`、`task_record_ref`、`execution_control_events` 做 JSON-safe 透传。
- guardian 十一轮审查未能 post 但本地 state 摘要指出 record-unavailable、result observability 与 `task_record_ref` 仍需补强；已将 `task_record_ref` 写入 durable TaskRecord / terminal envelope，并让 HTTP result 从 record-level refs 补齐可观测字段。
- guardian 十二轮审查要求补齐两项阻断：未显式携带 `execution_control_policy` 时必须物化共享默认 carrier，且 `TaskRecord.task_record_ref` 必须与 `task_id` 绑定一致；已在 Core normalize 阶段物化默认 policy，并在 TaskRecord 反序列化 / 校验阶段拒绝缺失或错绑 ref。
- guardian 十三轮审查要求保留旧 `TaskRecord` durable payload 的读取路径，并拒绝 terminal envelope 内嵌 observability truth 与 record 顶层 truth 冲突；已将缺失 `task_record_ref` 作为 legacy payload 在 load 时按 `task_id` 补齐，错绑仍 fail-closed，并校验 terminal envelope 中显式出现的 `task_record_ref`、`runtime_result_refs`、`execution_control_events` 必须与顶层 record truth 一致。
- guardian 十四轮审查要求 legacy terminal record 不仅可读，还必须可幂等回写；已在 `task_record_from_dict()` 加载旧终态 payload 时同步回填 `result.envelope.task_record_ref`，并补 `LocalTaskRecordStore.write(load(legacy_terminal))` 回归。
- guardian 十五轮审查要求 fail-closed recovery 不得因 malformed `TaskRecord.request` 二次崩溃，且 submit mismatch guard 必须保留 HTTP admission 预分配 `task_id`；已让 `_task_failure()` 只以安全反射读取 record identity，并在 mismatch failed envelope 中保留预分配 task_id，补 HTTP 回归。

## 下一步动作

- 等待 PR `#245` 最新 head CI / guardian 通过。
- 通过 `scripts/merge_pr.py` 执行受控 squash merge。
- 合入后同步主干事实、GitHub issue/project 状态并退役 implementation branch / worktree。

## 当前 checkpoint 推进的 release 目标

- 推进 `v0.6.0` 的 “HTTP + CLI through same Core path” 能力切片。
- 本事项只交付 HTTP endpoint runtime；完整 same-path regression evidence 留给 `#231`。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0018` 下游 implementation Work Item。
- 阻塞：`#231` 的 CLI/API same-path evidence 与 `#232` 的 parent closeout 依赖本事项先完成 endpoint runtime。

## 已验证项

- `git status --short --branch`
  - 结果：主工作区开始实现前位于 `main...origin/main` 且干净；权限恢复后已创建 `issue-230-fr-0018-http` 独立 worktree。
- `python3 scripts/create_worktree.py --issue 230 --class implementation`
  - 结果：通过，创建 `issue-230-fr-0018-http` worktree / branch，base SHA 为 `151a6ee9debebb07c77196ab44b9145f2a39becb`。
- `gh issue view 230 --json number,title,state,body,projectItems,url`
  - 结果：已确认 `#230` open，project 状态为 `Todo`，item_key / release / sprint 与本执行计划一致。
- `rg -n "FR-0018|HTTP transport|endpoint|status mapping" .`
  - 结果：已定位 `FR-0018` formal spec、contracts README、exec-plan 与 closeout evidence。
- `gh issue view 224` / `gh issue view 227`
  - 结果：`FR-0016` 与 `FR-0017` runtime implementation Work Item 仍为 open Todo；本事项不得实现其本体。
- `python3 -m unittest tests.runtime.test_http_api`
  - 结果：首轮通过 `Ran 16 tests`，`OK`；修复 guardian 一轮阻断后通过 `Ran 19 tests`，`OK`；修复 guardian 三轮阻断后通过 `Ran 21 tests`，`OK`；修复 guardian 四轮阻断后通过 `Ran 25 tests`，`OK`；修复 guardian 五轮阻断后通过 `Ran 29 tests`，`OK`；修复 guardian 六轮阻断后通过 `Ran 30 tests`，`OK`；修复 guardian 十二轮阻断后通过 `Ran 41 tests`，`OK`；修复 guardian 十三轮阻断后通过 `Ran 43 tests`，`OK`；修复 guardian 十五轮阻断后通过 `Ran 45 tests`，`OK`。
- `python3 -m unittest tests.runtime.test_http_api tests.runtime.test_task_record tests.runtime.test_runtime`
  - 结果：修复 guardian 十二轮阻断后通过，`Ran 118 tests`，`OK`；修复 guardian 十三轮阻断后通过，`Ran 121 tests`，`OK`。
- `python3 -m unittest tests.runtime.test_http_api tests.runtime.test_runtime`
  - 结果：修复 guardian 七轮阻断后通过，`Ran 89 tests`，`OK`。
- `python3 -m unittest tests.runtime.test_cli tests.runtime.test_task_record_store tests.runtime.test_runtime`
  - 结果：通过，`Ran 108 tests`，`OK`；修复 guardian 十二轮阻断后通过，`Ran 115 tests`，`OK`；修复 guardian 十四轮阻断后通过，`Ran 116 tests`，`OK`。
- `python3 -m unittest tests.runtime.test_http_api tests.runtime.test_task_record_store`
  - 结果：修复 guardian 二轮阻断后通过，`Ran 39 tests`，`OK`；修复 guardian 三轮阻断后通过，`Ran 40 tests`，`OK`；修复 guardian 八轮阻断后通过，`Ran 56 tests`，`OK`；修复 guardian 九轮阻断后通过，`Ran 61 tests`，`OK`。
- `python3 -m unittest tests.runtime.test_http_api tests.runtime.test_task_record_store tests.runtime.test_task_record`
  - 结果：修复 guardian 十轮阻断后通过，`Ran 80 tests`，`OK`；修复 guardian 十一轮阻断后通过，`Ran 81 tests`，`OK`；修复 guardian 十四轮阻断后通过，`Ran 88 tests`，`OK`。
- `python3 -m unittest tests.runtime.test_cli tests.runtime.test_runtime`
  - 结果：修复 guardian 十轮阻断后通过，`Ran 91 tests`，`OK`；修复 guardian 十一轮阻断后再次通过，`Ran 91 tests`，`OK`。
- `python3 -m unittest tests.runtime.test_cli tests.runtime.test_runtime`
  - 结果：修复 guardian 二轮阻断后通过，`Ran 90 tests`，`OK`。
- `python3 -m unittest tests.runtime.test_task_record_store tests.runtime.test_cli tests.runtime.test_runtime`
  - 结果：修复 guardian 四轮阻断后通过，`Ran 109 tests`，`OK`；修复 guardian 五轮阻断后再次通过，`Ran 109 tests`，`OK`；修复 guardian 六轮阻断后再次通过，`Ran 109 tests`，`OK`；修复 guardian 七轮阻断后再次通过，`Ran 110 tests`，`OK`；修复 guardian 八轮阻断后再次通过，`Ran 113 tests`，`OK`；修复 guardian 九轮阻断后再次通过，`Ran 115 tests`，`OK`；修复 guardian 十轮阻断后再次通过，`Ran 115 tests`，`OK`。
- `python3 -m unittest discover`
  - 结果：未发现测试并以 exit code 5 退出，输出 `NO TESTS RAN`；这是当前仓库根目录 unittest discover 规则表现，不代表新测试失败。
- `python3 -m unittest discover -s tests`
  - 结果：首轮通过，`Ran 376 tests`，`OK`；修复 guardian 二轮阻断后再次通过，`Ran 376 tests`，`OK`；修复 guardian 五轮阻断后再次通过，`Ran 376 tests`，`OK`；修复 guardian 六轮阻断后再次通过，`Ran 376 tests`，`OK`；修复 guardian 七轮阻断后再次通过，`Ran 376 tests`，`OK`；修复 guardian 八轮阻断后再次通过，`Ran 376 tests`，`OK`；修复 guardian 九轮阻断后再次通过，`Ran 376 tests`，`OK`；修复 guardian 十轮阻断后再次通过，`Ran 376 tests`，`OK`；修复 guardian 十二轮阻断后再次通过，`Ran 376 tests`，`OK`；修复 guardian 十三轮阻断后再次通过，`Ran 376 tests`，`OK`；修复 guardian 十四轮阻断后再次通过，`Ran 376 tests`，`OK`；修复 guardian 十五轮阻断后再次通过，`Ran 376 tests`，`OK`。
- `python3 scripts/governance_gate.py --mode local --base-ref origin/main`
  - 结果：通过；修复 guardian 十二轮阻断后再次通过。
- `env -u GH_TOKEN -u GITHUB_TOKEN gh pr checks 245 --watch`
  - 结果：PR `#245` 在 head `9b88400` 上远端 CI 全部通过；guardian 十二轮修复后需等待 amend/push 后重新核对。

## 未决风险

- 当前只实现 `ExecutionControlPolicy` 共享 carrier 与 HTTP ingress 投影；仍不实现 `FR-0016/#224` 的超时、重试、并发控制运行体。
- 提交后需要重新运行 guardian，确认 `head SHA` 与 PR review / merge gate 绑定一致。
- `submit` 当前复用同步 Core path；成功 HTTP receipt 的 `status` 来自 durable record 当前状态，可能已是 terminal status，这是当前单进程 runtime 的真实 durable truth。

## 回滚方式

- 在实现 PR 中 revert `syvert/http_api.py`、`tests/runtime/test_http_api.py` 与本 exec-plan 增量。
- 不回滚 `FR-0018` formal spec，不修改 `FR-0016` / `FR-0017` 上游 spec 或 runtime Work Item。

## 最近一次 checkpoint 对应的 head SHA

- 本 exec-plan 记录当前实现与审查恢复上下文，不把 metadata-only 跟进的 live head 作为静态真相追逐；PR `#245` 最新 head 与 merge gate 输出为合入前 authoritative head truth。
