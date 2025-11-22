# Spec Delta: ozon-scraper

## 变更类型
MODIFICATION - 添加跟卖商品详情自动抓取功能，扩展 OZON scraper 能力

## 变更内容

### 新增 Requirement: 跟卖商品详情自动抓取
系统 SHALL 在检测到有更优价格的跟卖店铺时，自动抓取第一个跟卖店铺的商品详细信息。

#### Scenario: 有更优跟卖价格时自动抓取详情
- **GIVEN** 系统正在抓取 OZON 商品信息
- **AND** `include_competitors=True`（启用跟卖抓取）
- **AND** 检测到 `has_better_price=True`（存在更优跟卖价格）
- **WHEN** 系统完成跟卖列表抓取后
- **THEN** 系统应自动点击第一个跟卖店铺链接
- **AND** 浏览器应跳转到跟卖商品页面
- **AND** 系统应递归调用 `scrape()` 方法抓取该商品的详细信息
- **AND** 递归调用时 `include_competitors=False`（不再抓取该商品的跟卖）
- **AND** 递归调用时 `_recursion_depth=1`（标记为递归调用）
- **AND** 抓取结果应包含在 `first_competitor_details` 字段中

#### Scenario: 无更优跟卖价格时不触发递归
- **GIVEN** 系统正在抓取 OZON 商品信息
- **AND** `include_competitors=True`
- **AND** `has_better_price=False`（无更优跟卖价格）
- **WHEN** 系统完成商品信息抓取
- **THEN** 系统不应触发递归抓取
- **AND** 返回结果中不应包含 `first_competitor_details` 字段

#### Scenario: 递归抓取失败时降级
- **GIVEN** 系统正在递归抓取跟卖商品详情
- **AND** 点击跟卖店铺链接失败或页面未跳转
- **WHEN** 捕获到异常
- **THEN** 系统应记录警告日志
- **AND** 系统不应抛出异常
- **AND** 系统应继续返回原商品的数据
- **AND** 返回结果中 `first_competitor_details` 为空

### 新增 Requirement: 递归深度严格控制
系统 SHALL 通过递归深度参数严格限制递归层数，防止无限循环。

#### Scenario: 递归深度限制生效
- **GIVEN** 系统正在执行 `scrape()` 方法
- **AND** `_recursion_depth > 1`
- **WHEN** 方法开始执行
- **THEN** 系统应直接返回，不执行任何抓取操作
- **AND** 系统应记录递归深度超限的信息

#### Scenario: 递归调用时深度参数正确传递
- **GIVEN** 系统正在执行递归调用
- **WHEN** 调用 `scrape(new_url, ..., _recursion_depth=1)`
- **THEN** 递归调用应正确接收 `_recursion_depth=1`
- **AND** 递归调用内部不应再次触发递归（深度检查生效）

### 新增 Requirement: Product ID 字段
系统 SHALL 在抓取商品信息时提取并返回唯一的 Product ID。

#### Scenario: 从 URL 提取 Product ID
- **GIVEN** 商品 URL 为 `https://www.ozon.ru/product/xxx-1234567/`
- **WHEN** 系统执行 `scrape()` 方法
- **THEN** 系统应从 URL 中提取 Product ID `1234567`
- **AND** 返回结果中应包含 `product_id: "1234567"`

#### Scenario: Product ID 提取失败时处理
- **GIVEN** 商品 URL 格式异常，无法提取 Product ID
- **WHEN** 系统执行 `scrape()` 方法
- **THEN** 系统应继续正常抓取
- **AND** 返回结果中 `product_id` 字段为 `None`
- **AND** 不应影响其他字段的抓取

### 新增 Requirement: 跟卖店铺点击和跳转
系统 SHALL 能够自动定位、点击第一个跟卖店铺卡片的安全区域（避免店铺名称/Logo），并验证页面跳转到商品详情页成功。

**重要说明**: 跟卖卡片的点击行为基于 JavaScript 事件监听器：
- ❌ 点击店铺名称/Logo (`a.pdp_ae5`, `a.pdp_ea2`) → 跳转到店铺首页 `/seller/xxx/`
- ✅ 点击价格等其他区域 (`div.pdp_bk0`, `div.pdp_b3j`) → 跳转到商品详情页 `/product/xxx/`

