# Change: 重构浏览器服务为仅连接模式并支持配置化多域名登录态检查

## Why
当前浏览器服务存在以下问题：
1. 启动新浏览器实例会导致丢失用户登录态，需要重新登录
2. 无法利用用户已经打开的浏览器中的 Cookie 和会话信息
3. 启动参数使用不存在的 Default Profile，导致登录态丢失
4. 缺乏对浏览器进程和 Profile 的智能检测机制
5. 登录态检查域名硬编码，无法灵活配置
6. 缺少对多个域名（如 seerfar.cn 和 www.maozierp.com）的统一登录态检查
7. 未登录时缺少明确的错误提示和程序中断机制
8. 配置文件结构不合理：`scraping` 和 `browser` 配置分散在不同位置，但它们本质上都是浏览器相关配置

这些问题导致用户体验差，需要频繁手动登录，影响自动化流程的效率。

## What Changes
- **BREAKING**: 移除所有启动新浏览器的代码路径，系统只支持连接到已运行的浏览器
- 新增 `BrowserDetector` 工具类，提供浏览器进程检测和 Profile 识别能力
- 新增基于 Cookies 数据库的登录态验证机制，支持多域名检查
- **配置文件重构**：
  - 将 browser 配置从用户数据文件（config.json）迁移到系统配置文件（test_system_config.json）
  - 将 scraping 配置合并到 browser 配置中，统一管理所有浏览器相关配置
  - 新的配置结构：`browser.required_login_domains`、`browser.browser_type`、`browser.headless`、`browser.timeout_seconds`、`browser.max_retries`、`browser.debug_port`
- **新增配置化登录态检查**：在系统配置中添加 `browser.required_login_domains` 配置
- **新增 AND 逻辑登录态验证**：所有配置的域名都必须有登录态
- **新增 LoginRequiredError 异常**：未登录时抛出明确异常并中断程序
- **新增登录状态详细报告**：检查所有 Profile 的登录情况并输出详细报告
- 修改 `xuanping_browser_service.py`，集成自动 Profile 检测和配置化登录态检查
- 修改 `browser_service.py`，强制要求连接模式
- 新增跨平台支持（macOS/Windows/Linux）
- 新增完整的单元测试和集成测试

## Impact
- **Affected specs**: `browser-service`
- **Affected code**: 
  - `rpa/browser/utils/browser_detector.py` (修改 - 新增多域名检查和详细报告)
  - `rpa/browser/utils/__init__.py` (修改 - 导出新异常类)
  - `rpa/browser/utils/exceptions.py` (新增 - LoginRequiredError)
  - `common/scrapers/xuanping_browser_service.py` (修改 - 集成配置化登录态检查)
  - `rpa/browser/browser_service.py` (修改)
  - `test_system_config.json` (修改 - 合并 scraping 和 browser 配置)
  - `tests/test_browser_detector.py` (修改 - 新增多域名测试)
  - `tests/test_login_validation.py` (新增 - 登录态验证测试)
  - `rpa/tests/test_browser_connection.py` (新增)
- **Breaking changes**: 
  - 用户必须先手动启动浏览器并开启调试端口
  - 不再支持自动启动浏览器
  - **配置文件结构变更**：
    - browser 配置从 config.json 迁移到 test_system_config.json
    - scraping 配置合并到 browser 配置中
    - 需要更新配置读取逻辑以适应新的配置结构
  - 需要在系统配置中配置 `browser.required_login_domains`
  - 如果配置了登录域名但未登录，程序将立即中断并抛出 `LoginRequiredError`
