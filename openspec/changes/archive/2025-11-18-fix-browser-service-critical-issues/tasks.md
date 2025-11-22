# 实施任务清单

**重要**：严格按照阶段顺序执行，每个阶段完成后运行测试验证，不可跳过或并行执行跨阶段任务！

## 阶段 0：准备工作（已完成）
- [x] 0.1 完整审查 `XuanpingBrowserService` 代码
- [x] 0.2 识别所有潜在隐患和设计缺陷（11个问题）
- [x] 0.3 评估每个问题的严重程度和影响范围
- [x] 0.4 制定修复优先级（P0: 7个, P1: 4个）
- [x] 0.5 分析架构分层和依赖关系
- [x] 0.6 创建 OpenSpec 提案并验证通过

## 阶段 1：底层驱动修复（Layer 0: PlaywrightBrowserDriver）✅
**依赖**：无  
**目标**：修复最底层的浏览器驱动问题

- [x] 1.1 **P0-0**: 实现浏览器复用逻辑（Driver 部分）
  - [x] 在 `PlaywrightBrowserDriver` 中添加 `connect_to_existing_browser()` 方法
  - [x] 实现 Playwright 的 `connect_over_cdp` 连接逻辑
  - [x] 添加连接失败的降级处理
  - [x] 添加详细的日志记录（连接成功/失败）
  - [ ] 单元测试：模拟连接成功/失败场景
  - **文件**: `rpa/browser/implementations/playwright_browser_driver.py`
  - **风险**: 低（新增方法，不影响现有逻辑）

## 阶段 2：浏览器服务层修复（Layer 1: SimplifiedBrowserService）✅
**依赖**：阶段 1 完成  
**目标**：修复 SimplifiedBrowserService 的核心问题

- [x] 2.1 **P0-5**: 完善驱动初始化失败处理
  - [x] 在 `initialize()` 失败时将 `browser_driver` 设为 `None`
  - [x] 记录详细的失败原因
  - [ ] 单元测试：初始化失败场景
  - **文件**: `rpa/browser/browser_service.py`
  - **风险**: 低（防御性修复）

- [x] 2.2 **P0-4**: 添加 browser_driver 空值检查
  - [x] 在 `navigate_to()` 等方法中添加空值检查
  - [x] 空值时抛出 `BrowserError` 异常，消息明确
  - [ ] 单元测试：驱动为 None 时的访问
  - **文件**: `rpa/browser/browser_service.py`
  - **依赖**: Task 2.1
  - **风险**: 低（防御性检查）

- [x] 2.3 **P0-3**: 修复 start_browser 空操作问题
  - [x] 验证 `browser_driver` 不为 None
  - [x] 验证 `browser_driver.is_initialized()` 为 True
  - [x] 验证 `page` 对象已创建
  - [ ] 单元测试：启动验证场景
  - **文件**: `rpa/browser/browser_service.py`
  - **依赖**: Task 2.1, 2.2
  - **风险**: 中（改变方法行为，但更安全）

- [x] 2.4 **P0-0**: 实现浏览器复用配置读取（Service 部分）
  - [x] 在 `initialize()` 中读取 `connect_to_existing` 配置
  - [x] 检测到现有浏览器时调用 Driver 的连接方法
  - [x] 连接失败时降级到启动新实例
  - [ ] 集成测试：连接现有浏览器场景
  - **文件**: `rpa/browser/browser_service.py`
  - **依赖**: Task 1.1, 2.1, 2.2, 2.3
  - **风险**: 中（改变初始化流程）

## 阶段 3：异步服务层修复（Layer 2: XuanpingBrowserService）✅
**依赖**：阶段 2 完成  
**目标**：修复 XuanpingBrowserService 的单例和状态问题

- [x] 3.1 **P0-2**: 添加引用计数机制
  - [x] 在 `__init__()` 中增加引用计数
  - [x] 在 `close()` 中实现引用计数逻辑
  - [x] 添加 `force` 参数支持强制关闭
  - [x] 使用线程锁保证原子性
  - [ ] 单元测试：引用计数场景
  - **文件**: `common/scrapers/xuanping_browser_service.py`
  - **依赖**: 阶段 2 全部完成
  - **风险**: 中（改变资源管理逻辑）

- [x] 3.2 **P1-9**: 修复事件循环使用不一致
  - [x] 在 `scrape_page_data()` 中使用 `get_running_loop()` 替代 `get_event_loop()`
  - [x] 确保时间计算在正确的事件循环中
  - [ ] 单元测试：时间计算准确性
  - **文件**: `common/scrapers/xuanping_browser_service.py`
  - **依赖**: Task 3.1
  - **风险**: 低（简单替换）

- [x] 3.3 **P1-7**: 修复状态管理混乱
  - [x] 移除类级别的 `_initialized` 状态（如果存在）
  - [x] 统一使用实例级别状态管理
  - [ ] 单元测试：多实例状态独立性
  - **文件**: `common/scrapers/xuanping_browser_service.py`
  - **依赖**: Task 3.1, 3.2
  - **风险**: 低（清理冗余状态）

## 阶段 4：同步包装层修复（Layer 3: XuanpingBrowserServiceSync）✅
**依赖**：阶段 3 完成  
**目标**：修复 XuanpingBrowserServiceSync 的对象同步问题

