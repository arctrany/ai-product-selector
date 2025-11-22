# Spec Delta: browser-service

## 变更类型
MODIFICATION - 确保browser-service规范完全同步化，移除异步API依赖

## 变更内容

### 修改 Requirement: 同步浏览器服务架构
确保浏览器服务提供纯同步的API接口。

#### Scenario: Playwright同步API集成
- **WHEN** 启动浏览器实例时
- **THEN** 系统应使用Playwright的sync_api
- **AND** 使用sync_playwright()上下文管理器
- **AND** 所有页面操作都是同步阻塞执行

#### Scenario: 同步元素查找
- **WHEN** 查找页面元素时
- **THEN** 使用同步的query_selector方法
- **AND** 移除所有异步的Locator.count()等调用
- **AND** 方法调用立即返回结果

### 修改 Requirement: 服务初始化
确保浏览器服务初始化是同步的。

#### Scenario: 同步初始化流程
- **WHEN** 初始化浏览器服务时
- **THEN** 使用同步的初始化流程
- **AND** 不创建或依赖任何事件循环
- **AND** 初始化完成后立即可用

## 技术实现说明

**确保的功能**：
- 使用Playwright sync_api而非async_api
- 所有方法都是同步方法
- 不依赖asyncio事件循环

**保持不变**：
- 浏览器启动和连接逻辑
- 平台兼容性支持
- 配置管理机制

