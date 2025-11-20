# 实施任务清单

## 1. 底层驱动层迁移
- [ ] 1.1 修改 `playwright_browser_driver.py` - 切换到 sync_api
- [ ] 1.2 修改 `browser_driver.py` 接口定义 - 移除 async
- [ ] 1.3 修改 `dom_page_analyzer.py` - 移除 async
- [ ] 1.4 修改 `universal_paginator.py` - 移除 async
- [ ] 1.5 运行 `rpa/tests/` 下的单元测试验证

## 2. 服务层迁移
- [ ] 2.1 修改 `browser_service.py` - 所有方法改为同步
- [ ] 2.2 移除 `asyncio` 相关导入和使用
- [ ] 2.3 更新浏览器配置和初始化逻辑
- [ ] 2.4 运行集成测试验证

## 3. 抓取器层迁移
- [ ] 3.1 修改 `base_scraper.py` - 移除 asyncio.run() 包装
- [ ] 3.2 修改 `ozon_scraper.py` - 移除所有 async/await
- [ ] 3.3 修改 `seerfar_scraper.py` - 移除所有 async/await
- [ ] 3.4 修改 `erp_plugin_scraper.py` - 移除所有 async/await
- [ ] 3.5 修改 `competitor_scraper.py` - 移除所有 async/await
- [ ] 3.6 替换 `asyncio.sleep` 为 `time.sleep`

## 4. 测试文件迁移
- [ ] 4.1 修改 `rpa/tests/` 下所有测试文件
- [ ] 4.2 修改 `tests/` 下所有测试文件
- [ ] 4.3 移除测试中的 async/await 和 asyncio 相关代码

## 5. 全面验证
- [ ] 5.1 运行所有单元测试
- [ ] 5.2 运行所有集成测试
- [ ] 5.3 执行端到端测试场景
- [ ] 5.4 性能基准测试对比
- [ ] 5.5 运行 lint 检查并修复错误

## 6. 文档和配置更新
- [ ] 6.1 更新 `openspec/project.md` - 移除"异步优先"约定
- [ ] 6.2 更新 README（如果存在）
- [ ] 6.3 更新依赖说明（如需要）
- [ ] 6.4 添加迁移说明文档

## 7. 代码审查和提交
- [ ] 7.1 代码自审，确保没有遗漏的 async/await
- [ ] 7.2 提交代码变更
- [ ] 7.3 标记 change 为完成
