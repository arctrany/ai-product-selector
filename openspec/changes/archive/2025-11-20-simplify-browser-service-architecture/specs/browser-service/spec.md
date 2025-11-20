



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
