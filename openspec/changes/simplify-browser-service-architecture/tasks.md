## 1. 分析和准备
- [x] 1.1 使用 sub agent 深度分析 xuanping_browser_service 架构
- [x] 1.2 使用 sub agent 深度分析 browser_service 架构
- [x] 1.3 使用 sub agent 深度分析 driver 架构
- [x] 1.4 使用 sub agent 分析参数传递流程
- [x] 1.5 识别所有冗余和不合理设计
- [x] 1.6 创建 OpenSpec 提案

## 2. 删除冗余层
- [ ] 2.1 识别所有使用 XuanpingBrowserService 的代码位置
- [ ] 2.2 将所有调用迁移到直接使用 SimplifiedBrowserService
- [ ] 2.3 删除 `common/scrapers/xuanping_browser_service.py` 文件
- [ ] 2.4 更新相关的导入语句

## 3. 简化 SimplifiedBrowserService
- [ ] 3.1 移除 `_shared_instances` 类变量和相关方法
- [ ] 3.2 移除 `_instance_lock` 异步锁
- [ ] 3.3 简化 `initialize()` 方法，移除共享实例检查
- [ ] 3.4 简化 `close()` 方法，移除共享实例清理
- [ ] 3.5 移除 `cleanup_all_shared_instances()` 类方法
- [ ] 3.6 移除 `_generate_instance_key()` 方法

## 4. 优化配置传递
- [ ] 4.1 修改 `_prepare_browser_config()` 方法，移除重复设置
- [ ] 4.2 优化 BrowserConfig 到 Driver 的直接传递
- [ ] 4.3 确保 user_data_dir 只在必要时设置一次
- [ ] 4.4 确保 debug_port 只在必要时设置一次
- [ ] 4.5 移除 to_dict() 后的重复赋值逻辑

## 5. 简化 global_browser_singleton
- [ ] 5.1 简化配置创建逻辑
- [ ] 5.2 移除不必要的配置字段
- [ ] 5.3 确保单例管理的唯一性
- [ ] 5.4 优化 Profile 检测和验证流程

## 6. 更新调用代码
- [ ] 6.1 更新 `seerfar_scraper.py` 中的浏览器服务使用
- [ ] 6.2 更新 `good_store_selector.py` 中的浏览器服务使用
- [ ] 6.3 更新其他所有使用浏览器服务的代码
- [ ] 6.4 确保所有导入语句正确

## 7. 测试
- [ ] 7.1 编写单元测试：测试全局单例机制
- [ ] 7.2 编写单元测试：测试用户数据复用
- [ ] 7.3 编写集成测试：测试完整的浏览器启动流程
- [ ] 7.4 编写集成测试：测试 Profile 检测和验证
- [ ] 7.5 编写回归测试：确保所有现有功能正常
- [ ] 7.6 手动测试：验证无头模式启动
- [ ] 7.7 手动测试：验证连接到现有浏览器
- [ ] 7.8 手动测试：验证僵尸进程清理机制

## 8. 文档和清理
- [ ] 8.1 更新 README（如果有）
- [ ] 8.2 更新代码注释
- [ ] 8.3 运行 lint 检查并修复所有错误
- [ ] 8.4 运行类型检查（如果使用 mypy）
- [ ] 8.5 清理未使用的导入
- [ ] 8.6 验证没有遗留的 TODO 或临时代码

## 9. 验证和部署
- [ ] 9.1 运行所有测试套件
- [ ] 9.2 验证代码覆盖率
- [ ] 9.3 进行代码审查
- [ ] 9.4 部署到测试环境
- [ ] 9.5 验证测试环境功能正常
- [ ] 9.6 部署到生产环境
- [ ] 9.7 监控生产环境运行状况
