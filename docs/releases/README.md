# Syvert Release 索引区

本目录用于承载 release 级目标、完成判据与事项聚合入口。

## 职责边界

- release 文档回答“这个版本要证明什么、明确不做什么、完成判据是什么”。
- release 文档只承载聚合索引，不承载 GitHub backlog 的状态真相。
- release 文档通过 `item_key` 关联 `spec`、`exec-plan`、`decision` 与 PR。

## 禁止承载的内容

- 不记录可漂移的 backlog 状态明细。
- 不替代 GitHub Milestones / Projects。
- 不复制 formal spec 正文或执行细节。

## 模板

- 新 release 索引优先从 [./_template.md](./_template.md) 复制。
