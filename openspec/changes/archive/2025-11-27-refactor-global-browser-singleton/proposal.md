# Change: 重构Global Browser Singleton到Browser Service

## Why
当前项目存在循环依赖问题：`common/scrapers/global_browser_singleton.py` 和 `rpa/browser/browser_service.py` 之间相互依赖，违反了架构分层原则。Global browser singleton作为全局单例管理器，应该属于基础设施层(RPA)，但被放置在业务逻辑层(Common)中，导致基础设施层反向依赖业务逻辑层。

## What Changes
- 将global_browser_singleton的全局单例管理功能整合到SimplifiedBrowserService类中
- 添加新的类级别单例访问方法：`get_global_instance()`, `has_global_instance()`, `reset_global_instance()`
- 保留`common/scrapers/global_browser_singleton.py`作为向后兼容的包装器
- 添加deprecation警告，引导用户迁移到新API
- 创建完整的单元测试覆盖新功能

## Impact
- Affected specs: browser (SimplifiedBrowserService)
- Affected code: 
  - `rpa/browser/browser_service.py` - 添加单例管理功能
  - `common/scrapers/global_browser_singleton.py` - 改为兼容性包装器
  - 5个Scraper类文件 - 使用global_browser_singleton的代码
  - 1个服务协调器文件 - 健康检查相关代码
  - 多个测试文件 - mock和测试代码
- Breaking changes: **无** - 通过兼容性包装器保持向后兼容
- Migration path: 渐进式迁移，现有代码无需立即修改