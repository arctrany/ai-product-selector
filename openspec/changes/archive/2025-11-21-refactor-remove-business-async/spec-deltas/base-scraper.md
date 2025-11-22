# Spec Delta: base-scraper

## 变更类型
NEW - 创建新的 base-scraper capability 规范

## 变更内容

这是一个全新的 capability，为统一的业务层爬虫基础类提供规范定义。

### 核心价值
- 提供统一的同步数据抓取基础架构
- 消除异步/同步混合架构的复杂性
- 确保所有业务爬虫类的一致性行为

### 主要功能
- 同步数据抓取接口
- 统一的错误处理和超时机制
- 浏览器服务集成
- 配置和日志管理

## 与现有 capabilities 的关系

### 与 browser-service 的集成
- 依赖 browser-service 的同步方法
- 不使用 browser-service 的异步功能
- 提供业务层的浏览器操作封装

### 与业务 scraper 的关系
- 作为 seerfar-scraper、ozon-scraper 等的基类
- 提供通用的基础设施方法
- 定义统一的接口规范

## 架构影响

### 简化调用链
**Before**: 业务方法 → run_async → 异步包装 → browser_service 同步方法
**After**: 业务方法 → browser_service 同步方法

### 消除复杂性
- 移除事件循环管理
- 移除异步同步转换
- 简化错误处理逻辑

## 迁移指导

### 现有代码迁移
1. 移除所有 `async def` 声明
2. 移除 `await` 关键字
3. 直接调用同步方法
4. 更新错误处理逻辑

### 测试更新
1. 移除异步测试装置
2. 使用同步测试方法
3. 更新模拟对象配置
4. 验证超时处理逻辑
