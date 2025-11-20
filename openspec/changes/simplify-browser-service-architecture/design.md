## Context

当前浏览器服务架构存在严重的冗余和职责混乱问题。通过 4 个 sub agent 的深入分析，我们识别出以下核心问题：

1. **三层架构过于复杂**：XuanpingBrowserService（业务层） → SimplifiedBrowserService（服务层） → SimplifiedPlaywrightBrowserDriver（驱动层）
2. **双重单例管理**：global_browser_singleton 和 SimplifiedBrowserService._shared_instances 两套机制
3. **配置传递冗余**：配置经过 5 次转换
4. **代码重复**：多层的初始化检查、状态管理、配置验证

此重构旨在简化架构、消除冗余、提升可维护性，同时确保**用户数据复用**和**全局单例**两个核心需求不受影响。

## Goals / Non-Goals

### Goals
- **简化架构**：从三层减少到两层（Service + Driver）
- **统一单例**：只保留 global_browser_singleton 一套单例机制
- **优化配置传递**：减少配置转换次数
- **删除冗余代码**：移除约 700 行冗余代码
- **保持功能不变**：用户数据复用和全局单例功能保持完全一致
- **提升性能**：减少配置转换和状态检查的开销

### Non-Goals
- **不改变外部 API**：保持对外接口兼容（但删除 XuanpingBrowserService）
- **不重写 Driver 层**：SimplifiedPlaywrightBrowserDriver 保持不变
- **不改变 Playwright 集成方式**：launch_persistent_context 等保持不变

## Decisions

### 决策 1：删除 XuanpingBrowserService 层

**理由**：
- XuanpingBrowserService 主要功能是连接到现有浏览器，但这可以由 SimplifiedBrowserService 直接处理
- 双重初始化检查和状态管理增加了复杂度
- XuanpingBrowserServiceSync 的同步包装在现代异步应用中不必要

**替代方案**：
- 保留 XuanpingBrowserService 作为业务适配层
  - ❌ 拒绝理由：增加维护成本，职责重叠
- 将 XuanpingBrowserService 合并到 SimplifiedBrowserService
  - ❌ 拒绝理由：会让 SimplifiedBrowserService 变得臃肿

**迁移策略**：
```python
# 之前
from common.scrapers.xuanping_browser_service import XuanpingBrowserServiceSync
browser_service = XuanpingBrowserServiceSync()

# 之后
from common.scrapers.global_browser_singleton import get_global_browser_service
browser_service = get_global_browser_service()
```

### 决策 2：移除 SimplifiedBrowserService._shared_instances

**理由**：
- global_browser_singleton 已经提供了全局单例管理
- 双重单例机制容易导致状态不一致
- _shared_instances 的实例键生成逻辑复杂且易出错

**替代方案**：
- 保留 _shared_instances 作为 SimplifiedBrowserService 内部的实例缓存
  - ❌ 拒绝理由：与 global_browser_singleton 功能重复
- 将 global_browser_singleton 移除，只保留 _shared_instances
  - ❌ 拒绝理由：global_browser_singleton 提供了 Profile 检测和验证，功能更完善

**实现细节**：
- 移除 `_shared_instances` 类变量
- 移除 `_instance_lock` 异步锁
- 移除 `_generate_instance_key()` 方法
- 简化 `initialize()` 和 `close()` 方法

### 决策 3：优化配置传递链

**当前流程**：
```
Dict → ConfigManager → BrowserServiceConfig → to_dict() → Dict → Driver
```

**优化后流程**：
```
Dict → BrowserServiceConfig → Driver (直接传递对象)
```

**理由**：
- 减少 to_dict() 和重新设置的开销
- 避免配置字段在转换过程中丢失
- 代码更清晰，易于理解

**实现细节**：
```python
# 优化前
def _prepare_browser_config(self) -> Dict[str, Any]:
    browser_config = self.config.browser_config.to_dict()
    if hasattr(self.config.browser_config, 'user_data_dir'):
        browser_config['user_data_dir'] = self.config.browser_config.user_data_dir
    # ... 重复设置多个字段
    return browser_config

# 优化后
def _prepare_browser_config(self) -> BrowserConfig:
    return self.config.browser_config
```

### 决策 4：保留 global_browser_singleton 作为唯一单例

**理由**：
- 提供了 Profile 检测和验证功能
- 实现了僵尸进程清理机制
- 是应用的统一入口点

**职责明确**：
- **global_browser_singleton**：负责 Profile 检测、验证、僵尸进程清理、全局单例管理
- **SimplifiedBrowserService**：负责浏览器生命周期管理、组件协调
- **SimplifiedPlaywrightBrowserDriver**：负责 Playwright API 封装

