# Change: 重构核心架构以解决并发浏览器、配置重复、任务控制和架构违规问题

## Why

当前AI选品系统存在7个关键架构问题，影响系统的稳定性、可维护性和性能：

1. **浏览器使用不规范**：部分组件可能绕过全局浏览器单例直接创建浏览器实例，导致资源浪费和潜在的稳定性问题
2. **配置管理混乱**：UIConfig和GoodStoreSelectorConfig存在重复字段，配置传递复杂，违反DRY原则
3. **任务控制不完整**：TaskManager的暂停功能只更新状态未实际暂停任务，进度报告机制不完善
4. **架构违规**：GoodStoreSelector绕过ScrapingOrchestrator直接调用scrapers，违反分层架构原则
5. **TaskManager路径管理重复**：TaskManagerConfig硬编码路径逻辑，与系统统一的get_data_directory()功能重复，违反DRY原则且存在硬编码问题
6. **配置参数过度复杂**：系统包含过度复杂的重试退避机制配置和未实际使用的并发配置，增加了系统复杂度而无实际价值
7. **CLI logging配置接口不匹配**：cli/main.py调用setup_logging(log_level=...)但common/logging_config.py函数只接受level和log_file参数，导致CLI基础功能无法正常启动

这些问题导致系统复杂度增加、维护困难、资源浪费，需要进行系统性重构。

## What Changes

- 强制所有组件使用现有的全局浏览器单例，确保单一浏览器实例
- **BREAKING** 统一配置管理，合并UIConfig和GoodStoreSelectorConfig的重复字段
- 完善TaskManager的任务控制机制，实现真正的任务暂停和恢复
- 增强任务进度报告机制，提供实时准确的进度信息
- 重构GoodStoreSelector，强制通过ScrapingOrchestrator调用scrapers
- **BREAKING** 重构TaskManager配置路径管理，使用系统统一的get_data_directory()替代硬编码路径
- 移除TaskManagerConfig中的重复路径管理逻辑，消除"xuanping"硬编码目录名
- **BREAKING** 简化配置参数设计，移除过度复杂的重试退避机制配置（exponential_backoff, backoff_multiplier, max_backoff_delay_s）
- **BREAKING** 移除未实际使用的并发配置参数（max_concurrent_stores, max_concurrent_products）
- 扩展TaskControlContext，添加系统运行控制参数和任务配置参数支持
- 修复CLI logging配置接口不匹配问题，确保CLI基础功能正常工作
- 实现数据迁移机制，确保现有用户数据的向后兼容性
- 更新相关测试以移除并发浏览器测试用例和路径硬编码测试

## Impact

- Affected specs: browser-service, config-layer, task-manager, business-layer
- Affected code: 
  - `common/scrapers/global_browser_singleton.py` - 浏览器单例管理
  - `cli/models.py` - CLI配置模型
  - `common/config/base_config.py` - 核心配置管理
  - `task_manager/controllers.py` - 任务管理器
  - `task_manager/config.py` - 任务管理器配置路径重构
  - `cli/task_controller_adapter.py` - 任务控制适配器
  - `cli/main.py` - CLI主入口文件logging配置修复
  - `common/logging_config.py` - logging配置接口统一
  - `good_store_selector.py` - 核心业务逻辑
  - `packaging/resource_path.py` - 统一路径管理依赖
  - `tests/` - 相关测试文件
- Breaking changes: API变更、配置格式变更、浏览器使用方式变更、TaskManager默认存储路径变更
- Migration needed: 现有配置文件需要更新，TaskManager数据需要迁移，测试用例需要修改
