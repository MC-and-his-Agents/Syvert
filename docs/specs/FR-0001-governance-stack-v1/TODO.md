# FR-0001 TODO

## 状态

- 当前成熟度：`implementation-ready`
- 当前阻塞：
  - 需要为当前 `head SHA` 重新获得 latest valid guardian verdict

## 实施清单

- [x] 建立治理栈 v1 的分层文档、hook、CI、merge 入口与项目自动化
- [x] 统一 policy 单一规则源与治理测试基线
- [x] 收敛 guardian verdict 复用信任边界，只消费本地受控结果
- [x] 统一高优先级文档中的 merge gate 口径
- [x] 将 GitHub Issue 与当前 PR 绑定并补齐验证证据

## 验证清单

- [x] 治理测试通过
- [x] 文档门禁、规约门禁与治理门禁通过
- [ ] guardian review 对当前 `head SHA` 通过
- [ ] 受控 merge 成功完成

## 会话恢复信息

- 当前停点：等待 guardian 对当前 `head SHA` 给出最新有效结论。
- 下一步动作：guardian 通过后执行 `python3 scripts/merge_pr.py 1 --delete-branch`。
