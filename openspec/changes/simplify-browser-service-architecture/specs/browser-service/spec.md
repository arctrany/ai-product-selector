## MODIFIED Requirements

### Requirement: 全局浏览器单例管理
系统 SHALL 通过 global_browser_singleton 提供唯一的全局浏览器实例管理机制，确保整个应用只有一个浏览器进程运行。

#### Scenario: 多次获取浏览器服务实例
- **WHEN** 业务代码多次调用 `get_global_browser_service()`
- **THEN** 返回相同的浏览器服务实例
- **AND** 不会创建多个浏览器进程

#### Scenario: 浏览器实例复用
- **WHEN** 浏览器服务已初始化
- **AND** 再次调用 `get_global_browser_service()`
- **THEN** 直接返回已存在的实例
- **AND** 不重新初始化浏览器

### Requirement: 用户数据目录和 Profile 管理
系统 SHALL 支持使用指定的用户数据目录（user_data_dir）启动浏览器，以复用用户的插件、登录状态和浏览数据。

#### Scenario: 自动检测最近使用的 Profile
- **WHEN** 启动浏览器服务
- **THEN** 自动检测最近使用的浏览器 Profile
- **AND** 使用该 Profile 的完整路径作为 user_data_dir

#### Scenario: Profile 被锁定时自动恢复
- **WHEN** 检测到 Profile 被锁定
- **THEN** 自动清理僵尸浏览器进程
- **AND** 等待 Profile 解锁
- **AND** 重新验证 Profile 可用性
- **AND** 继续启动浏览器

#### Scenario: Profile 清理失败时退出程序
- **WHEN** Profile 被锁定
- **AND** 僵尸进程清理失败
- **THEN** 记录详细错误信息
- **AND** 程序退出并返回错误码

### Requirement: 浏览器服务生命周期管理
系统 SHALL 通过 SimplifiedBrowserService 管理浏览器的完整生命周期，包括初始化、启动、导航和关闭。

#### Scenario: 浏览器服务初始化
- **WHEN** 调用 `initialize()` 方法
- **THEN** 创建浏览器驱动实例
- **AND** 启动浏览器进程
- **AND** 创建浏览器页面对象
- **AND** 返回成功状态

#### Scenario: 初始化失败时的处理
- **WHEN** 浏览器初始化失败
- **THEN** 清理失败状态
- **AND** 重置全局单例
- **AND** 程序退出并返回错误码

#### Scenario: 浏览器服务关闭
- **WHEN** 调用 `close()` 方法
- **THEN** 关闭浏览器驱动
- **AND** 清理浏览器资源
- **AND** 重置初始化状态

### Requirement: 配置参数传递
系统 SHALL 支持直接传递配置对象到浏览器驱动，避免不必要的配置转换。

#### Scenario: 配置对象直接传递
- **WHEN** SimplifiedBrowserService 初始化浏览器驱动
- **THEN** 直接传递 BrowserConfig 对象给驱动
- **AND** 不进行 to_dict() 转换
- **AND** 不重复设置配置参数

#### Scenario: 用户数据目录配置传递
- **WHEN** global_browser_singleton 创建配置
- **AND** 设置 user_data_dir 参数
- **THEN** user_data_dir 直接传递到浏览器驱动
- **AND** 只设置一次，不重复传递

## REMOVED Requirements

### Requirement: XuanpingBrowserService 业务层封装
**Reason**: 功能重复，与 SimplifiedBrowserService 职责重叠

**Migration**: 
```python
# 之前
from common.scrapers.xuanping_browser_service import XuanpingBrowserServiceSync
browser_service = XuanpingBrowserServiceSync()
await browser_service.initialize()

# 之后
from common.scrapers.global_browser_singleton import get_global_browser_service
browser_service = get_global_browser_service()
await browser_service.initialize()
```

### Requirement: 双重浏览器实例缓存
**Reason**: SimplifiedBrowserService._shared_instances 与 global_browser_singleton 功能重复

**Migration**: 
全局单例管理统一由 global_browser_singleton 负责，SimplifiedBrowserService 不再维护 _shared_instances。

### Requirement: 同步包装器 XuanpingBrowserServiceSync
**Reason**: 现代异步应用不需要同步包装器，增加不必要的复杂度

**Migration**: 
直接使用异步接口，如需同步调用可使用 `asyncio.run()`：
```python
# 之前
browser_service = XuanpingBrowserServiceSync()
browser_service.initialize()

# 之后
import asyncio
browser_service = get_global_browser_service()
asyncio.run(browser_service.initialize())
```

### Requirement: 配置多次转换和重复设置
**Reason**: 配置经过 5 次转换且重复设置参数，造成性能浪费和维护困难

**Migration**: 
配置直接传递，不再进行 to_dict() 转换和重复设置。

## ADDED Requirements

### Requirement: 僵尸浏览器进程自动清理
系统 SHALL 在检测到 Profile 被锁定时，自动清理僵尸浏览器进程，确保浏览器能够正常启动。

#### Scenario: 检测到僵尸进程时自动清理
- **WHEN** Profile 检测失败且被锁定
- **THEN** 调用 `kill_browser_processes()` 清理僵尸进程
- **AND** 等待进程完全退出
- **AND** 等待 Profile 解锁（最多 5 秒）

#### Scenario: 跨平台僵尸进程清理
- **WHEN** 执行僵尸进程清理
- **THEN** 根据操作系统选择对应的清理命令
- **AND** macOS 使用 `pkill -9 -f "Microsoft Edge"`
- **AND** Windows 使用 `taskkill /F /IM msedge.exe /T`
- **AND** Linux 使用 `pkill -9 -f "microsoft-edge"`

### Requirement: Profile 解锁等待机制
系统 SHALL 提供 Profile 解锁等待机制，在清理僵尸进程后等待 Profile 锁定文件被删除。

#### Scenario: 等待 Profile 解锁成功
- **WHEN** 清理僵尸进程后
- **AND** Profile 锁定文件仍然存在
- **THEN** 每 0.5 秒检查一次锁定状态
- **AND** 最多等待 5 秒
- **AND** 如果 Profile 解锁则返回成功

#### Scenario: 等待超时仍被锁定
- **WHEN** 等待 5 秒后 Profile 仍然被锁定
- **THEN** 返回失败状态
- **AND** 记录详细错误信息
- **AND** 程序退出

### Requirement: 简化的架构层次
系统 SHALL 采用简化的两层架构：服务层（SimplifiedBrowserService）和驱动层（SimplifiedPlaywrightBrowserDriver）。

#### Scenario: 业务代码直接访问服务层
- **WHEN** 业务代码需要使用浏览器服务
- **THEN** 通过 global_browser_singleton 获取 SimplifiedBrowserService 实例
- **AND** 不需要经过额外的业务适配层

#### Scenario: 服务层直接管理驱动层
- **WHEN** SimplifiedBrowserService 需要浏览器操作
- **THEN** 直接调用 SimplifiedPlaywrightBrowserDriver 方法
- **AND** 不经过中间层转换