#### Scenario: 成功点击价格区域并跳转到商品页
- **GIVEN** 商品页面存在跟卖店铺列表
- **AND** 第一个跟卖店铺卡片包含价格区域
- **WHEN** 系统执行 `_click_first_competitor()` 方法
- **THEN** 系统应定位到第一个跟卖店铺卡片
- **AND** 系统应优先查找价格区域 (`div.pdp_bk0`) 等安全点击目标
- **AND** 系统不应点击店铺名称链接 (`a.pdp_ae5`) 或Logo链接 (`a.pdp_ea2`)
- **AND** 系统应点击价格区域或其他安全区域
- **AND** 浏览器应跳转到跟卖商品详情页
- **AND** 新页面 URL 应包含 `/product/` 路径
- **AND** 新页面 URL 应不同于原页面 URL
- **AND** 系统应立即从新URL提取 product_id
- **AND** 方法应返回 (新URL, product_id) 元组

#### Scenario: 避免点击店铺链接
- **GIVEN** 系统正在查找可点击元素
- **AND** 跟卖卡片中同时存在价格区域和店铺名称链接
- **WHEN** 系统执行选择器匹配
- **THEN** 系统应优先选择价格区域 (`div.pdp_bk0`)
- **AND** 系统不应选择店铺名称链接 (`a.pdp_ae5`)
- **AND** 系统不应选择Logo链接 (`a.pdp_ea2`)
- **AND** 点击后应跳转到商品详情页而非店铺首页

#### Scenario: 跳转后立即提取product_id
- **GIVEN** 系统成功点击跟卖卡片并跳转到新页面
- **AND** 新页面URL为 `https://www.ozon.ru/product/xxx-7654321/`
- **WHEN** 系统在 `_click_first_competitor()` 方法中验证跳转后
- **THEN** 系统应立即调用 `_extract_product_id()` 从新URL提取商品ID
- **AND** 应成功提取到 product_id `7654321`
- **AND** 应记录日志："✅ 提取到跟卖商品ID: 7654321"
- **AND** 方法应返回元组 `(new_url, "7654321")`

#### Scenario: 无法提取product_id时的处理
- **GIVEN** 系统成功点击并跳转到新页面
- **AND** 新页面URL格式异常，无法提取product_id
- **WHEN** 系统尝试提取product_id
- **THEN** `_extract_product_id()` 应返回 `None`
- **AND** 系统应记录警告日志："⚠️ 无法从URL提取商品ID: {url}"
- **AND** 方法应返回元组 `(new_url, None)`
- **AND** 不应抛出异常，继续执行

#### Scenario: 跟卖店铺卡片不存在时
- **GIVEN** 商品页面不存在跟卖店铺列表
- **WHEN** 系统执行 `_click_first_competitor()` 方法
- **THEN** 系统应抛出 "未找到跟卖店铺卡片" 异常

#### Scenario: 安全点击区域不存在时
- **GIVEN** 第一个跟卖店铺卡片存在
- **AND** 卡片中不存在安全的可点击区域（价格、配送信息等）
- **WHEN** 系统执行 `_click_first_competitor()` 方法
- **THEN** 系统应抛出 "未找到安全的可点击区域" 异常

#### Scenario: 页面未跳转时
- **GIVEN** 系统点击了跟卖卡片的安全区域
- **AND** 等待 3 秒后页面 URL 未改变
- **WHEN** 系统验证页面跳转
- **THEN** 系统应抛出 "页面未跳转" 异常

### 新增 Requirement: 选择器兼容性
系统 SHALL 支持 OZON 平台的新旧两套 CSS 选择器，提供降级策略。

#### Scenario: 使用新版选择器成功定位
- **GIVEN** OZON 页面使用新版 CSS 类名
- **WHEN** 系统尝试定位跟卖店铺卡片
- **THEN** 系统应使用新版选择器 `div.pdp_bk3` 成功定位

#### Scenario: 新版选择器失败时降级到旧版
- **GIVEN** OZON 页面使用旧版 CSS 类名
- **AND** 新版选择器 `div.pdp_bk3` 无法定位元素
- **WHEN** 系统尝试定位跟卖店铺卡片
- **THEN** 系统应降级使用旧版选择器 `div.pdp_kb2`
- **AND** 应成功定位卡片

#### Scenario: 所有选择器都失败时
- **GIVEN** OZON 页面结构发生重大变化
- **AND** 所有预定义选择器都无法定位元素
- **WHEN** 系统尝试定位跟卖店铺卡片
- **THEN** 系统应抛出 "未找到跟卖店铺卡片" 异常

## 技术实现说明

**新增的功能**：
- 递归调用 `scrape()` 方法抓取跟卖商品详情
- Product ID 提取和返回
- 跟卖店铺卡片的安全点击和页面跳转验证
- 新旧选择器兼容性支持

**新增的返回字段**：
- `product_id`: 商品唯一标识符
- `first_competitor_details`: 第一个跟卖商品的详细信息（可选）

**向后兼容性**：
- 所有新增参数都有默认值
- 所有新增返回字段都是可选的
- 现有调用方式无需修改

