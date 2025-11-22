、## 1. 分析和准备
- [x] 1.1 使用 sub agent 深度分析 xuanping_browser_service 架构
- [x] 1.2 使用 sub agent 深度分析 browser_service 架构
- [x] 1.3 使用 sub agent 深度分析 driver 架构
- [x] 1.4 使用 sub agent 分析参数传递流程
- [x] 1.5 识别所有冗余和不合理设计
- [x] 1.6 创建 OpenSpec 提案

## 2. 删除冗余层
- [x] 2.1 识别所有使用 XuanpingBrowserService 的代码位置
- [x] 2.2 将所有调用迁移到直接使用 SimplifiedBrowserService
- [x] 2.3 删除 `common/scrapers/xuanping_browser_service.py` 文件
- [x] 2.4 更新相关的导入语句

## 3. 简化 SimplifiedBrowserService
- [x] 3.1 移除 `_shared_instances` 类变量和相关方法
- [x] 3.2 移除 `_instance_lock` 异步锁
- [x] 3.3 简化 `initialize()` 方法，移除共享实例检查
- [x] 3.4 简化 `close()` 方法，移除共享实例清理
- [x] 3.5 移除 `cleanup_all_shared_instances()` 类方法
- [x] 3.6 移除 `_generate_instance_key()` 方法

## 4. 优化配置传递
- [x] 4.1 修改 `_prepare_browser_config()` 方法，移除重复设置
- [x] 4.2 优化 BrowserConfig 到 Driver 的直接传递
- [x] 4.3 确保 user_data_dir 只在必要时设置一次
- [x] 4.4 确保 debug_port 只在必要时设置一次
- [x] 4.5 移除 to_dict() 后的重复赋值逻辑

## 5. 简化 global_browser_singleton
- [x] 5.1 简化配置创建逻辑
- [x] 5.2 移除不必要的配置字段
- [x] 5.3 确保单例管理的唯一性
- [x] 5.4 优化 Profile 检测和验证流程

## 6. 更新调用代码
- [x] 6.1 更新 `ozon_scraper.py` 改用 `get_global_browser_service()`
- [x] 6.2 更新 `seerfar_scraper.py` 改用 `get_global_browser_service()`
- [x] 6.3 更新 `__init__.py` 模块导出
- [x] 6.4 更新 `test_competitor_debug.py` 测试文件
- [x] 6.5 更新 `test_erp_ozon_integration.py` 测试文件
- [x] 6.6 确保所有导入语句正确

## 7. 代码质量检查
- [x] 7.1 运行 lint 检查（无错误）
- [x] 7.2 验证所有导入引用正确
- [x] 7.3 确保代码编译通过
- [x] 7.4 验证无遗留的 TODO 或临时代码

## 8. 任务完成
- [x] 8.1 所有代码修改完成
- [x] 8.2 所有 lint 检查通过
- [x] 8.3 tasks.md 已更新

---

## 📊 最终成果

**代码简化统计：**
- 删除代码：~870 行
- 删除文件：1 个（xuanping_browser_service.py，724行）
- 配置优化：减少 60% 的配置转换代码
- Lint 检查：✅ 通过（无错误）

**修改文件清单（9个）：**
1. ✅ `rpa/browser/browser_service.py` - 简化主服务类
2. ✅ `common/scrapers/global_browser_singleton.py` - 简化配置
3. ✅ `common/scrapers/erp_plugin_scraper.py` - 迁移到全局单例
4. ✅ `common/scrapers/ozon_scraper.py` - 改用 get_global_browser_service()
5. ✅ `common/scrapers/seerfar_scraper.py` - 改用 get_global_browser_service()
6. ✅ `common/scrapers/__init__.py` - 更新模块导出
7. ✅ `tests/test_competitor_debug.py` - 改用 get_global_browser_service()
8. ✅ `tests/test_erp_ozon_integration.py` - 改用 get_global_browser_service()
9. ✅ `openspec/changes/simplify-browser-service-architecture/tasks.md` - 本文件

**架构改进：**
- ✅ 统一浏览器服务管理（单一入口）
- ✅ 消除配置冗余转换
- ✅ 简化代码调用链路
- ✅ 提高代码可维护性

**🎉 OpenSpec 提案 `simplify-browser-service-architecture` 已成功完成！**
