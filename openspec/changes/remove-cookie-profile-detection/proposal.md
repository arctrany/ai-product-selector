# Change: 移除基于 Cookie 的 Profile 检测逻辑

## Why

当前系统使用 Cookie 检测来判断浏览器 Profile 是否有登录态，但这种方式存在以下问题：

1. **Playwright 的 `launch_persistent_context` 无法读取现有 Profile 的 Cookies**
   - 即使传入完整的 Profile 路径，启动的浏览器实例是隔离的
   - 无法访问原有 Profile 的 Cookies 和登录态
   - 导致登录态验证失败，程序无法正常运行

2. **误判率高**
   - Cookie 文件可能被浏览器锁定或加密
   - 检测逻辑复杂且不可靠
   - 用户体验差（即使已登录也可能被判定为未登录）

3. **不符合实际使用场景**
   - 用户通常会在启动程序前确保已登录
   - 强制检测反而增加了使用门槛

## What Changes

- **移除** `BrowserDetector._has_login_cookies()` 方法
- **移除** `BrowserDetector.detect_active_profile()` 中的登录态检测逻辑
- **简化** Profile 选择机制：只选择最近使用的 Profile
- **移除** `XuanpingBrowserService` 中的登录态验证逻辑
- **更新** 文档和错误提示，引导用户在启动前手动登录

## Impact

### 受影响的模块
- `rpa/browser/utils/browser_detector.py` - Profile 检测逻辑
- `common/scrapers/xuanping_browser_service.py` - 浏览器服务配置
- `rpa/browser/utils/__init__.py` - 导出的工具函数

### 受影响的代码
- 删除约 100 行 Cookie 检测相关代码
- 简化 Profile 选择逻辑
- 更新错误提示和日志

### 用户体验变化
- **之前**：程序自动检测登录态，检测失败则报错
- **之后**：程序使用最近使用的 Profile，用户需确保启动前已登录
- **优势**：更简单、更可靠、更符合实际使用场景

### 风险
- **低风险**：用户可能忘记登录，但错误提示会明确告知
- **缓解措施**：在文档和启动提示中明确说明需要预先登录
