# Browser Service Capability - Spec Delta

## MODIFIED Requirements

### Requirement: 浏览器对象访问
`XuanpingBrowserServiceSync` SHALL 直接暴露 `page`、`browser`、`context` 属性，以简化 API 访问。

#### Scenario: 初始化后访问 page 对象
- **GIVEN** 创建了 `XuanpingBrowserServiceSync` 实例
- **WHEN** 调用 `initialize()` 和 `start_browser()`
- **THEN** `service.page` 应该返回有效的 Playwright Page 对象
- **AND** `service.browser` 应该返回有效的 Browser 对象
- **AND** `service.context` 应该返回有效的 BrowserContext 对象

#### Scenario: 浏览器未启动时访问
- **GIVEN** 创建了 `XuanpingBrowserServiceSync` 实例
- **WHEN** 未调用 `start_browser()`
- **THEN** `service.page` 应该为 `None`
- **AND** `service.browser` 应该为 `None`
- **AND** `service.context` 应该为 `None`

#### Scenario: 简化的 API 使用
- **GIVEN** 浏览器已启动
- **WHEN** 在 extractor 函数中访问 page
- **THEN** 应该使用 `browser_service.page` 而不是 `browser_service.async_service.browser_service.browser_driver.page`
- **AND** 代码应该更简洁易读


