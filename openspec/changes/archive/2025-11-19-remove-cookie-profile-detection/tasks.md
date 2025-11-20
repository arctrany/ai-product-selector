# 实施任务清单

## 1. 移除 Cookie 检测逻辑
- [x] 1.1 删除 `BrowserDetector._has_login_cookies()` 方法
- [x] 1.2 删除 `BrowserDetector._get_cookies_db_path()` 方法
- [x] 1.3 简化 `BrowserDetector.detect_active_profile()` 方法，移除登录态检测
- [x] 1.4 更新 `BrowserDetector.validate_required_logins()` 方法，移除 Cookie 检测

## 2. 简化 Profile 选择逻辑
- [x] 2.1 修改 `detect_active_profile()` 函数，只返回最近使用的 Profile
- [x] 2.2 移除 `target_domain` 参数（不再需要）
- [x] 2.3 更新函数文档字符串

## 3. 更新 XuanpingBrowserService
- [x] 3.1 移除 `_create_browser_config()` 中的登录态验证逻辑
- [x] 3.2 移除 `validate_required_logins()` 调用
- [x] 3.3 简化错误提示，引导用户手动登录
- [x] 3.4 更新日志输出

## 4. 更新导出和引用
- [x] 4.1 更新 `rpa/browser/utils/__init__.py` 中的导出
- [x] 4.2 检查并更新所有调用 `detect_active_profile()` 的地方
- [x] 4.3 移除 `LoginRequiredError` 异常（如果不再使用）

## 5. 测试和验证
- [x] 5.1 运行现有测试，确保无回归
- [x] 5.2 手动测试浏览器启动流程
- [x] 5.3 验证错误提示是否清晰
- [x] 5.4 检查 lint 错误

## 6. 文档更新
- [x] 6.1 更新 README（如有）
- [x] 6.2 更新用户文档，说明需要预先登录
- [x] 6.3 更新错误提示文案
