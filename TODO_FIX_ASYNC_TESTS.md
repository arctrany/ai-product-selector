# 异步测试修复任务清单

## 待修复文件列表

### 1. test_browser_cdp_launch.py
- **问题**: 使用pytest.mark.asyncio装饰器和async/await语法
- **修复建议**: 
  - 移除async/await关键字
  - 移除@pytest.mark.asyncio装饰器
  - 将异步测试方法改为同步方法
  - 移除asyncio.run()调用

### 2. test_browser_service*.py 系列文件
- **问题**: 使用pytest.mark.skip标记，API已变更但测试未更新
- **修复建议**:
  - 移除pytest.mark.skip标记
  - 更新测试用例以匹配SimplifiedBrowserService API
  - 将异步测试方法改为同步方法
  - 移除AsyncMock相关代码

### 3. test_erp_ozon_integration.py
- **问题**: 使用unittest.IsolatedAsyncioTestCase和大量async/await语法
- **修复建议**:
  - 将unittest.IsolatedAsyncioTestCase改为unittest.TestCase
  - 移除async/await关键字
  - 将asyncSetUp/asyncTearDown改为setUp/tearDown
  - 移除asyncio.run()调用

### 4. test_ozon_competitor_scenarios_fixed.py
- **问题**: 使用unittest.IsolatedAsyncioTestCase和async/await语法
- **修复建议**:
  - 将unittest.IsolatedAsyncioTestCase改为unittest.TestCase
  - 移除async/await关键字
  - 将asyncSetUp/asyncTearDown改为setUp/tearDown
  - 移除asyncio.run()调用

### 5. test_ozon_scraper_recursive_features.py
- **问题**: 使用unittest.IsolatedAsyncioTestCase
- **修复建议**:
  - 将unittest.IsolatedAsyncioTestCase改为unittest.TestCase
  - 移除async/await关键字（如果存在）
  - 将asyncSetUp/asyncTearDown改为setUp/tearDown

## 修复优先级
1. test_browser_cdp_launch.py - 高优先级
2. test_erp_ozon_integration.py - 高优先级
3. test_ozon_competitor_scenarios_fixed.py - 高优先级
4. test_ozon_scraper_recursive_features.py - 中优先级
5. test_browser_service*.py 系列文件 - 低优先级（已标记跳过）