# CHORE-0327 FR-0026 parent closeout evidence

## 目的

本文档汇总 `FR-0026` 父事项 closeout 所需的主干事实、子 Work Item 状态、验证证据、风险和后续消费边界。它不定义新的 compatibility decision 语义。

## 父 FR

- FR Issue：`#298`
- item_key：`FR-0026-adapter-provider-compatibility-decision`
- release：`v0.8.0`
- sprint：`2026-S21`
- Parent Phase：`#293`

## 子 Work Item closeout 状态

| Issue | item_key | 结果 |
| --- | --- | --- |
| `#323` | `CHORE-0323-fr-0026-formal-spec-closeout` | closed completed |
| `#324` | `CHORE-0324-fr-0026-compatibility-decision-runtime` | closed completed |
| `#325` | `CHORE-0325-fr-0026-provider-no-leakage-guards` | closed completed |
| `#326` | `CHORE-0326-fr-0026-docs-evidence-migration` | closed completed |
| `#327` | `CHORE-0327-fr-0026-parent-closeout` | current closeout Work Item |

## PR / Main 对账

| Work Item | PR | PR head | main merge commit | merged_at |
| --- | --- | --- | --- | --- |
| `#323` | `#333` | `068a0de4198b4c223da14425f71f9da46cc23087` | `22aae087cbf7fba790d85485259d0af278f22375` | `2026-05-03T10:38:00Z` |
| `#324` | `#339` | `d39a94fa46b4f34fcfa4987657dc3e602049f49a` | `b3850cd588d557d2a97ce7d1526863eccbb1ac4e` | `2026-05-04T11:34:43Z` |
| `#325` | `#340` | `65c95969d2702df32155a5037a07da80fb3556db` | `d1577d6e620a43010c40e81f3a8c05b413dbc04f` | `2026-05-05T03:27:37Z` |
| `#326` | `#341` | `1c6d9bff9e4c696ad623aa989ee25d5f6bb3ba17` | `24ae582447165596a54edacb35568ab4c73a55cb` | `2026-05-05T07:15:42Z` |

对账结论：

- `#323/#324/#325/#326` 的 PR 均已 merged，且对应 Work Item 均为 `closed completed`。
- 当前 worktree 基线为 `24ae582447165596a54edacb35568ab4c73a55cb`，已包含 `#323/#324/#325/#326` 的 main truth。
- `#327` 是唯一剩余的 `FR-0026` closeout Work Item，合入后即可关闭父 FR `#298`。

## Review / Guardian 对账

- `#333`：formal spec PR，经 guardian / checks 后合入，主干包含 `docs/specs/FR-0026-adapter-provider-compatibility-decision/`。
- `#339`：runtime PR，经 guardian / checks 后合入，主干包含 `syvert/adapter_provider_compatibility_decision.py` 与 runtime tests。
- `#340`：no-leakage PR，经 guardian `APPROVE` / checks 后合入，主干包含 `syvert/provider_no_leakage_guard.py` 与 no-leakage tests。
- `#341`：docs / evidence PR，经 guardian `APPROVE` / checks 后合入，主干包含 SDK docs 与 `CHORE-0326` evidence。
- `#342`：当前 parent closeout PR，合入前必须取得 guardian `APPROVE` 与 GitHub checks 全绿。

## GitHub 状态对账

- 父 FR `#298` 当前仍 open；它必须等待 `#342` 合入后再 close。
- Phase `#293` 当前仍 open；本 closeout 只为 Phase closeout 提供 `FR-0026` 完成输入，不关闭 Phase。
- `#323/#324/#325/#326` 已关闭；`#327` 当前 open，作为本轮唯一执行入口。

## 主干事实

- Formal spec：`docs/specs/FR-0026-adapter-provider-compatibility-decision/`
- Runtime decision：`syvert/adapter_provider_compatibility_decision.py`
- Runtime tests：`tests/runtime/test_adapter_provider_compatibility_decision.py`
- No-leakage guard：`syvert/provider_no_leakage_guard.py`
- No-leakage tests：`tests/runtime/test_provider_no_leakage_guard.py`
- SDK docs：`adapter-sdk.md`
- Docs evidence：`docs/exec-plans/artifacts/CHORE-0326-fr-0026-compatibility-decision-evidence.md`

## 完成语义

`FR-0026` 已完成以下 v0.8.0 范围：

- 冻结 `AdapterCapabilityRequirement x ProviderCapabilityOffer -> AdapterProviderCompatibilityDecision` 的 canonical decision contract。
- 明确 `matched`、`unmatched`、`invalid_contract` 与 fail-closed 边界。
- Runtime decision 消费 `FR-0024`、`FR-0025` 与 `FR-0027` truth，不重写输入 carrier。
- No-leakage guard 证明 provider identity 不进入 Core projection / routing、registry discovery、TaskRecord、resource lifecycle 或 runtime provider category。
- SDK docs 和 evidence 已解释 Adapter 作者迁移路径、fail-closed 示例与禁止边界。

## 明确不完成

- 不引入 provider selector、priority、score、fallback、ranking 或 marketplace。
- 不声明任何真实 provider 产品正式支持。
- 不让 Core discovery / routing 感知 provider。
- 不关闭 Phase `#293`；Phase closeout 等 `FR-0023`、`FR-0025` 等父项一起收口。

## 后续消费

- `v0.9.0` 真实 provider sample 可以消费本 FR 的 decision contract，但必须以独立 Work Item 进入。
- Phase `#293` closeout 可引用本 closeout evidence 说明 `FR-0026` 已完成。
- 若后续要改变 compatibility decision 语义，必须回到 formal spec Work Item，不在 parent closeout 中改写。
