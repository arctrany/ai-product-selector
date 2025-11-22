# 技术设计文档

## Context

### 背景
当前 OZON 商品抓取流程能够识别有更优价格的跟卖店铺，但无法自动获取这些跟卖商品的详细信息。用户需要手动点击进入跟卖店铺查看详情，影响选品效率。

### 约束条件
1. **浏览器状态管理**: 点击跳转后浏览器 URL 改变，需要管理状态
2. **递归深度限制**: 必须严格控制递归深度，防止无限循环
3. **性能要求**: 额外抓取不应显著影响整体性能（单商品 < 30秒）
4. **向后兼容**: 不能破坏现有调用方式
5. **错误容错**: 递归失败不应影响主流程

### 利益相关者
- **最终用户**: 商家和选品人员
- **开发团队**: 需要维护递归逻辑和错误处理
- **运维团队**: 需要监控性能和错误率

## Goals / Non-Goals

### Goals
- ✅ 自动化抓取第一个跟卖店铺的商品详情
- ✅ 提供完整的跟卖商品数据（价格、ERP、产品ID）
- ✅ 严格控制递归深度，确保系统稳定性
- ✅ 保持向后兼容，不破坏现有功能
- ✅ 提供完善的错误处理和降级策略

### Non-Goals
- ❌ 抓取所有跟卖店铺的详情（只抓取第一个）
- ❌ 提供跟卖商品的跟卖列表（递归时 `include_competitors=False`）
- ❌ 支持用户自定义选择要抓取的跟卖店铺
- ❌ 实现跟卖商品的自动对比和推荐

## Decisions

### 决策1：递归调用 vs 两次独立调用

**选择**: 递归调用（在 `scrape()` 内部调用自身）

**理由**:
- ✅ **代码复用**: 完全复用现有的抓取逻辑，无需重复实现
- ✅ **浏览器状态管理**: 点击后浏览器自动跳转，scrape() 内部 navigate 保证状态一致
- ✅ **向后兼容**: 新增参数有默认值，不影响现有调用
- ✅ **维护成本低**: 只需修改一个方法，易于维护

**备选方案**:
- **方案A**: 在调用方（good_store_selector）进行两次独立调用
  - ❌ 需要在调用方实现点击逻辑
  - ❌ 浏览器状态管理更复杂
  - ❌ 代码重复，维护成本高

### 决策2：递归深度控制策略

**选择**: 双重保险（递归深度参数 + 业务标志参数）

**参数设计**:
```python
def scrape(self, 
           product_url: str, 
           include_competitors: bool = False,
           _recursion_depth: int = 0,
           _fetch_competitor_details: bool = True,
           **kwargs) -> ScrapingResult:
```

**理由**:
- ✅ `_recursion_depth`: 硬性限制，防止任何情况下的无限循环
- ✅ `_fetch_competitor_details`: 语义清晰，明确表达是否要抓取跟卖详情
- ✅ 下划线前缀：表示内部参数，不建议外部调用方使用
- ✅ 默认值：`_recursion_depth=0` 表示初次调用，`_fetch_competitor_details=True` 表示默认启用

**终止条件**:
```python
# 条件1: 深度限制（硬性保护）
if _recursion_depth > 1:
    raise RecursionError("递归深度超限")

# 条件2: 业务控制（逻辑终止）
if (include_competitors and 
    has_better_price and 
    _fetch_competitor_details and 
    _recursion_depth == 0):
    # 触发递归
```

**备选方案**:
- **方案A**: 只用 `include_competitors=False` 作为终止条件
  - ❌ 不够安全，如果参数传递错误可能无限循环
  - ❌ 语义不够清晰
- **方案B**: 使用 `is_recursive_call` 布尔标志
  - ❌ 不如深度参数灵活，未来无法扩展到多层递归

### 决策3：浏览器状态管理

**选择**: scrape() 内部总是执行 navigate

**当前实现保持不变**:
```python
def scrape(self, product_url: str, ...):
    # 总是导航到指定 URL
    await self.browser_service.navigate_to(product_url)
    # ... 抓取逻辑 ...
```

**理由**:
- ✅ **简单一致**: 每次 scrape() 都确保浏览器在正确的页面
- ✅ **自动优化**: Playwright 会自动优化相同 URL 的导航
- ✅ **状态可靠**: 不依赖浏览器当前状态，减少不确定性
- ✅ **易于调试**: 行为可预测

**递归场景的状态变化**:
```
1. scrape(url1) 
   → navigate_to(url1) 
   → 抓取数据
   → click_first_competitor() 
   → 浏览器跳转到 url2

2. scrape(url2, recursion_depth=1)
   → navigate_to(url2)  # 浏览器已在 url2，Playwright 优化
   → 抓取数据
   → 不递归（深度限制）
```

