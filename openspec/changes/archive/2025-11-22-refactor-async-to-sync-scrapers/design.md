# 异步到同步架构改造设计文档

## Context

当前系统存在严重的异步/同步混合架构问题：
- Browser Driver接口层全部使用async/await
- Playwright集成使用异步API
- 但业务层经常同步调用异步方法，导致大量RuntimeWarning
- 项目原则："推荐能同步处理，就不要异步"
- 网页抓取场景实际上不需要异步并发处理

## Goals / Non-Goals

### Goals
- **完全消除异步依赖**：0个async/await关键字在scraper相关代码中
- **统一编程模型**：所有接口都是同步的
- **消除RuntimeWarning**：解决91个异步警告
- **简化代码复杂度**：移除事件循环和异步处理逻辑
- **提升性能**：减少异步开销
- **提高可维护性**：统一的同步编程范式

### Non-Goals  
- 不改变CLI和打包系统（保持现有功能）
- 不影响Excel处理和配置管理模块
- 不改变外部API接口（如果有的话）

## Decisions

### 1. Browser Driver接口设计
**决策**: 将所有异步方法改为同步方法
```python
# 原来 (异步)
async def initialize(self) -> bool:
async def open_page(self, url: str) -> bool:
async def execute_script(self, script: str) -> Any:

# 改为 (同步)  
def initialize(self) -> bool:
def open_page(self, url: str) -> bool:
def execute_script(self, script: str) -> Any:
```

**理由**: 网页抓取是线性操作，不需要并发处理

### 2. Playwright集成策略
**决策**: 使用Playwright的同步API（已验证存在）
```python
# ✅ 确认可用：Playwright官方支持同步API
from playwright.sync_api import Playwright, Browser, Page, sync_playwright

# 同步启动浏览器示例
def create_browser():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        return browser, page

# 同步操作示例
def sync_browser_operations(page):
    page.goto("https://example.com")  # 同步导航
    element = page.query_selector("div")  # 同步查询
    element.click()  # 同步点击
```

**选择**: 使用Playwright官方的sync_api，完全移除asyncio依赖

### 3. 错误处理策略
**决策**: 简化异常处理装饰器
```python
# 移除异步分支，只保留同步处理
def handle_browser_errors(default_return=None):
    def decorator(func):
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BrowserError:
                raise
            except Exception as e:
                raise BrowserError(f"Unexpected error in {func.__name__}: {str(e)}")
        return sync_wrapper
    return decorator
```

### 4. 测试策略
**决策**: 完全移除异步测试设置
- 移除`@pytest.mark.asyncio`
- 移除`AsyncMock`，使用普通`Mock`
- 简化测试setup和teardown

## Architecture Impact

### Before (异步混合架构)
```
CLI Layer
    ↓
Scraper Business Layer (同步调用异步方法 - 问题所在!)
    ↓  
Browser Service Layer (异步)
    ↓
Browser Driver Interface (异步)
    ↓
Playwright Implementation (异步)
```

### After (纯同步架构)
```
CLI Layer
    ↓
Scraper Business Layer (纯同步)
    ↓
Browser Service Layer (纯同步)  
    ↓
Browser Driver Interface (纯同步)
    ↓
Playwright Sync Implementation (同步封装)
```

## Risks / Trade-offs

### 风险
1. **Playwright API限制**: 如果同步API功能受限
   - **缓解**: 创建完善的异步到同步适配层
2. **性能影响**: 失去异步并发能力
   - **缓解**: 网页抓取场景本身就是串行的，影响有限
3. **第三方依赖**: 某些库可能只提供异步接口
   - **缓解**: 创建同步适配器或寻找替代方案

### 权衡
- **简洁性 vs 并发性**: 选择简洁的同步模型
- **性能 vs 维护性**: 选择可维护性
- **一致性 vs 灵活性**: 选择架构一致性

## Migration Plan

### 阶段1: 接口层改造 (1-2天)
1. 更新IBrowserDriver接口签名
2. 更新Browser Service接口
3. 修复编译错误

### 阶段2: 实现层改造 (2-3天)  
1. 研究Playwright同步API
2. 重写PlaywrightBrowserDriver
3. 实现同步适配层

### 阶段3: 业务层改造 (2-3天)
1. 修复所有scraper文件
2. 移除异步调用
3. 修复BeautifulSoup警告

### 阶段4: 测试和验证 (1-2天)
1. 重写测试用例
2. 验证功能正常
3. 确保0个异步警告

### 回滚策略
如果改造过程中遇到不可解决的问题：
1. Git回滚到改造前状态
2. 采用渐进式修复：先修复明显的异步调用错误
3. 保留异步接口，但确保正确使用

## 已解决的关键问题

1. **✅ Playwright同步API完整性**: 官方文档确认支持完整的同步API
2. **✅ 具体异步调用位置识别**:
   - `competitor_scraper.py:93` - `page.query_selector()` 未await
   - `ozon_scraper.py:303` - `Locator.count()` 未await  
   - Browser Driver接口中15个异步方法需要同步化
3. **✅ 改造范围确定**: 主要涉及3个层次：接口层、实现层、业务层

## 待验证问题

1. **性能基准**: 改造后的性能对比数据
2. **兼容性测试**: 不同操作系统上的兼容性验证  
3. **错误处理**: 同步模式下的错误恢复策略是否需要调整？

## Implementation Notes

### 关键文件优先级
1. **高优先级**: `browser_driver.py`, `browser_service.py`
2. **中优先级**: `ozon_scraper.py`, `competitor_scraper.py`  
3. **低优先级**: 测试文件，工具脚本

### 代码审查要点
- 确保没有遗留的async/await关键字
- 验证所有导入语句已更新
- 检查错误处理逻辑的完整性
- 确认性能没有显著下降
