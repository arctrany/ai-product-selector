# Browser Service Specification

## Overview
浏览器服务规范定义了浏览器启动、连接、管理的核心行为。

---

## MODIFIED Requirements

### REQ-BS-001: 浏览器启动策略
**Priority**: P0  
**Status**: Modified

**Description**:
系统应支持智能浏览器启动策略，根据运行状态自动选择连接或启动。

**Previous Behavior**:
- 检测到没有运行中的浏览器 → 报错退出
- 要求用户手动启动浏览器

**New Behavior**:
- 检测到有运行中的浏览器 → 连接
- 检测到没有运行中的浏览器 → 自动启动

**Scenarios**:

#### Scenario 1: 有运行中的浏览器
```
GIVEN 用户已手动启动浏览器并开启调试端口 9222
WHEN 系统初始化浏览器服务
THEN 系统应连接到已运行的浏览器
AND 保留用户的登录态和会话
AND 输出日志 "🔗 检测到现有浏览器，将连接到端口 9222"
AND 输出日志 "✅ 成功连接到现有浏览器"
```

#### Scenario 2: 没有运行中的浏览器
```
GIVEN 没有运行中的浏览器
WHEN 系统初始化浏览器服务
THEN 系统应自动启动浏览器
AND 使用系统默认的用户数据目录
AND 开启调试端口
AND 输出日志 "🚀 未检测到浏览器，将自动启动"
AND 输出日志 "✅ 浏览器启动成功"
```

#### Scenario 3: 启动失败
```
GIVEN 没有运行中的浏览器
AND 浏览器启动失败（如：可执行文件不存在）
WHEN 系统尝试启动浏览器
THEN 系统应输出详细错误信息
AND 退出程序（不重试）
```

---

### REQ-BS-002: 配置管理
**Priority**: P0  
**Status**: Modified

**Description**:
系统应从统一的配置中读取浏览器启动参数。

**Previous Behavior**:
- 强制要求 `connect_to_existing = True`
- 不支持启动模式配置

**New Behavior**:
- 自动设置 `connect_to_existing`（根据检测结果）
- 支持 `headless` 模式配置
- 使用系统默认用户数据目录

**Configuration Schema**:
```json
{
  "browser": {
    "browser_type": "edge",
    "headless": false,
    "timeout_seconds": 30,
    "max_retries": 3,
    "required_login_domains": ["seerfar.cn", "www.maozierp.com"],
    "debug_port": 9222
  }
}
```

**Scenarios**:

#### Scenario 1: 读取 headless 配置
```
GIVEN 配置文件设置 "headless": true
WHEN 系统启动浏览器
THEN 系统应以 headless 模式启动浏览器
AND 输出日志 "🚀 未检测到浏览器，将自动启动（headless=True）"
```

#### Scenario 2: 使用默认配置
```
GIVEN 配置文件未设置 headless
WHEN 系统启动浏览器
THEN 系统应使用默认值 headless=False
AND 以正常模式启动浏览器
```

---

### REQ-BS-003: 错误处理
**Priority**: P1  
**Status**: Modified

**Description**:
系统应提供清晰的错误信息，不再要求用户手动启动浏览器。

**Previous Behavior**:
```
❌ 未检测到运行中的 Edge 浏览器
💡 请先手动启动 Edge 浏览器，或运行启动脚本：
   ./start_edge_with_debug.sh
```

**New Behavior**:
```
# 连接失败时
❌ 连接现有浏览器失败
💡 解决方案：
   1. 确保浏览器的调试端口 9222 已开启
   2. 或关闭所有浏览器窗口，让系统自动启动

# 启动失败时
❌ 浏览器启动失败
💡 请检查浏览器是否已正确安装
```

**Scenarios**:

#### Scenario 1: 连接失败
```
GIVEN 检测到浏览器在运行
AND CDP 端口不可用
WHEN 系统尝试连接
THEN 系统应输出连接失败错误
AND 提供解决方案
AND 退出程序
```

#### Scenario 2: 启动失败
```
GIVEN 没有运行中的浏览器
AND 浏览器启动失败
WHEN 系统尝试启动浏览器
THEN 系统应输出启动失败错误
AND 提供解决方案
AND 退出程序
```

---

## ADDED Requirements

### REQ-BS-004: 利用现有实现
**Priority**: P0  
**Status**: New