**备选方案**:
- **方案A**: 判断当前 URL 是否匹配，匹配则跳过 navigate
  - ❌ 增加复杂度
  - ❌ 需要处理 URL 参数、锚点等边界情况
  - ❌ 收益有限（Playwright 已有优化）

### 决策4：点击实现方案

**选择**: 在 `_click_first_competitor()` 辅助方法中实现完整的点击和跳转逻辑

**关键发现**: 
跟卖卡片的点击行为基于 JavaScript 事件监听器：
- ❌ **店铺名称/Logo链接** (`a.pdp_ae5`, `a.pdp_ea2`) → 跳转到店铺首页（不是商品页）
- ✅ **价格区域等其他区域** (`div.pdp_bk0`, `div.pdp_b3j` 等) → 跳转到该店铺的商品详情页（这才是我们要的）

**实现要点**:
```python
async def _click_first_competitor(self) -> tuple[str, Optional[str]]:
    """点击第一个跟卖店铺卡片的安全区域（避免店铺名称/Logo）
    返回跳转后的商品详情页URL和商品ID
    
    Returns:
        tuple[str, Optional[str]]: (新URL, 商品ID)
            - 新URL: 跳转后的商品详情页URL
            - 商品ID: 从URL中提取的product_id，提取失败时为None
        
    Raises:
        Exception: 点击失败、跳转失败等
    """
    page = self.browser_service.get_page()
    
    # 1. 定位第一个跟卖卡片（支持新旧选择器）
    card_selectors = ["div.pdp_bk3", "div.pdp_kb2"]
    first_card = None
    for selector in card_selectors:
        cards = page.locator(selector)
        if await cards.count() > 0:
            first_card = cards.first
            self.logger.info(f"✅ 找到第一个跟卖卡片: {selector}")
            break
    
    if not first_card:
        raise Exception("未找到跟卖店铺卡片")
    
    # 2. 优先点击的安全区域选择器（避开店铺名称/Logo）
    # 注意：整个卡片有JS事件监听，点击非店铺链接区域会跳转到商品页
    safe_click_selectors = [
        # 🥇 最高优先级：价格区域（用户已验证）
        "div.pdp_bk0",              # 价格容器
        "div.pdp_b1k",              # 价格文本
        
        # 🥈 高优先级：其他信息区域
        "div.pdp_kb1",              # Ozon卡片价格
        "div.pdp_b3j",              # 配送信息区域
        "div.pdp_jb3",              # 配送文本区域
        
        # 🥉 中优先级：按钮区域
        "div.pdp_j6b",              # 按钮容器
    ]
    
    # 3. 查找可点击的安全区域
    clickable_element = None
    used_selector = None
    
    for selector in safe_click_selectors:
        element = first_card.locator(selector)
        if await element.count() > 0:
            clickable_element = element.first
            used_selector = selector
            self.logger.info(f"✅ 找到安全点击区域: {selector}")
            break
    
    if not clickable_element:
        raise Exception("未找到安全的可点击区域")
    
    # 4. 记录原URL
    original_url = page.url
    self.logger.info(f"原始URL: {original_url}")
    
    # 5. 滚动到元素可见位置
    await clickable_element.scroll_into_view_if_needed()
    await asyncio.sleep(0.2)
    
    # 6. 点击元素
    await clickable_element.click()
    self.logger.info(f"✅ 已点击跟卖卡片的{used_selector}区域")
    
    # 7. 等待页面跳转
    await asyncio.sleep(3)  # 等待页面加载
    
    # 8. 获取跳转后的URL
    new_url = page.url
    self.logger.info(f"跳转后URL: {new_url}")
    
    # 9. 验证跳转
    if new_url == original_url:
        raise Exception("页面未跳转，点击可能失败")
    
    # 10. 验证跳转到商品页（而非店铺首页）
    if '/product/' not in new_url:
        self.logger.warning(f"⚠️ 可能跳转到了店铺首页: {new_url}")
        # 不抛异常，因为可能是预期行为
    
    # 11. 立即从新URL提取product_id
    product_id = self._extract_product_id(new_url)
    if product_id:
        self.logger.info(f"✅ 提取到跟卖商品ID: {product_id}")
    else:
        self.logger.warning(f"⚠️ 无法从URL提取商品ID: {new_url}")
    
    return new_url, product_id
```

**理由**:
- ✅ **正确的点击目标**: 避开店铺链接，点击价格等区域，确保跳转到商品页
- ✅ **用户验证**: 价格区域已由用户实际验证有效
- ✅ **封装完整**: 点击、等待、验证、提取ID都在一个方法中
- ✅ **早期验证**: 跳转后立即提取product_id，更早发现问题
- ✅ **异常明确**: 不同失败场景抛出不同异常
- ✅ **选择器兼容**: 支持 OZON 的新旧版本
- ✅ **易于测试**: 单独测试点击逻辑
- ✅ **日志完善**: 记录详细的点击、跳转和ID提取信息

