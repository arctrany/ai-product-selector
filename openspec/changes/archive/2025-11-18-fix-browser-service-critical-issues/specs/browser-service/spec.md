## ADDED Requirements

### Requirement: 浏览器复用逻辑的完整实现
系统SHALL正确实现浏览器复用逻辑，确保检测到现有浏览器时能够连接而非启动新实例。

#### Scenario: 检测到现有浏览器时连接
- **WHEN** 通过端口检查检测到现有浏览器实例
- **THEN** 系统应使用 Playwright 的 connect_over_cdp 连接到现有浏览器
- **AND** 不应尝试启动新的浏览器进程
- **AND** 记录连接成功日志

#### Scenario: 未检测到现有浏览器时启动新实例
- **WHEN** 端口检查未发现现有浏览器
- **THEN** 系统应启动新的浏览器实例
- **AND** 使用配置的启动参数
- **AND** 记录启动成功日志

#### Scenario: 连接现有浏览器失败时的降级
- **WHEN** 检测到现有浏览器但连接失败
- **THEN** 系统应记录警告日志
- **AND** 尝试启动新的浏览器实例作为降级方案
- **AND** 提示用户可能存在端口冲突

#### Scenario: 配置传递的完整性
- **WHEN** 设置 connect_to_existing 配置
- **THEN** SimplifiedBrowserService 应读取并使用该配置
- **AND** PlaywrightBrowserDriver 应根据配置选择连接或启动
- **AND** 配置不应被忽略或丢失

### Requirement: 浏览器对象更新错误处理
系统SHALL在浏览器对象更新失败时提供明确的错误信息和异常处理。

#### Scenario: 更新成功
- **WHEN** 浏览器已正确启动且驱动可用
- **THEN** 系统应成功更新 page、browser、context 对象
- **AND** 所有对象应不为 None
- **AND** 记录调试日志

#### Scenario: 驱动未初始化
- **WHEN** 浏览器驱动为 None
- **THEN** 系统应抛出 BrowserError 异常
- **AND** 异常消息应包含"浏览器驱动未初始化"
- **AND** 记录错误日志

#### Scenario: Page 对象为 None
- **WHEN** 驱动存在但 page 对象为 None
- **THEN** 系统应抛出 BrowserError 异常
- **AND** 异常消息应包含"page 对象为 None"
- **AND** 提示浏览器可能未正确启动

#### Scenario: 属性访问失败
- **WHEN** 访问驱动属性时发生 AttributeError 或 TypeError
- **THEN** 系统应抛出 BrowserError 异常
- **AND** 异常应包含原始错误信息
- **AND** 使用异常链（from e）保留堆栈信息

### Requirement: 单例模式下的引用计数管理
系统SHALL使用引用计数机制管理单例浏览器服务的生命周期。

#### Scenario: 创建实例增加引用
- **WHEN** 创建新的浏览器服务实例
- **THEN** 引用计数应增加 1
- **AND** 使用线程锁保证计数操作的原子性

#### Scenario: 普通关闭检查引用计数
- **WHEN** 调用 close() 方法且 force=False
- **THEN** 引用计数应减少 1
- **AND** 如果引用计数大于 0，不关闭浏览器
- **AND** 记录剩余引用数量
- **AND** 返回 True 表示操作成功

#### Scenario: 最后一个引用关闭浏览器
- **WHEN** 调用 close() 且引用计数减为 0
- **THEN** 系统应真正关闭浏览器
- **AND** 重置初始化状态
- **AND** 记录关闭成功日志

#### Scenario: 强制关闭忽略引用计数
- **WHEN** 调用 close(force=True)
- **THEN** 系统应立即关闭浏览器
- **AND** 引用计数应重置为 0
- **AND** 忽略其他实例的引用

### Requirement: 同步包装器的自动状态同步
系统SHALL在可能启动浏览器的操作后自动更新浏览器对象。

#### Scenario: navigate_to 后自动更新
- **WHEN** 调用 navigate_to() 成功
- **THEN** 系统应自动调用 _update_browser_objects()
- **AND** page、browser、context 应被正确更新
- **AND** 后续操作可以直接使用这些对象

#### Scenario: initialize 后自动更新
- **WHEN** 调用 initialize() 成功且浏览器已启动
- **THEN** 系统应自动更新浏览器对象
- **AND** 确保对象可用

#### Scenario: scrape_page_data 中的更新
- **WHEN** 在 scrape_page_data 的 wrapper 中
- **THEN** 系统应在提取数据前更新浏览器对象
- **AND** 确保提取函数能访问到有效的 page 对象

### Requirement: 浏览器驱动对象的空值检查
系统SHALL在访问浏览器驱动对象前进行空值检查，避免 NoneType 错误。

