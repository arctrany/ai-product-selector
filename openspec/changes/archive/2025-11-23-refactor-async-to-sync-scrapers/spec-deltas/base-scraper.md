# Spec Delta: base-scraper

## 变更类型
MODIFICATION - 确保base-scraper规范完全同步化，移除任何异步依赖

## 变更内容

### 修改 Requirement: 同步数据抓取接口
确保所有数据抓取操作都是完全同步的，不依赖异步机制。

#### Scenario: 完全同步的浏览器操作
- **WHEN** 执行任何浏览器操作时
- **THEN** 所有操作必须是同步阻塞执行
- **AND** 不使用async/await关键字
- **AND** 不依赖asyncio事件循环

### 修改 Requirement: 浏览器服务集成
确保与browser-service的集成完全使用同步方法。

#### Scenario: 使用同步浏览器方法
- **WHEN** 需要浏览器操作时
- **THEN** 系统应调用browser_service的同步方法
- **AND** 不使用异步包装器
- **AND** 直接处理同步操作结果

## 技术实现说明

**确保的功能**：
- 所有方法都是同步方法（无async关键字）
- 所有浏览器操作都是同步阻塞执行
- 错误处理使用同步异常机制

**保持不变**：
- 现有的同步接口定义
- 超时和错误处理机制
- 配置和日志管理

