## MODIFIED Requirements

### Requirement: 商品价格抓取
OZON抓取器 SHALL 提供同步的商品价格抓取功能，从商品详情页提取价格信息。

**变更说明**：内部实现从异步改为同步，但对外接口保持不变（仅移除 async）。

#### Scenario: 抓取单个商品价格
- **GIVEN** 提供有效的OZON商品URL
- **WHEN** 调用 `scrape_product_prices(url)` 方法（同步）
- **THEN** 返回包含商品价格、标题等信息的 ProductInfo 对象

#### Scenario: 提取价格数据
- **GIVEN** 已导航到商品详情页
- **WHEN** 内部调用 `extract_price_data` 函数（同步）
- **THEN** 同步提取并返回价格、标题、跟卖数等信息

### Requirement: 跟卖店铺抓取
OZON抓取器 SHALL 提供同步的跟卖店铺信息抓取功能。

**变更说明**：从异步方法改为同步方法。

#### Scenario: 抓取跟卖店铺列表
- **GIVEN** 商品存在跟卖店铺
- **WHEN** 调用 `scrape_competitor_stores(url)` 方法（同步）
- **THEN** 返回跟卖店铺信息列表

#### Scenario: 提取竞争对手数据
- **GIVEN** 已导航到商品详情页并打开跟卖弹窗
- **WHEN** 内部调用 `extract_competitor_data` 函数（同步）
- **THEN** 同步提取并返回竞争对手店铺信息
