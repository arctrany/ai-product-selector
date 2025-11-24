## ADDED Requirements

### Requirement: 强制单一浏览器实例使用
所有系统组件SHALL通过全局浏览器单例获取浏览器服务，禁止直接创建新的浏览器实例。

#### Scenario: 全局浏览器单例获取
- **WHEN** 任何组件需要浏览器服务时
- **THEN** 必须通过get_global_browser_service()函数获取
- **AND** 不允许直接实例化BrowserService或SimplifiedBrowserService

#### Scenario: Scraper浏览器使用规范
- **WHEN** BaseScraper及其子类需要浏览器时
- **THEN** SHALL使用全局浏览器单例
- **AND** 不允许在scraper中创建独立的浏览器实例

#### Scenario: 浏览器使用串行化
- **WHEN** 多个scraper同时需要使用浏览器时
- **THEN** 通过全局锁机制确保串行化访问
- **AND** 前一个操作完成后才能开始下一个操作

## MODIFIED Requirements

### Requirement: 全局浏览器服务管理
现有的全局浏览器单例实现SHALL被所有组件强制使用，确保系统中只有一个浏览器实例运行。

#### Scenario: 浏览器实例验证
- **WHEN** 系统启动时
- **THEN** 验证只有一个浏览器服务实例存在
- **AND** 所有组件都通过相同的实例访问浏览器功能

#### Scenario: 浏览器资源共享
- **WHEN** 多个scraper需要浏览器功能时
- **THEN** 共享同一个浏览器实例
- **AND** 通过队列机制管理并发访问

## REMOVED Requirements

### Requirement: 独立浏览器实例创建
**Reason**: 禁止在各个组件中直接创建浏览器实例
**Migration**: 所有浏览器使用改为通过get_global_browser_service()获取