**为什么不点击店铺名称/Logo**:
- ❌ `a.pdp_ae5` (店铺名称) → 跳转到 `/seller/xxx/` (店铺首页)
- ❌ `a.pdp_ea2` (店铺Logo) → 跳转到 `/seller/xxx/` (店铺首页)
- 店铺首页不是具体商品页，无法直接抓取商品详情

**为什么点击价格区域**:
- ✅ `div.pdp_bk0` (价格容器) → 跳转到 `/product/xxx/` (商品详情页)
- 整个跟卖卡片有 JavaScript 事件监听器
- 点击除店铺链接外的任何区域都会触发商品详情页跳转

**备选方案**:
- **方案A**: 复用 `CompetitorScraper` 的点击逻辑
  - ❌ `CompetitorScraper` 可能不提供点击单个店铺的接口
  - ❌ 增加依赖，降低内聚性
- **方案B**: 直接在 `scrape()` 中实现点击逻辑
  - ❌ 降低可读性
  - ❌ 难以单独测试
- **方案C**: 点击店铺名称链接后再导航
  - ❌ 需要额外的导航步骤
  - ❌ 增加复杂度和失败点

### 决策5：Product ID 提取

**选择**: 从 URL 中使用正则表达式提取

**实现**:
```python
import re

def _extract_product_id(self, url: str) -> Optional[str]:
    """从 URL 中提取商品 ID
    
    支持的 URL 格式:
    - https://www.ozon.ru/product/xxx-1234567/
    - https://www.ozon.ru/seller/xxx/product/1234567/
    
    Returns:
        Optional[str]: 商品ID，提取失败返回 None
    """
    # 匹配 /product/xxx-数字/ 或 /product/数字/
    patterns = [
        r'/product/[^/]+-(\d+)/',    # xxx-1234567
        r'/product/(\d+)/',           # 1234567
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None
```

**调用位置**: 在 `scrape()` 开始时提取
```python
def scrape(self, product_url: str, ...):
    product_id = self._extract_product_id(product_url)
    # ... 继续抓取 ...
    result_data['product_id'] = product_id
```

**理由**:
- ✅ **简单可靠**: URL 格式相对稳定
- ✅ **无额外开销**: 不需要额外的页面操作
- ✅ **向后兼容**: 提取失败返回 None，不影响现有功能

**备选方案**:
- **方案A**: 从页面 DOM 中提取
  - ❌ 增加页面操作开销
  - ❌ 依赖页面结构，不如 URL 稳定
- **方案B**: 从 API 响应中获取
  - ❌ 当前没有 API 抓取，增加复杂度

### 决策6：错误处理策略

**选择**: 完善的降级策略，确保主流程不受影响

**错误场景和处理**:

| 错误场景 | 处理策略 | 影响 |
|---------|---------|------|
| 跟卖卡片不存在 | 捕获异常，记录日志，不抛出 | 主流程继续，`first_competitor_details` 为空 |
| 可点击链接不存在 | 捕获异常，记录日志，不抛出 | 同上 |
| 点击失败 | 捕获异常，记录日志，不抛出 | 同上 |
| 页面未跳转 | 捕获异常，记录日志，不抛出 | 同上 |
| 跳转超时 | 设置超时时间（3秒），超时捕获异常 | 同上 |
| 递归抓取失败 | 捕获异常，记录日志，不抛出 | 同上 |
| 递归深度超限 | 直接返回，不抛出异常 | 防止无限循环 |

**实现**:
```python
# 在 scrape() 中
if (include_competitors and 
    has_better_price and 
    _fetch_competitor_details and 
    _recursion_depth == 0):
    try:
        # 点击和递归逻辑
        first_url, first_product_id = await self._click_first_competitor()
        self.logger.info(f"跳转到跟卖商品: {first_url} (ID: {first_product_id})")
        
        competitor_result = self.scrape(
            first_url,
            include_competitors=False,
            _fetch_competitor_details=False,
            _recursion_depth=1
        )
        
        if competitor_result.success:
            result_data['first_competitor_details'] = competitor_result.data
        else:
            self.logger.warning("递归抓取失败，但不影响主流程")
            
    except Exception as e:
        self.logger.warning(f"抓取跟卖商品详情失败: {e}")
        # 不抛出异常，继续返回原商品数据
```

**理由**:
- ✅ **用户体验**: 部分失败不影响整体流程
- ✅ **系统稳定性**: 降低系统崩溃风险
- ✅ **数据完整性**: 至少返回原商品数据
- ✅ **可观测性**: 记录日志，便于监控和调试