## Architecture

### 优化前
```
业务代码
    ↓
XuanpingBrowserServiceSync (同步包装)
    ↓
XuanpingBrowserService (业务层)
    ↓
global_browser_singleton (单例 1)
    ↓
SimplifiedBrowserService (服务层)
    ↓
_shared_instances (单例 2)
    ↓
SimplifiedPlaywrightBrowserDriver (驱动层)
    ↓
Playwright API
```

### 优化后
```
业务代码
    ↓
global_browser_singleton (唯一单例)
    ↓
SimplifiedBrowserService (服务层)
    ↓
SimplifiedPlaywrightBrowserDriver (驱动层)
    ↓
Playwright API
```

### 配置流程优化

**优化前**：
```
环境变量 → global_browser_singleton
    ↓
Dict 配置
    ↓
ConfigManager.load_config
    ↓
BrowserServiceConfig
    ↓
to_dict()
    ↓
_prepare_browser_config (重复设置)
    ↓
Dict 配置
    ↓
Driver
```

**优化后**：
```
环境变量 → global_browser_singleton
    ↓
BrowserServiceConfig
    ↓
Driver (直接传递对象)
```

## Risks / Trade-offs

### 风险 1：迁移成本
- **风险**：所有使用 XuanpingBrowserService 的代码需要修改
- **缓解**：
  1. 使用代码搜索工具识别所有使用位置
  2. 提供详细的迁移文档
  3. 保持 SimplifiedBrowserService 的接口不变

### 风险 2：向后兼容性
- **风险**：删除 XuanpingBrowserService 会破坏现有代码
- **缓解**：
  1. 这是内部重构，不影响外部 API
  2. 提供清晰的迁移路径
  3. 充分测试确保功能一致

### 风险 3：性能回归
- **风险**：配置优化可能引入未知的性能问题
- **缓解**：
  1. 编写性能测试
  2. 对比优化前后的性能指标
  3. 监控生产环境运行状况

### Trade-off：删除同步包装器
- **Trade-off**：XuanpingBrowserServiceSync 提供了同步接口，删除后需要使用异步
- **决策**：接受这个 trade-off，因为：
  1. 现代 Python 应用应该使用异步
  2. 同步包装器增加了复杂度
  3. 如果真的需要同步接口，可以在调用处使用 asyncio.run()

## Migration Plan

### 阶段 1：准备（1天）
1. 识别所有使用 XuanpingBrowserService 的代码位置
2. 准备迁移文档
3. 创建分支进行重构

### 阶段 2：实施重构（2-3天）
1. 删除 XuanpingBrowserService 相关代码
2. 简化 SimplifiedBrowserService
3. 优化配置传递
4. 更新所有调用代码

### 阶段 3：测试（2天）
1. 编写单元测试
2. 编写集成测试
3. 手动测试所有场景
4. 性能测试

### 阶段 4：部署（1天）
1. 部署到测试环境
2. 验证功能正常
3. 部署到生产环境
4. 监控运行状况

### Rollback Plan
如果发现重大问题：
1. 立即回滚到上一个稳定版本
2. 分析问题根因
3. 修复后重新部署

## Testing Strategy

### 单元测试
1. **测试全局单例**：验证同一实例被复用
2. **测试用户数据复用**：验证 user_data_dir 正确传递
3. **测试配置传递**：验证配置正确传递到 Driver
4. **测试 Profile 检测**：验证 Profile 检测逻辑
5. **测试僵尸进程清理**：验证清理机制

### 集成测试
1. **完整启动流程**：测试从 Profile 检测到浏览器启动的完整流程
2. **错误恢复**：测试 Profile 被锁定时的自动清理和重试
3. **多场景测试**：headless 模式、连接模式、启动模式

### 性能测试
1. **启动时间**：对比优化前后的启动时间
2. **内存使用**：对比优化前后的内存占用
3. **配置转换开销**：测量配置传递的性能

### 回归测试
1. 运行所有现有测试套件
2. 确保所有功能保持一致
3. 验证无新增 bug

## Open Questions

无待解决问题。所有设计决策已明确。

## Success Criteria

1. **代码减少**：删除约 700 行冗余代码 ✓
2. **架构简化**：从三层减少到两层 ✓
3. **功能保持**：用户数据复用和全局单例功能完全一致 ✓
4. **测试覆盖**：所有核心功能有测试覆盖 ✓
5. **性能提升**：配置传递和初始化更快 ✓
6. **无回归**：所有现有功能正常工作 ✓
