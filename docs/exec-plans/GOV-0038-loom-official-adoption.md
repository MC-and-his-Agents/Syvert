# GOV-0038 Loom official adoption 执行计划

## 关联信息

- item_key：`GOV-0038-loom-official-adoption`
- Issue：`#258`
- item_type：`GOV`
- release：`governance-baseline`
- sprint：`loom-official-adoption`
- 关联 spec：无（治理 bootstrap / Loom adoption 事项）
- Loom carrier spec：`.loom/specs/INIT-0001/spec.md`
- 关联 decision：`docs/decisions/ADR-GOV-0038-loom-official-adoption.md`
- 关联 PR：#259
- active 收口事项：`GOV-0038-loom-official-adoption`
- 状态：`active`

## 目标

- 将 Loom 正式作为 Syvert 的上游 governance runtime / canonical governance layer 引入 Syvert main。
- 通过 `.loom/bootstrap`、`.loom/bin` 与 `.loom/companion` 让 Loom 可以直接读取 Syvert 的强治理 surface。
- 将 Syvert 文档中的通用治理语义降级为 Loom 指向，同时保留 Syvert repo-owned residue。

## 范围

- 本次纳入：`.loom/` runtime / companion carrier、`AGENTS.md`、`WORKFLOW.md`、`docs/AGENTS.md`、`docs/process/delivery-funnel.md`、`.github/PULL_REQUEST_TEMPLATE.md` 的 Loom locator、`.github/workflows/governance-gate.yml` 的 repo-local Loom gate wiring、`scripts/governance_gate.py` / `scripts/policy/policy.json` 的 `.loom` governance policy、`tests/governance/**` 回归测试、`docs/decisions/ADR-GOV-0038-loom-official-adoption.md`。
- 本次不纳入：删除 Syvert guardian、替换 integration contract、修改 adapter/runtime 行为、把 release/sprint/item_key 升级为 Loom core schema。

## 当前停点

- GitHub Phase `#256`、FR `#257`、Work Item `#258` 已创建，并通过 native sub-issue 关系形成 `#256 -> #257 -> #258`。
- 独立 worktree `/Users/mc/dev/syvert-official-loom` 已从 `origin/main` 创建。
- Loom bootstrap 已生成 vendored `.loom/bin` runtime 与初始 fact chain。
- Syvert-owned PR template 未被替换，仅追加 Loom runtime locator 与 verify compatibility 注释。
- `.loom/companion` 与 `.loom/shadow` 已按 Phase D smoke boundary 转成正式 adoption carrier。

## 下一步动作

- CI 与 guardian 已在 PR #259 上循环校验；当前下一步是等待最新 guardian 通过后执行受控 merge。
- 合入后关闭 Work Item `#258`、FR `#257` 与 Phase `#256`，并同步 main。

## 当前 checkpoint 推进的 release 目标

- 为 `governance-baseline` 正式建立 Loom consumption carrier，使 Syvert main 可以直接被 Loom runtime parity 与 shadow parity 读取。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`loom-official-adoption` 的唯一实现 Work Item，承接 Phase D release judgment 后的 Syvert 正式迁移。
- 阻塞：`tests/runtime` 全量发现当前存在既有 baseline 失败；Work Item #258 与 FR #257 已明确接受该项为本治理迁移 out-of-scope，并由 #260 跟进修复。本轮以 governance gate、CI 必跑门禁与 Loom-on-Syvert 验证作为合并依据。

## 已验证项

- `python3 .loom/bin/loom_check.py .`
  - 结果：通过；repo-local Loom gate 覆盖 vendored runtime、runtime parity、shadow parity 与 merge checkpoint。
- `python3 .loom/bin/loom_init.py verify --target .`
  - 结果：通过。
- `python3 .loom/bin/loom_init.py route --target . --task 'inspect adoption carrier'`
  - 结果：通过；vendored `.loom/bin` layout 不依赖外部 skills registry。
- `python3 .loom/bin/loom_flow.py governance-profile status --target .`
  - 结果：`pass`，maturity=`strong`。
- `python3 .loom/bin/loom_flow.py runtime-parity validate --target .`
  - 结果：`pass`。
- `python3 .loom/bin/loom_flow.py shadow-parity --target .`
  - 结果：`pass`。
- `python3 .loom/bin/loom_flow.py shadow-parity --target . --blocking`
  - 结果：`pass`。
- `python3 .loom/bin/loom_flow.py checkpoint merge --target . --item INIT-0001`
  - 结果：`pass`；review head binding 为 `carrier-only`，spec review head binding 为 `implementation-drift-only` 且 `spec_changed_paths=[]`。
