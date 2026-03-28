# FR-0001 契约说明

本事项不引入新的业务运行时契约，但会约束治理层的稳定输入与输出：

- `pr_guardian` 输出结构化审查结果，至少包含 `verdict`、`safe_to_merge`、`summary`
- `merge_pr` 只消费绑定当前 `head SHA` 的最新有效 guardian 结果
- merge gate 的判定字段与语义以 [code_review.md](../../../../code_review.md) 为准

本目录当前仅记录治理层稳定接口语义；若后续需要细化 guardian 结果 schema 或 merge gate 输入格式，再在此目录增补专门文档。
