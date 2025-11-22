# Implementation Tasks

## 1. 添加模板生成功能到 UIConfig
- [ ] 1.1 在 `cli/models.py` 中添加 `generate_template()` 类方法
- [ ] 1.2 实现 `select-shops` 模式的模板生成逻辑
- [ ] 1.3 实现 `select-goods` 模式的模板生成逻辑
- [ ] 1.4 确保模板包含注释说明每个字段的用途

## 2. 添加 CLI 命令支持
- [ ] 2.1 在 `cli/main.py` 的 `create_parser()` 中添加 `--create-template-data` 选项
- [ ] 2.2 添加 `--mode` 参数用于指定模板类型（select-shops/select-goods）
- [ ] 2.3 添加 `--output` 参数用于指定输出文件路径（默认：当前目录）
- [ ] 2.4 实现 `handle_create_template_command()` 函数处理模板生成
- [ ] 2.5 确保生成的模板中 `output_path` 字段说明：如未指定则默认输出到当前目录

## 3. 清理冗余字段
- [ ] 3.1 从 `UIConfig` 中移除未使用的 `item_created_days` 字段
- [ ] 3.2 从 `UIConfig` 中移除 `category_blacklist` 字段（应在系统配置中）
- [ ] 3.3 更新 `to_dict()` 方法移除 `item_created_days` 和 `category_blacklist` 字段
- [ ] 3.4 确保 `remember_settings` 和 `dryrun` 不出现在生成的模板中
- [ ] 3.5 更新现有的示例文件 `test_user_data.json` 移除 `item_created_days` 和 `category_blacklist`
- [ ] 3.6 在模板中添加 `item_shelf_days` 字段

## 4. 更新文档和帮助信息
- [ ] 4.1 更新 CLI help text 说明新命令的用法
- [ ] 4.2 在 epilog 中添加模板生成的示例
- [ ] 4.3 更新字段说明，明确哪些字段在哪种模式下使用

## 5. 测试
- [ ] 5.1 测试 `select-shops` 模式模板生成
- [ ] 5.2 测试 `select-goods` 模式模板生成
- [ ] 5.3 验证生成的模板可以被 `load_user_data()` 正确加载
- [ ] 5.4 测试默认输出路径和自定义输出路径
- [ ] 5.5 测试 `output_path` 为空时使用当前目录作为默认值
- [ ] 5.6 确保清理字段后现有测试仍然通过

## 6. 验证
- [ ] 6.1 运行所有现有测试确保无回归
- [ ] 6.2 手动测试生成的模板文件
- [ ] 6.3 验证生成的 JSON 格式正确且可读
