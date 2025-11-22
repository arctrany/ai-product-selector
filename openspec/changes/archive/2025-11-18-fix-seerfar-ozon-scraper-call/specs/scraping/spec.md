## MODIFIED Requirements

### Requirement: SeerfarScraper OZON 数据提取
SeerfarScraper 在抓取 Seerfar 商品列表后，点击商品图片跳转到 OZON 详情页时，MUST 使用 OzonScraper 的公共接口方法正确提取 OZON 商品数据。

#### Scenario: 调用 OzonScraper 公共接口
- **WHEN** SeerfarScraper 需要从 OZON 详情页提取数据
- **THEN** 系统 SHALL 调用 `OzonScraper.scrape(url, include_competitors=True)` 方法
- **AND** 系统 SHALL 正确处理返回的 `ScrapingResult` 对象
- **AND** 系统 SHALL 从 `result.data` 中提取 `price_data`、`competitors`、`erp_data`

#### Scenario: 优化浏览器资源管理
- **WHEN** SeerfarScraper 打开临时页面跳转到 OZON URL
- **THEN** 系统 SHALL 获取 OZON URL 后立即关闭临时页面
- **AND** 系统 SHALL 让 OzonScraper 使用自己的浏览器服务进行抓取
- **AND** 系统 SHALL NOT 同时运行两个浏览器实例

#### Scenario: 错误处理
- **WHEN** OzonScraper 抓取失败（`result.success == False`）
- **THEN** 系统 SHALL 记录错误日志包含 `result.error_message`
- **AND** 系统 SHALL 继续处理而不中断整个流程