- `python3 .loom/bin/loom_init.py bootstrap --target . --output ../loom-escape.json --verify`
  - 结果：阻断；`--output` 必须保持在 target root 内。
- 临时篡改 `.loom/bootstrap/init-result.json` 的 `fact_chain.entry_points.work_item` 为 `../loom-escape.md` 后运行 fact-chain 读取。
  - 结果：阻断；fact-chain carrier 必须保持在 target root 内。
- 临时篡改 `.loom/companion/manifest.json` 的 locator 为 `../loom-escape.md` 后运行 `build_governance_surface()`。
  - 结果：repo companion interface 变为 `incomplete`，对应 locator 不再返回 `present`；companion locator 必须保持在 target root 内。
- `python3 .loom/bin/loom_flow.py review read --target . --review-file ../outside.json`
  - 结果：阻断；review artifact 必须保持在 target root 内。
- `python3 .loom/bin/loom_flow.py review record --target . --decision fallback --kind general_review --summary x --reviewer x --fallback-to build --findings-file ../outside.json`
  - 结果：阻断；findings file 必须保持在 target root 内。
- `python3 .loom/bin/loom_flow.py work-item create --target . --item SAFE-WS-ESCAPE --goal x --scope x --execution-path x --workspace-entry ../ --validation-entry x --closing-condition x`
  - 结果：阻断，且未创建 `.loom/work-items/SAFE-WS-ESCAPE.md`；workspace entry 必须在写入 carrier 前完成边界校验。
- 临时篡改 `.loom/bootstrap/init-result.json` 的 `fact_chain.entry_points.current_item_id` 为 `../escape` 后运行 review flow。
  - 结果：阻断；既有 fact-chain 中的 item id 也必须通过路径安全校验。
- 使用 `--output .loom/bootstrap/custom-init-result.json` bootstrap 后运行 fact-chain。
  - 结果：通过；status surface 的 `Locator Truth` 与实际 output path 保持一致。
- `python3.11 -m py_compile scripts/*.py scripts/policy/*.py`
  - 结果：通过。
- `python3.11 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3.11 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3.11 -m unittest discover -s tests/governance -p 'test_*.py'`
  - 结果：通过。
- `python3.11 -m unittest discover -s tests/runtime -p 'test_*.py'`
  - 结果：5 failures / 1 error；该项属于 Syvert runtime business baseline residual，已在 #258/#257 中作为 accepted waiver 记录，并由 #260 跟进，不阻断 PR #259 的 Loom governance adoption closeout。
  - 结果：失败，5 failures / 1 error；失败集中于 Douyin browser bridge、CLI durable truth、platform leakage fixture，与本轮 `.loom` / governance docs 改动无直接路径重叠。

## 未决风险

- 当前 Loom `v1.3` 要求 vendored `.loom/bin` runtime；未来 Loom runtime 升级时 Syvert 需要刷新 vendored 文件，直到 Loom 支持 external-runtime companion。
- 若后续继续在 Syvert 中扩写通用治理模型，会重新产生 Loom 与 Syvert 平行治理漂移。
- `tests/runtime` 既有 baseline 失败需要由后续 Syvert runtime Work Item 单独处理，不能混入本治理迁移 PR。

## 回滚方式

- 使用独立 revert PR 撤销 `.loom/` carrier、ADR-GOV-0038、PR template locator 与本轮文档边界增量；Syvert legacy governance、guardian、integration contract 与 runtime 实现未被删除，可直接恢复迁移前状态。

## 起始基线 SHA

- `5a949c9dfc1a076faf58b706064d4383ff98ceb6`
- 说明：该 SHA 是本轮 worktree 从 `origin/main` 创建时的只读基线，只用于说明迁移起点，不是当前 checkpoint。

## 当前 checkpoint 真相

- Work Item：`.loom/work-items/INIT-0001.md`
- Progress：`.loom/progress/INIT-0001.md`
- Status：`.loom/status/current.md`
- Review：`.loom/reviews/INIT-0001.json`
- Spec review：`.loom/reviews/INIT-0001.spec.json`
- Merge checkpoint：`python3 .loom/bin/loom_flow.py checkpoint merge --target . --item INIT-0001`，结果 `pass`。

## 最近一次 checkpoint 对应的 head SHA

- 当前 checkpoint 真相由 `.loom/reviews/INIT-0001.json` 的 `reviewed_head`、`.loom/progress/INIT-0001.md` 与 `.loom/status/current.md` 共同记录。
- 当前文本不把起始基线 SHA 伪装为 checkpoint；执行恢复时以 Loom carrier 为准。