**Description**:
系统应利用现有的 `PlaywrightBrowserDriver._launch_browser()` 方法，不重复实现。

**Rationale**:
`PlaywrightBrowserDriver._launch_browser()` 已经实现了：
- 跨平台支持（macOS/Windows/Linux）
- 多浏览器支持（Edge/Chrome）
- 用户数据目录处理
- Profile 选择（包括 Default Profile）
- 扩展支持
- 反检测脚本注入

**Implementation**:
- 移除阻止调用 `_launch_browser()` 的限制
- 通过 `SimplifiedPlaywrightBrowserDriver.initialize()` 调用
- 配置 `connect_to_existing=False` 触发启动逻辑

**Scenarios**:

#### Scenario 1: 调用现有实现
```
GIVEN 配置 connect_to_existing=False
WHEN 系统初始化 SimplifiedPlaywrightBrowserDriver
THEN 系统应调用 initialize() 方法
AND initialize() 应调用 _launch_browser()
AND 使用现有的成熟实现
```

---

## Implementation Notes

### 关键修改点

#### 1. SimplifiedBrowserService.initialize()
**文件**: `rpa/browser/browser_service.py`

**移除**:
```python
if not connect_to_existing:
    raise RuntimeError("未启用连接模式")
```

**添加**:
```python
if connect_to_existing:
    # 连接逻辑（保留）
    ...
else:
    # 启动逻辑（新增）
    self.browser_driver = SimplifiedPlaywrightBrowserDriver(browser_config)
    success = await self.browser_driver.initialize()
```

#### 2. XuanpingBrowserService._create_browser_config()
**文件**: `common/scrapers/xuanping_browser_service.py`

**修改**:
```python
has_browser = self._check_existing_browser(debug_port)

if has_browser:
    config['connect_to_existing'] = True
    self.logger.info(f"🔗 检测到现有浏览器")
else:
    config['connect_to_existing'] = False
    config['headless'] = self.config.get('browser', {}).get('headless', False)
    self.logger.info(f"🚀 未检测到浏览器，将自动启动")
```

### 现有实现的优势

`PlaywrightBrowserDriver._launch_browser()` 提供：
1. **跨平台路径处理**：自动检测操作系统并使用正确的路径
2. **默认用户数据目录**：自动使用系统默认的浏览器用户数据目录
3. **Profile 处理**：自动选择 Default Profile
4. **扩展支持**：保留用户的扩展和设置
5. **反检测**：注入反检测脚本，避免被识别为自动化
6. **错误处理**：完善的错误处理和日志输出

### 不需要实现的功能

以下功能**已经存在**，不需要重新实现：
- ❌ Profile 扫描和选择
- ❌ 登录态检查
- ❌ 浏览器启动命令生成
- ❌ 跨平台路径处理
- ❌ 进程管理

只需要：
- ✅ 移除阻止调用的限制
- ✅ 修改配置逻辑

---

## Testing Requirements

### Unit Tests
不需要新的单元测试，现有测试应该通过。

### Integration Tests
1. 测试自动启动功能
2. 测试连接功能（确保不破坏）
3. 测试 headless 模式

### Manual Tests
1. 没有浏览器时启动程序
2. 有浏览器时启动程序
3. headless 模式测试

---

## Migration Guide

### For Users
无需任何操作，系统会自动处理：
- 有运行中的浏览器 → 自动连接（原有行为）
- 没有运行中的浏览器 → 自动启动（新功能）

### For Developers
如果有自定义的浏览器启动逻辑，需要：
1. 移除手动启动浏览器的代码
2. 依赖系统的自动启动功能
3. 配置 `headless` 参数（如果需要）

---

## Related Specifications
- [Config Management](../config-management/spec.md) - 配置管理规范
- [Browser Service](../../specs/browser-service/spec.md) - 浏览器服务规范（原有）

---

## Key Insight

**这是一个"解锁"变更，而不是重新实现！**

现有的代码已经实现了所有需要的功能，我们只需要：
1. 移除阻止使用它的限制
2. 修改配置逻辑以触发启动模式
3. 让现有的成熟代码发挥作用

**代码修改量**：< 50 行  
**功能增强**：巨大（从"必须手动启动"到"自动启动"）  
**风险**：极低（使用现有的成熟实现）
