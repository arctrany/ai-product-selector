# 技术设计文档

## Context

### 背景
当前项目使用 Playwright 的异步 API (`playwright.async_api`) 进行浏览器自动化，导致代码中充斥着 `async/await` 关键字，增加了维护复杂度和潜在的稳定性问题。

### 约束条件
1. **项目规范**：用户规则要求"**推荐** 能同步处理，就不要异步"
2. **业务场景**：当前是单任务顺序处理，不需要异步并发
3. **技术可行性**：Playwright 提供完整的同步 API 支持
4. **兼容性要求**：跨平台支持（Windows、macOS、Linux）

### 利益相关者
- **开发团队**：代码维护者，受益于简化的代码
- **测试团队**：需要更新所有测试用例
- **用户**：不受影响，功能保持一致

## Goals / Non-Goals

### Goals
- ✅ 将所有异步代码改为同步实现
- ✅ 保持功能完全一致，零破坏性变更
- ✅ 提高代码可读性和可维护性
- ✅ 消除异步相关的稳定性风险

### Non-Goals
- ❌ 不改变外部 API 接口
- ❌ 不重构业务逻辑
- ❌ 不优化性能（性能略微下降可接受）
- ❌ 不添加新功能

## Decisions

### 决策1：使用 Playwright 同步 API

**选择**：从 `playwright.async_api` 切换到 `playwright.sync_api`

**理由**：
- Playwright 官方同时支持两种 API，功能完全对等
- 同步 API 更简单，符合项目规范要求
- 无需引入额外依赖

**替代方案考虑**：
- ❌ **保持异步但优化使用**：不符合项目规范，无法从根本解决问题
- ❌ **切换到其他自动化库**：迁移成本过高，风险大

### 决策2：自底向上的迁移策略

**选择**：从底层驱动开始，逐层向上迁移

**理由**：
- 底层变更影响上层，自底向上可以逐步验证
- 每层迁移后可以立即测试，降低风险
- 符合依赖关系，避免循环依赖问题

**迁移顺序**：
1. Playwright 驱动实现 (`playwright_browser_driver.py`)
2. 接口定义 (`browser_driver.py`)
3. 分析器和分页器
4. 浏览器服务层 (`browser_service.py`)
5. 抓取器基类 (`base_scraper.py`)
6. 具体抓取器（ozon、seerfar、erp、competitor）
7. 测试文件

### 决策3：一次性完整迁移

**选择**：在一个 change 中完成所有迁移，不分多个 PR

**理由**：
- 避免同步/异步混合状态导致的问题
- 降低维护成本，避免需要同时维护两套实现
- 便于回滚（如果需要）

**替代方案考虑**：
- ❌ **渐进式迁移**：会导致同步异步混用，增加复杂度

### 决策4：API 兼容性保持

**选择**：保持所有公共方法的签名不变（除了移除 async）

**理由**：
- 降低对调用方的影响
- 功能行为完全一致
- 便于测试验证

**变更示例**：
```python
# 之前
async def navigate_to(self, url: str) -> bool:
    await self.page.goto(url)
    return True

# 之后
def navigate_to(self, url: str) -> bool:
    self.page.goto(url)
    return True
```

## Risks / Trade-offs

### 风险1：大量代码修改可能引入 bug

**风险**：涉及 50+ 处代码修改，可能引入疏漏

**缓解措施**：
- 逐模块迁移并测试
- 使用 IDE 的重构功能辅助
- 全面的单元测试和集成测试
- 代码审查
- 使用 grep/rg 搜索确保没有遗漏的 async/await

### 风险2：性能略微下降

**风险**：失去异步并发能力，可能影响性能

**缓解措施**：
- 当前场景是单任务顺序处理，实际影响很小
- 可以在迁移后进行性能基准测试对比
- 如果性能下降明显，可以考虑局部优化

### 风险3：第三方库兼容性

**风险**：某些第三方库可能只支持异步

**缓解措施**：
- Playwright 同步 API 功能完整，无此问题
- 项目主要依赖都支持同步方式

### Trade-off：失去未来的异步扩展能力

**代价**：如果将来需要并发处理，需要重新迁移回异步

**接受理由**：
- 当前和可预见的未来都不需要并发
- 如果真需要，可以局部引入异步而非全局
- 简单性和可维护性优先级更高

## Migration Plan

### 阶段1：准备（1天）
1. 创建功能分支
2. 设置测试基准（记录当前所有测试的通过状态）
3. 准备回滚计划

### 阶段2：底层迁移（1-2天）
1. 修改 Playwright 驱动和接口
2. 运行单元测试验证
3. 修复发现的问题

### 阶段3：服务层迁移（1天）
1. 修改浏览器服务层
2. 运行集成测试验证
3. 修复发现的问题

### 阶段4：业务层迁移（1-2天）
1. 修改所有抓取器
2. 修改所有测试文件
3. 运行完整测试套件
4. 修复所有失败的测试

### 阶段5：验证和优化（1天）
1. 端到端测试
2. 性能基准测试
3. 代码审查
4. Lint 检查
5. 文档更新

### 总计时间估算：5-7 天

### 回滚策略
- 如果发现严重问题无法及时解决：
  1. 回滚所有代码到迁移前状态
  2. 保留 proposal 和经验教训
  3. 重新评估方案

### 验证标准
- ✅ 所有现有测试通过
- ✅ Lint 检查无错误
- ✅ 代码中无残留的 async/await 关键字
- ✅ 功能行为与迁移前完全一致
- ✅ 性能下降在可接受范围内（<20%）

## Technical Details

### 关键代码变更模式

#### 模式1：导入语句
```python
# 之前
from playwright.async_api import Browser, Page, BrowserContext

# 之后  
from playwright.sync_api import Browser, Page, BrowserContext
```

#### 模式2：方法定义
```python
# 之前
async def get_page_content(self) -> str:
    return await self.page.content()

# 之后
def get_page_content(self) -> str:
    return self.page.content()
```

#### 模式3：方法调用
```python
# 之前
content = await browser_service.get_page_content()

# 之后
content = browser_service.get_page_content()
```

#### 模式4：延时操作
```python
# 之前
await asyncio.sleep(1)

# 之后
import time
time.sleep(1)
```

#### 模式5：BaseScraper.scrape_page_data
```python
# 之前（混合模式）
def scrape_page_data(self, url: str, extractor_func: Callable) -> ScrapingResult:
    async def async_scrape():
        await self.browser_service.navigate_to(url)
        data = await extractor_func(self.browser_service)
        return ScrapingResult(...)
    
    return asyncio.run(async_scrape())

# 之后（纯同步）
def scrape_page_data(self, url: str, extractor_func: Callable) -> ScrapingResult:
    self.browser_service.navigate_to(url)
    data = extractor_func(self.browser_service)
    return ScrapingResult(...)
```

### 浏览器初始化变更
```python
# 之前
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch()

# 之后
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
```

## Open Questions

1. ✅ **Playwright 同步 API 是否功能完整？**
   - 答：是的，功能完全对等

2. ⏳ **是否需要更新 requirements.txt？**
   - 答：Playwright 包同时包含两种 API，无需更新

3. ⏳ **迁移后性能下降是否可接受？**
   - 答：需要在迁移后进行基准测试评估

4. ⏳ **是否需要保留任何异步代码？**
   - 答：目前看来全部同步化即可，除非测试中发现特殊场景
