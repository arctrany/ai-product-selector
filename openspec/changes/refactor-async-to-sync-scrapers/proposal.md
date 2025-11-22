# Change: 彻底移除Scraper系统中的异步依赖，实现完全同步化架构

## Why

当前Scraper系统存在严重的异步/同步混合架构问题，导致：

1. **RuntimeWarning频发**：`coroutine 'Page.query_selector' was never awaited` 等91个警告
2. **架构不一致**：部分代码使用同步调用异步API，违反项目"推荐能同步处理，就不要异步"原则
3. **维护复杂性**：异步/同步混合代码难以理解和调试
4. **性能问题**：不必要的事件循环开销
5. **测试困难**：需要AsyncMock和复杂的异步测试设置

通过grep分析发现，整个Browser Driver接口层、Playwright集成层都是异步的，但实际业务场景（网页抓取）完全可以用同步方式实现。

## What Changes

### **BREAKING** 核心架构重构
- **移除所有async/await关键字**：将IBrowserDriver接口完全同步化
- **替换Playwright异步API**：使用Playwright同步API或封装同步接口
- **重构Browser Service**：移除asyncio依赖，实现纯同步服务
- **更新所有Scraper实现**：ozon_scraper.py, competitor_scraper.py等
- **修复BeautifulSoup废弃API**：text参数改为string参数

### 具体变更范围
- `rpa/browser/core/interfaces/browser_driver.py` - 接口同步化
- `rpa/browser/implementations/` - Playwright驱动同步化  
- `common/scrapers/*.py` - 所有scraper同步化
- `tests/` - 测试代码同步化
- 移除`asyncio`、`AsyncMock`等异步相关导入

## Impact

### 受影响的specs
- `base-scraper` - 基础scraper接口变更
- `browser-service` - 浏览器服务接口重大变更  
- `ozon-scraper` - OZON scraper实现变更

### 受影响的代码
- **接口层**：`IBrowserDriver` 15个异步方法全部同步化
- **实现层**：`PlaywrightBrowserDriver` 完全重写
- **业务层**：所有 `*_scraper.py` 文件
- **测试层**：所有测试文件移除异步标记

### 向后兼容性
- **BREAKING**: 所有异步接口调用需要更新
- **BREAKING**: BrowserService初始化方式变更
- **BREAKING**: Scraper方法签名变更（移除async/await）

### 预期收益
- **0个异步警告**：完全消除RuntimeWarning
- **简化代码**：移除复杂的异步处理逻辑
- **提升性能**：消除不必要的事件循环开销  
- **提高可维护性**：统一的同步编程模型