## Risks / Trade-offs

### 风险1: 递归深度控制失效
**风险**: 如果递归深度参数传递错误，可能导致无限循环

**缓解措施**:
- ✅ 双重保险：深度参数 + 业务标志
- ✅ 单元测试：测试递归深度限制
- ✅ 代码审查：重点检查递归调用参数

**残留风险**: 极低，双重保险基本杜绝此风险

### 风险2: 浏览器状态不一致
**风险**: 点击跳转后浏览器状态可能异常（404、超时等）

**缓解措施**:
- ✅ 验证跳转：检查 URL 是否改变
- ✅ 超时控制：设置合理的等待时间
- ✅ 异常捕获：所有异常都被捕获并降级

**残留风险**: 低，完善的错误处理确保主流程不受影响

### 风险3: 性能影响
**风险**: 递归抓取增加约 100-140% 的时间开销

**缓解措施**:
- ✅ 条件触发：只有 `has_better_price=True` 时才触发（预计 < 30% 的商品）
- ✅ 性能监控：设置性能阈值，超时自动失败
- ✅ 可选关闭：通过参数可以关闭递归功能

**残留风险**: 中，需要在实际使用中监控和优化

**Trade-off**: 牺牲部分性能换取更完整的数据

### 风险4: OZON 页面结构变化
**风险**: OZON 更新页面结构，导致选择器失效

**缓解措施**:
- ✅ 多套选择器：支持新旧两套选择器
- ✅ 通用选择器：使用 `href` 属性匹配
- ✅ 降级策略：选择器失效时只影响递归功能，不影响主流程

**残留风险**: 中，需要定期维护选择器

## Migration Plan

### 步骤1: 代码实现和测试（第 1-3 天）
1. 实现核心功能（递归逻辑、点击方法、Product ID 提取）
2. 编写单元测试和集成测试
3. 本地测试验证

### 步骤2: 代码审查和优化（第 4 天）
1. 代码审查：递归逻辑、错误处理、性能
2. 运行 lint 和类型检查
3. 修复发现的问题

### 步骤3: 集成验证（第 5 天）
1. 在完整的选品流程中测试
2. 验证数据正确性和完整性
3. 验证性能满足要求

### 步骤4: 灰度发布（第 6-7 天）
1. 部署到测试环境
2. 小范围测试用户试用
3. 收集反馈和监控数据

### 步骤5: 全量发布（第 7 天后）
1. 部署到生产环境
2. 监控系统性能和错误率
3. 根据监控数据调优

### 回滚计划
如果出现严重问题：
1. 通过配置关闭递归功能（设置 `_fetch_competitor_details=False`）
2. 回滚代码到上一个稳定版本
3. 修复问题后重新发布

## Open Questions

### Q1: 是否需要支持抓取多个跟卖店铺？
**当前决策**: 只抓取第一个（价格最低的）

**理由**: 
- 简化实现，降低复杂度
- 大多数情况下，最低价就是最有参考价值的

**未来扩展**: 如果有需求，可以添加参数控制抓取数量

### Q2: 是否需要支持用户自定义选择跟卖店铺？
**当前决策**: 不支持，只自动抓取第一个

**理由**:
- 自动化是核心目标
- 用户自定义需要额外的交互界面

**未来扩展**: 可以在 CLI 或 GUI 中添加交互选项

### Q3: 递归抓取失败率阈值是多少？
**当前决策**: 错误率 < 5% 为可接受

**监控指标**:
- 点击失败率
- 跳转失败率
- 递归抓取失败率

**调优计划**: 根据实际监控数据调整选择器和超时时间

### Q4: 是否需要缓存跟卖商品详情？
**当前决策**: 不缓存，每次都重新抓取

**理由**:
- 价格和库存实时变化
- 缓存增加复杂度

**未来扩展**: 如果性能成为瓶颈，可以添加短期缓存（如 5 分钟）

## Summary

本设计文档详细描述了跟卖商品详情自动抓取功能的技术方案，包括：

1. **递归调用方案**: 在 `scrape()` 内部条件性递归，完全复用现有逻辑
2. **递归深度控制**: 双重保险（深度参数 + 业务标志）确保不会无限循环
3. **浏览器状态管理**: scrape() 总是 navigate，确保状态一致性
4. **点击实现**: 独立的 `_click_first_competitor()` 方法，支持多套选择器
5. **Product ID 提取**: 从 URL 正则提取，简单可靠
6. **错误处理**: 完善的降级策略，确保主流程不受影响

该方案在保持向后兼容的同时，提供了强大的自动化能力和完善的容错机制，预期能够显著提高用户的选品效率。
