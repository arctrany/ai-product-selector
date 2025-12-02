# Competitor Scraper - 跟卖店铺抓取器规范

## ADDED Requirements

### Requirement: ScrapingUtils工具类 - 商品ID提取
ScrapingUtils SHALL 提供`extract_product_id_from_url()`方法，支持从OZON商品URL中提取商品ID。

#### Scenario: 标准格式URL提取
- **WHEN** 调用`extract_product_id_from_url("https://www.ozon.ru/product/123456789/")`
- **THEN** 应返回商品ID字符串`"123456789"`

#### Scenario: 带商品名称的URL提取
- **WHEN** 调用`extract_product_id_from_url("https://www.ozon.ru/product/product-name-123456789/")`
- **THEN** 应返回商品ID字符串`"123456789"`

#### Scenario: 相对路径URL提取
- **WHEN** 调用`extract_product_id_from_url("/product/123456789/")`
- **THEN** 应返回商品ID字符串`"123456789"`

#### Scenario: 无效URL格式
- **WHEN** URL不包含`/product/`路径或不包含数字ID
- **THEN** 应返回`None`
- **AND** 记录调试级别日志说明无法提取

#### Scenario: 复用现有代码风格
- **WHEN** 实现`extract_product_id_from_url()`方法
- **THEN** 应复用现有的`extract_store_id_from_url()`方法的模式匹配风格
- **AND** 使用相同的日志记录格式（✅成功、⚠️警告）
- **AND** 使用相同的异常处理模式


### Requirement: 获取第一个跟卖店铺的商品ID
CompetitorScraper SHALL 提供获取指定排名跟卖店铺商品ID的能力，以支持后续对该商品的详细信息抓取。

#### Scenario: 成功从DOM提取商品ID
- **WHEN** 跟卖店铺元素中包含商品链接（`/product/xxx-123456789/`格式）
- **THEN** 系统应直接从DOM中提取商品ID
- **AND** 返回结果包含`success=True`, `product_id`, `method="dom_extraction"`
- **AND** 执行时间应小于1秒

#### Scenario: DOM提取失败，通过点击跳转提取商品ID
- **WHEN** 跟卖店铺元素中不包含商品链接
- **THEN** 系统应点击店铺的价格区域或非头像区域
- **AND** 等待页面跳转到商品详情页
- **AND** 从新页面URL中提取商品ID
- **AND** 返回结果包含`success=True`, `product_id`, `method="click_navigation"`
- **AND** 执行时间应小于10秒

#### Scenario: 所有提取策略都失败
- **WHEN** DOM中无商品链接且点击跳转也失败
- **THEN** 系统应返回`success=False`
- **AND** 返回结果包含详细的错误信息
- **AND** 不应抛出未捕获的异常

#### Scenario: 指定排名的店铺不存在
- **WHEN** 请求获取排名N的店铺商品ID，但只有M个店铺（M < N）
- **THEN** 系统应返回`success=False`
- **AND** 错误信息应明确说明店铺数量不足

### Requirement: CompetitorScraper复用工具类提取商品ID
CompetitorScraper SHALL 调用`self.scraping_utils.extract_product_id_from_url()`方法提取商品ID，而不是自己实现URL解析逻辑。

#### Scenario: 调用工具类方法
- **WHEN** 需要从URL提取商品ID
- **THEN** 应调用`self.scraping_utils.extract_product_id_from_url(url)`
- **AND** 不应在CompetitorScraper中重复实现URL解析逻辑

#### Scenario: 处理工具类返回值
- **WHEN** 工具类返回有效的商品ID
- **THEN** 应直接使用该ID
- **WHEN** 工具类返回`None`
- **THEN** 应记录日志并尝试其他提取策略

### Requirement: 从DOM元素中提取商品链接
系统 SHALL 能够从跟卖店铺的DOM元素中查找并提取商品链接。

#### Scenario: 元素包含商品链接
- **WHEN** 店铺元素中存在`<a href="/product/xxx-123456789/">`标签
- **THEN** 应成功提取该链接和商品ID
- **AND** 返回包含`product_id`和`product_url`的字典

#### Scenario: 元素只包含店铺链接
- **WHEN** 店铺元素中只有`<a href="/seller/xxx/">`标签
- **THEN** 应返回`None`
- **AND** 记录调试日志说明未找到商品链接

#### Scenario: 元素包含多个链接
- **WHEN** 店铺元素中包含多个链接（店铺链接和商品链接）
- **THEN** 应优先选择商品链接（包含`/product/`）
- **AND** 忽略店铺链接（包含`/seller/`）

### Requirement: 通过点击跳转提取商品ID
系统 SHALL 支持通过点击店铺元素跳转到商品页面并提取商品ID。

#### Scenario: 点击价格区域跳转成功
- **WHEN** 点击店铺的价格区域（`div.pdp_b3k`）
- **THEN** 应触发页面跳转到商品详情页
- **AND** 等待新页面加载完成
- **AND** 从新页面URL提取商品ID
- **AND** 返回包含`product_id`和`product_url`的字典

#### Scenario: 点击跳转超时
- **WHEN** 点击后页面在10秒内未完成跳转
- **THEN** 应返回`None`
- **AND** 记录错误日志说明超时
- **AND** 不应阻塞后续流程

#### Scenario: 点击元素不可用
- **WHEN** 目标点击元素不存在或不可点击
- **THEN** 应返回`None`
- **AND** 记录警告日志说明元素状态

### Requirement: 集成到scrape()方法
系统 SHALL 在`scrape()`方法中集成商品ID提取功能，支持通过参数控制是否提取。

#### Scenario: 通过context参数启用商品ID提取
- **WHEN** 调用`scrape(url, context={'extract_first_product': True})`
- **THEN** 在提取跟卖列表后自动提取第一个店铺的商品ID
- **AND** 返回结果中包含`first_competitor_product_id`字段

#### Scenario: 默认不提取商品ID
- **WHEN** 调用`scrape(url)`不传递`extract_first_product`参数
- **THEN** 应保持现有行为，只返回跟卖店铺列表
- **AND** 不执行商品ID提取逻辑
- **AND** 确保向后兼容性

#### Scenario: 提取商品ID失败不影响主流程
- **WHEN** 跟卖列表提取成功但商品ID提取失败
- **THEN** 应返回`success=True`
- **AND** 返回完整的跟卖列表数据
- **AND** `first_competitor_product_id`字段为`None`
- **AND** 记录警告日志说明提取失败原因
