# CHORE-0424 v1.5 creator media consumer migration 执行计划

## 关联信息

- item_key：`CHORE-0424-v1-5-creator-media-consumer-migration`
- Issue：`#424`
- item_type：`CHORE`
- release：`v1.5.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#405`
- 关联 spec：`docs/specs/FR-0405-creator-profile-media-asset-read-contract/spec.md`
- 关联 PR：待创建
- 状态：`active`
- active 收口事项：`CHORE-0424-v1-5-creator-media-consumer-migration`

## 目标

- 证明 `creator_profile_by_id` 与 `media_asset_fetch_by_ref` 已被 TaskRecord、CLI query、HTTP result、Adapter requirement、Provider offer 与 compatibility decision 的共享 consumer 路径接受。
- 保持 compatibility decision 只消费 requirement/offer/admission inputs，不读取 result carriers。
- 保持 `content_detail_by_url`、`content_search_by_keyword`、`content_list_by_creator`、`comment_collection` 与既有 `v1.x` shared query/result 路径不回退。

## 范围

- 本次纳入：
  - `tests/runtime/test_adapter_capability_requirement.py`
  - `tests/runtime/test_provider_capability_offer.py`
  - `tests/runtime/test_adapter_provider_compatibility_decision.py`
  - `tests/runtime/test_http_api.py`
  - `tests/runtime/test_cli.py`
  - 本 exec-plan
- 本次不纳入：
  - creator/media runtime carrier 本体（#422/#423 已承接）。
  - sanitized evidence matrix（#425）。
  - `#405` closeout、release tag、GitHub Release 或 Phase `#381` closeout（#426）。

## 当前停点

- `#422 / PR #440 / 005329da83fe299ff0996099901999117c4f770d` 已合入 creator runtime carrier。
- `#423 / PR #439 / e2e62f8667784d0b746a6c086f259c5268d8430c` 已合入 media runtime carrier。
- 共享 consumer 代码路径经审查已基本泛化；本 Work Item 主要补 creator/media admission、compatibility 与 result-query proof，避免误以为只支持 `#403/#404`。

## consumer migration 结论

- Adapter requirement / Provider offer / compatibility decision 已通过 `stable_operation_entry()` 命中 creator/media stable execution slices；本次补 creator/media 的 matched / unmatched / invalid_contract 场景回归。
- TaskRecord durable truth 已能承载 creator/media public envelopes；本次补 CLI query 与 HTTP result 对两类 terminal envelope 的无重包裹读取回归。
- 共享 consumer 不应读取 raw payload shape；creator/media query/result 继续只消费 public envelope 与 normalized result。

## 已验证项

- `python3 -m unittest tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_http_api tests.runtime.test_cli`
  - 结果：通过，177 tests。
- `python3 -m unittest discover -s tests -p 'test*.py'`
  - 结果：通过，527 tests。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/version_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `git diff --check`
  - 结果：通过。

## 最近一次 checkpoint 对应的 head SHA

- `417673b020605c72133b79f11c0c5fa56d2f4ff7`

## 未决风险

- `#425` 仍需把 creator/media dual-reference evidence 与 no raw payload policy 落成正式 artifact。
- `#426` 仍需汇总 closeout truth、release decision 与 deferred 项。

## 回滚方式

- 使用独立 revert PR 撤销本 Work Item 的 consumer regression / compatibility proof / exec-plan 增量修改。
