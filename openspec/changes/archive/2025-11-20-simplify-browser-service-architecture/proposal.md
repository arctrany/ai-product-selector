# Change: 简化浏览器服务架构

## Why

当前浏览器服务存在以下问题：

1. **架构冗余**：三层架构（XuanpingBrowserService → SimplifiedBrowserService → Driver）导致职责重叠和代码重复
2. **双重单例**：global_browser_singleton 和 SimplifiedBrowserService._shared_instances 两套单例机制
3. **配置传递冗余**：配置参数经过 5 次转换（Dict → ConfigManager → BrowserServiceConfig → to_dict() → Dict → Driver）
4. **状态管理重复**：多个层级都维护 `_initialized` 和 `_browser_started` 状态
5. **代码维护困难**：冗余设计增加了维护成本和bug风险

## What Changes

### 删除冗余层
- **删除** `XuanpingBrowserService` 类（业务层封装不必要）
- **删除** `XuanpingBrowserServiceSync` 类（同步包装器冗余）
- **删除** `SimplifiedBrowserService._shared_instances` 机制（双重单例）

### 简化配置传递
- **简化** 配置传递链：BrowserConfig → Driver（移除中间转换）
- **移除** `_prepare_browser_config()` 中的重复设置
- **优化** ConfigManager 直接传递配置对象而非字典

### 统一单例管理
- **保留** `global_browser_singleton.py` 作为唯一的单例管理
- **移除** SimplifiedBrowserService 中的共享实例管理
- **简化** 初始化流程，避免多层检查

### 清理重复代码
- **移除** 双重初始化检查
- **移除** 重复的状态管理变量
- **统一** 浏览器通道选择逻辑到 Driver 层

## Impact

### 受影响的规格
- `specs/browser-service/spec.md` - 浏览器服务核心规格

### 受影响的代码
**删除文件**：
- `common/scrapers/xuanping_browser_service.py`

**修改文件**：
- `common/scrapers/global_browser_singleton.py` - 简化配置创建
- `rpa/browser/browser_service.py` - 移除 _shared_instances，简化配置传递
- 所有调用 XuanpingBrowserService 的代码 - 改为直接使用 SimplifiedBrowserService

### 受影响的业务场景
- 所有使用浏览器服务的爬虫和自动化任务
- **无破坏性变更**：保留相同的功能和接口

### 收益
- **代码减少**：删除约 700 行冗余代码
- **性能提升**：减少配置转换和状态检查
- **维护性**：更清晰的架构和单一职责
- **用户数据复用**：保持不变
- **全局单例**：更可靠的单例管理
