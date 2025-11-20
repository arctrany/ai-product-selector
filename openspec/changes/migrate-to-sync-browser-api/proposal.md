# Change: 将浏览器自动化从异步迁移到同步API

## Why

**问题**：
当前项目大量使用异步代码（async/await），导致以下问题：
1. **维护困难**：异步代码的复杂性增加了调试和维护成本
2. **稳定性问题**：事件循环管理、asyncio.run() 等增加了潜在的错误点
3. **违反项目规范**：用户规则明确要求"**推荐** 能同步处理，就不要异步"
4. **不必要的复杂度**：当前业务场景是单任务顺序处理，不需要并发

**技术可行性**：
- Playwright 同时支持同步和异步 API
- 当前使用 `playwright.async_api`，可切换到 `playwright.sync_api`
- 所有异步操作都可以用同步方式实现

## What Changes

### 核心变更
- **从 `playwright.async_api` 迁移到 `playwright.sync_api`**
- **移除所有 `async/await` 关键字**
- **移除 `asyncio.run()` 等异步运行工具**
- **将所有异步方法改为同步方法**

### 影响范围

**核心文件（11个）：**
1. `rpa/browser/implementations/playwright_browser_driver.py` - Playwright 驱动实现
2. `rpa/browser/browser_service.py` - 浏览器服务层
3. `rpa/browser/core/interfaces/browser_driver.py` - 接口定义
4. `common/scrapers/base_scraper.py` - 抓取器基类
5. `common/scrapers/ozon_scraper.py` - OZON 抓取器
6. `common/scrapers/seerfar_scraper.py` - Seerfar 抓取器
7. `common/scrapers/erp_plugin_scraper.py` - ERP 插件抓取器
8. `common/scrapers/competitor_scraper.py` - 竞争对手抓取器
9. `rpa/browser/implementations/dom_page_analyzer.py` - DOM 分析器
10. `rpa/browser/implementations/universal_paginator.py` - 分页器
11. 所有测试文件（10+ 个）

**代码修改统计：**
- 异步方法数量：50+ 处
- 涉及模块：browser-service, ozon-scraper, seerfar-scraper

### 不影响的内容
- ✅ 外部API接口保持不变
- ✅ 数据模型和业务逻辑不变
- ✅ 配置管理方式不变
- ✅ 用户界面和CLI交互不变

## Impact

**收益：**
- ✅ 代码更简单、易理解
- ✅ 调试和维护更容易
- ✅ 消除异步带来的稳定性风险
- ✅ 符合项目规范要求

**潜在风险：**
- ⚠️ 大量代码修改可能引入bug
- ⚠️ 需要全面的回归测试
- ⚠️ 可能略微降低并发性能（但当前场景不需要并发）

**影响的规格：**
- `browser-service` - 所有异步方法改为同步
- `ozon-scraper` - 抓取方法改为同步
- `seerfar-scraper` - 抓取方法改为同步

**受影响的代码：**
- `rpa/browser/` - 核心浏览器服务层
- `common/scrapers/` - 所有抓取器
- `rpa/tests/` 和 `tests/` - 所有测试文件

**迁移策略：**
1. 自底向上迁移：先改底层驱动，再改上层业务
2. 逐模块验证：每个模块改完后立即运行该模块的测试
3. 全面回归测试：所有模块改完后进行端到端测试
