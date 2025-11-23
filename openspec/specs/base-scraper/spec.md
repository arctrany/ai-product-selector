# base-scraper Specification

## Purpose
提供统一的业务层爬虫基础类，支持同步数据抓取操作，确保浏览器资源管理和错误处理的一致性。
## Requirements
### Requirement: 同步数据抓取接口
系统 SHALL 提供统一的同步数据抓取接口。

#### Scenario: 基础页面数据抓取
- **WHEN** 调用 `scrape_page_data()` 方法
- **THEN** 系统应同步执行数据抓取操作
- **AND** 返回抓取结果或抛出异常
- **AND** 确保超时控制在合理范围内

#### Scenario: 浏览器资源清理
- **WHEN** 调用 `close()` 方法
- **THEN** 系统应同步关闭浏览器资源
- **AND** 释放所有相关连接
- **AND** 不依赖异步事件循环

### Requirement: 错误处理和超时机制
系统 SHALL 提供统一的错误处理和超时控制。

#### Scenario: 操作超时处理
- **WHEN** 数据抓取操作超过预设时间
- **THEN** 系统应抛出 TimeoutError 异常
- **AND** 包含具体的超时时间信息
- **AND** 清理已分配的资源

#### Scenario: 网络错误重试
- **WHEN** 遇到可恢复的网络错误
- **THEN** 系统应自动重试最多3次
- **AND** 使用指数退避策略
- **AND** 记录重试日志

### Requirement: 浏览器服务集成
系统 SHALL 与 browser_service 的同步方法集成。

#### Scenario: 使用同步浏览器方法
- **WHEN** 需要浏览器操作时
- **THEN** 系统应调用 browser_service 的 *_sync 方法
- **AND** 不使用异步包装器
- **AND** 直接处理同步操作结果

#### Scenario: 浏览器连接管理
- **WHEN** 初始化爬虫实例
- **THEN** 系统应确保浏览器连接可用
- **AND** 验证必要的浏览器功能
- **AND** 设置合适的超时参数

### Requirement: 同步化浏览器驱动接口
基础Scraper系统SHALL使用完全同步的浏览器驱动接口，移除所有异步依赖。

#### Scenario: 浏览器初始化
- **WHEN** 创建浏览器驱动实例
- **THEN** 使用同步的初始化方法，无需await关键字
- **AND** 初始化过程不依赖asyncio事件循环

#### Scenario: 页面导航
- **WHEN** 导航到指定URL  
- **THEN** 使用同步的导航方法完成跳转
- **AND** 方法调用立即返回结果，无需await

#### Scenario: 元素交互
- **WHEN** 查找或操作页面元素
- **THEN** 使用同步的元素查找和操作方法
- **AND** 所有DOM操作都是阻塞式同步执行

### Requirement: 禁止异步操作
系统 SHALL 完全禁止在业务层使用异步操作。

#### Scenario: 不包含异步方法
- **WHEN** 定义业务抓取方法时
- **THEN** 所有方法必须是同步方法
- **AND** 不使用 async/await 关键字
- **AND** 不依赖事件循环机制

#### Scenario: 移除异步包装器
- **WHEN** 系统运行时
- **THEN** 不应包含 run_async 等异步包装方法
- **AND** 不应有异步同步转换逻辑
- **AND** 保持简单的同步调用链

### Requirement: 统一配置和日志
系统 SHALL 提供统一的配置管理和日志记录。

#### Scenario: 超时配置管理
- **WHEN** 执行不同类型的操作时
- **THEN** 系统应根据操作类型设置合适的超时
- **AND** 页面导航：10-30秒
- **AND** 元素查找：5-10秒
- **AND** 数据抓取：15-60秒

#### Scenario: 操作日志记录
- **WHEN** 执行关键操作时
- **THEN** 系统应记录详细的操作日志
- **AND** 包含操作类型和耗时
- **AND** 包含成功/失败状态
- **AND** 包含错误详情（如有）

