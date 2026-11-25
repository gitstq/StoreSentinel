# 贡献指南 / Contributing

感谢关注 StoreSentinel！欢迎通过 Issue 反馈问题、通过 PR 贡献代码。

## 本地开发

```bash
git clone https://github.com/gitstq/StoreSentinel.git
cd StoreSentinel
python3 -m unittest discover -s tests   # 运行测试（零依赖）
python3 -m storesentinel --list-rules   # 查看规则
```

## 提交规范

遵循 [Angular Commit 规范](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit)：

- `feat:` 新增规则或功能
- `fix:` 修复缺陷
- `docs:` 文档
- `refactor:` 重构
- `test:` 测试
- `chore:` 构建/工具

## 新增规则的约定

1. 在对应扫描器（`storesentinel/scanners/`）中定义 `Rule` 常量并实现检测逻辑；
2. 在 `storesentinel/registry.py` 注册；
3. 在 `tests/` 中至少添加一个触发该规则的用例与一个不触发的用例；
4. 更新三份 README 中的规则表。

## 代码风格

- 仅使用 Python 3.8+ 标准库（保持零依赖）
- 每个模块、函数配有 docstring 与注释
- 严重级别语义：`error` = 大概率被拒审；`warn` = 常见拒审风险；`info` = 建议项
