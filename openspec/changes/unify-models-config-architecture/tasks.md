# 统一模型和配置架构 - 任务清单

## 1. 冲突和冗余清理
- [ ] 1.1 统一dryrun配置字段
- [ ] 1.2 统一店铺筛选配置字段
- [ ] 1.3 更新所有配置引用和同步机制
- [ ] 1.4 统一Browser配置命名
- [ ] 1.5 统一超时和重试参数命名
- [ ] 1.6 更新受影响的引用文件
- [ ] 1.7 迁移task_control到CLI层
- [ ] 1.8 重构logging_config

## 2. 模型层准备
- [ ] 2.1 创建common/models/enums.py模型文件
- [ ] 2.2 创建common/models/business_models.py文件
- [ ] 2.3 创建common/models/scraping_models.py文件
- [ ] 2.4 创建common/models/excel_models.py文件
- [ ] 2.5 创建common/models/exceptions.py文件
- [ ] 2.6 更新common/models/__init__.py统一导出
- [ ] 2.7 验证向后兼容性

## 3. 配置层准备
- [ ] 3.1 创建cli/config/user_config.py
- [ ] 3.2 创建system配置目录
- [ ] 3.3 创建business配置目录
- [ ] 3.4 重组scraping配置目录
- [ ] 3.5 更新config/__init__.py统一导出
- [ ] 3.6 验证配置向后兼容性

## 4. 工具函数迁移
- [ ] 4.1 创建common/utils/model_utils.py
- [ ] 4.2 迁移clean_price_string到common/utils/scraping_utils.py
- [ ] 4.3 更新common/models/__init__.py兼容导出

## 5. 删除旧文件
- [ ] 5.1 删除common/models.py
- [ ] 5.2 删除common/config.py
- [ ] 5.3 删除common/logging_config.py
- [ ] 5.4 保留common/models/scraping_result.py作为别名
- [ ] 5.5 运行完整测试套件验证

## 6. 模型层测试
- [ ] 6.1 编写test_models_enums.py
- [ ] 6.2 编写test_models_business.py
- [ ] 6.3 编写test_models_scraping.py
- [ ] 6.4 编写test_models_excel.py
- [ ] 6.5 编写test_models_exceptions.py
- [ ] 6.6 编写test_models_compatibility.py

## 7. 配置层测试
- [ ] 7.1 编写test_config_user.py
- [ ] 7.2 编写test_config_system.py
- [ ] 7.3 编写test_config_business.py
- [ ] 7.4 编写test_config_scraping.py
- [ ] 7.5 编写test_config_compatibility.py
- [ ] 7.6 编写test_config_validation.py

## 8. 集成测试
- [ ] 8.1 编写test_good_store_selector_integration.py
- [ ] 8.2 编写test_config_loading_integration.py
- [ ] 8.3 验证完整流程测试覆盖

## 9. 更新现有测试用例
- [ ] 9.1 审查tests目录下所有测试文件
- [ ] 9.2 识别使用老旧模型导入的测试
- [ ] 9.3 识别使用老旧配置导入的测试
- [ ] 9.4 更新所有测试使用新的模型导入路径
- [ ] 9.5 更新所有测试使用新的配置导入路径
- [ ] 9.6 补充新字段的测试覆盖
- [ ] 9.7 补充配置验证逻辑的测试
- [ ] 9.8 完善业务模型的测试场景
- [ ] 9.9 完善抓取模型的测试场景
- [ ] 9.10 运行完整测试套件验证
- [ ] 9.11 修复所有测试失败
- [ ] 9.12 验证测试覆盖率达标

## 10. 文档更新
- [ ] 10.1 更新openspec/project.md模型架构章节
- [ ] 10.2 更新openspec/project.md配置架构章节
- [ ] 10.3 更新openspec/project.md模块依赖关系图
- [ ] 10.4 更新openspec/project.md分层架构说明
- [ ] 10.5 创建迁移指南文档
- [ ] 10.6 标记废弃的导入路径
- [ ] 10.7 验证所有文档链接有效
- [ ] 10.8 验证所有代码示例可运行

## 11. 代码清理和质量检查
- [ ] 11.1 清理未跟踪的临时文件
- [ ] 11.2 运行autoflake检查并移除未使用的导入
- [ ] 11.3 运行vulture检测并移除死代码
- [ ] 11.4 运行pylint检测并消除重复代码
- [ ] 11.5 验证所有文件都有文档字符串
- [ ] 11.6 运行完整lint和类型检查
- [ ] 11.7 提交最终代码清理变更