#### Scenario: 导航前检查驱动对象
- **WHEN** 调用 navigate_to() 方法
- **THEN** 系统应先检查 browser_driver 是否为 None
- **AND** 如果为 None，应抛出 BrowserError 异常
- **AND** 异常消息应明确指出驱动未初始化

#### Scenario: 驱动初始化失败后的清理
- **WHEN** browser_driver.initialize() 返回 False
- **THEN** 系统应将 browser_driver 设为 None
- **AND** 记录详细的失败原因
- **AND** 确保后续代码不会访问未初始化的驱动

#### Scenario: 访问路径的逐层验证
- **WHEN** 需要访问 async_service.browser_service.browser_driver.page
- **THEN** 系统应逐层检查每个对象是否为 None
- **AND** 在第一个 None 处抛出明确的异常
- **AND** 异常消息应指出具体哪一层为 None

### Requirement: SimplifiedBrowserService.start_browser() 的实际启动逻辑
系统SHALL确保 start_browser() 方法执行实际的浏览器启动操作，而非仅设置状态标志。

#### Scenario: start_browser 执行实际启动
- **WHEN** 调用 start_browser() 方法
- **THEN** 系统应确保浏览器驱动已初始化
- **AND** 应验证 browser_driver 不为 None
- **AND** 应验证 page/browser/context 对象已创建
- **AND** 不应仅设置状态标志而不执行实际操作

#### Scenario: start_browser 的幂等性
- **WHEN** 多次调用 start_browser()
- **THEN** 第一次应执行实际启动
- **AND** 后续调用应检查已启动状态并直接返回
- **AND** 不应重复启动浏览器

### Requirement: 异步上下文中的同步方法调用安全性
系统SHALL确保在异步上下文中调用同步方法时的安全性，避免事件循环不一致问题。

#### Scenario: 异步函数中更新浏览器对象
- **WHEN** 在异步函数（如 wrapper_extractor）中调用 _update_browser_objects()
- **THEN** 系统应确保访问的对象在当前事件循环中有效
- **AND** 不应出现事件循环不匹配的错误
- **AND** 对象访问应该是线程安全的

#### Scenario: 事件循环时间获取的一致性
- **WHEN** 需要获取事件循环时间
- **THEN** 系统应使用 asyncio.get_running_loop() 而非 get_event_loop()
- **AND** 确保在正确的事件循环上下文中获取时间
- **AND** 避免跨事件循环的时间计算错误

#### Scenario: 跨线程访问浏览器对象
- **WHEN** 同步包装器在独立线程的事件循环中执行异步操作
- **THEN** 浏览器对象的访问应该通过正确的事件循环
- **AND** 不应直接在主线程访问异步创建的对象
- **AND** 使用 run_coroutine_threadsafe 确保线程安全

### Requirement: 状态管理一致性
系统SHALL使用一致的状态管理策略，避免类级别和实例级别状态混用。

#### Scenario: 实例级别状态管理
- **WHEN** 管理浏览器初始化和启动状态
- **THEN** 系统应只使用实例级别的状态变量
- **AND** 不应使用类级别的状态变量（除了单例相关）
- **AND** 确保多实例场景下状态独立

#### Scenario: 单例状态正确性
- **WHEN** 多个代码路径访问同一个单例实例
- **THEN** 状态应保持一致
- **AND** 不应出现状态不同步的情况

## MODIFIED Requirements

### Requirement: 浏览器服务关闭
系统SHALL支持安全的浏览器服务关闭，考虑单例模式下的多引用场景。

#### Scenario: 普通关闭（原有场景）
- **WHEN** 调用 close() 方法
- **THEN** 系统应检查引用计数
- **AND** 只有最后一个引用才真正关闭浏览器
- **AND** 返回操作结果

#### Scenario: 强制关闭（新增场景）
- **WHEN** 调用 close(force=True)
- **THEN** 系统应立即关闭浏览器
- **AND** 忽略引用计数
- **AND** 重置所有状态

#### Scenario: 上下文管理器退出
- **WHEN** 使用 with 语句且退出上下文
- **THEN** 系统应正确递减引用计数
- **AND** 确保资源被正确释放

### Requirement: 浏览器对象访问
系统SHALL提供直接访问浏览器对象的能力，并确保对象的有效性。

#### Scenario: 直接访问 page 对象（原有场景）
- **WHEN** 访问 browser_service.page
- **THEN** 应返回有效的 Playwright Page 对象
- **AND** 对象不应为 None（如果浏览器已启动）

#### Scenario: 对象未初始化时的访问（新增场景）
- **WHEN** 浏览器未启动时访问 page 对象
- **THEN** 应返回 None
- **AND** 不应抛出异常
- **AND** 用户应先调用 start_browser()

#### Scenario: 对象更新失败时的访问（新增场景）
- **WHEN** _update_browser_objects() 失败
- **THEN** 系统应抛出 BrowserError 异常
- **AND** 异常应包含详细的错误信息
- **AND** 用户应能根据异常信息排查问题