- [x] 4.1 **P0-6**: 简化 _update_browser_objects 访问路径
  - [x] 添加逐层验证（async_service → browser_service → browser_driver）
  - [x] 每层为 None 时抛出明确的异常，指出具体哪一层
  - [ ] 单元测试：各层为 None 的场景
  - **文件**: `common/scrapers/xuanping_browser_service.py`
  - **依赖**: 阶段 3 全部完成
  - **风险**: 低（增强错误处理）

- [x] 4.2 **P0-1**: 增强 _update_browser_objects 错误处理
  - [x] 失败时抛出 `BrowserError` 异常（而非静默忽略）
  - [x] 使用异常链（from e）保留堆栈信息
  - [ ] 单元测试：异常抛出场景
  - **文件**: `common/scrapers/xuanping_browser_service.py`
  - **依赖**: Task 4.1
  - **风险**: 低（已包含在 Task 4.1 中）

- [x] 4.3 **P1-8**: 完善状态同步
  - [x] 在 `navigate_to()` 成功后自动调用 `_update_browser_objects()`
  - [x] 在 `initialize()` 成功后自动更新
  - [ ] 单元测试：自动同步场景
  - **文件**: `common/scrapers/xuanping_browser_service.py`
  - **依赖**: Task 4.1, 4.2
  - **风险**: 低（自动化同步）

- [x] 4.4 **P1-10**: 增强异步/同步边界安全性
  - [x] 在 `scrape_page_data` 的 wrapper 中增强异常处理
  - [x] 确保 `_update_browser_objects()` 失败时有明确提示
  - [ ] 单元测试：线程安全场景
  - **文件**: `common/scrapers/xuanping_browser_service.py`
  - **依赖**: Task 4.3
  - **风险**: 低（增强异常处理）

## 阶段 5：测试和验证
**依赖**：阶段 1-4 全部完成  
**目标**：确保所有修复正确且无回归

- [ ] 5.1 扩展单元测试
  - [ ] 测试 P0-0：浏览器复用逻辑（连接成功/失败/降级）
  - [ ] 测试 P0-1：`_update_browser_objects()` 异常抛出场景
  - [ ] 测试 P0-2：引用计数机制（创建/关闭/强制关闭）
  - [ ] 测试 P0-3：`start_browser()` 验证逻辑
  - [ ] 测试 P0-4：`browser_driver` 空值检查
  - [ ] 测试 P0-5：驱动初始化失败处理
  - [ ] 测试 P0-6：访问路径逐层验证
  - [ ] 测试 P1-7：状态管理独立性
  - [ ] 测试 P1-8：自动状态同步
  - [ ] 测试 P1-9：事件循环时间计算
  - [ ] 测试 P1-10：异步/同步边界安全性
  - **文件**: `tests/test_xuanping_browser_service_sync.py`
  - **覆盖率目标**: >90%

- [ ] 5.2 创建集成测试
  - [ ] 测试真实浏览器启动和关闭
  - [ ] 测试连接现有浏览器（端到端）
  - [ ] 测试多 Scraper 共享浏览器
  - [ ] 测试完整的数据抓取流程
  - [ ] 测试错误恢复和重试
  - **文件**: `tests/test_xuanping_browser_service_integration.py`（新建）
  - **环境要求**: 需要真实浏览器环境

- [ ] 5.3 运行所有测试
  - [ ] 运行单元测试：`pytest tests/test_xuanping_browser_service_sync.py -v`
  - [ ] 运行集成测试：`pytest tests/test_xuanping_browser_service_integration.py -v`
  - [ ] 运行全部测试：`pytest tests/ -v`
  - [ ] 检查测试覆盖率：`pytest --cov=common/scrapers --cov=rpa/browser`
  - **通过标准**: 所有测试通过，无回归

- [ ] 5.4 Lint 检查
  - [ ] 检查 `common/scrapers/xuanping_browser_service.py`
  - [ ] 检查 `rpa/browser/browser_service.py`
  - [ ] 检查 `rpa/browser/implementations/playwright_browser_driver.py`
  - [ ] 修复所有 lint 错误和警告
  - **命令**: `flake8 <file_path>`
  - **通过标准**: 无 lint 错误

## 阶段 6：文档和归档
**依赖**：阶段 5 全部完成  
**目标**：更新文档并归档提案

- [ ] 6.1 更新代码注释
  - [ ] 更新所有修改方法的 docstring
  - [ ] 添加关键修复的注释说明
  - [ ] 更新类的文档字符串
  - **文件**: 所有修改的 Python 文件

- [ ] 6.2 验证 OpenSpec 提案
  - [ ] 运行 `openspec validate fix-browser-service-critical-issues --strict`
  - [ ] 确保提案通过验证
  - **通过标准**: 验证成功

- [ ] 6.3 归档提案
  - [ ] 运行 `openspec archive fix-browser-service-critical-issues`
  - [ ] 确认归档成功
  - **结果**: 提案移动到 archived 目录

## 阶段 7：部署和监控（可选）
**依赖**：阶段 6 全部完成  
**目标**：在生产环境验证修复效果

- [ ] 7.1 测试环境验证
  - [ ] 部署到测试环境
  - [ ] 运行完整的功能测试
  - [ ] 监控错误日志
  - [ ] 确认无异常

- [ ] 7.2 生产环境部署
  - [ ] 部署到生产环境
  - [ ] 监控运行情况（24小时）
  - [ ] 收集性能指标
  - [ ] 确认稳定性

- [ ] 7.3 持续优化
  - [ ] 收集用户反馈
  - [ ] 分析性能瓶颈
  - [ ] 规划后续优化
