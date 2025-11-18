# Implementation Tasks

## 1. 创建和增强 BrowserDetector 工具类
- [x] 1.1 创建 `rpa/browser/utils/browser_detector.py`
- [x] 1.2 实现浏览器进程检测功能（跨平台）
- [x] 1.3 实现 Profile 目录扫描功能
- [x] 1.4 实现 Cookies 数据库读取和登录态验证
- [x] 1.5 实现自动选择最近使用的有登录态的 Profile
- [x] 1.6 创建 `rpa/browser/utils/__init__.py` 导出接口
- [ ] 1.7 新增多域名登录态检查功能（AND 逻辑）
- [ ] 1.8 新增 `analyze_all_profiles_login_status()` 方法，输出所有 Profile 的详细登录报告
- [ ] 1.9 新增 `validate_required_logins()` 方法，验证所有必需域名的登录态

## 2. 创建异常类
- [ ] 2.1 创建 `rpa/browser/utils/exceptions.py`
- [ ] 2.2 实现 `LoginRequiredError` 异常类
- [ ] 2.3 异常信息包含未登录的域名列表和登录指导
- [ ] 2.4 在 `__init__.py` 中导出异常类

## 3. 配置文件更新
- [ ] 3.1 在 `config.json` 中添加 `browser` 配置区域
- [ ] 3.2 添加 `required_login_domains` 配置项（数组类型）
- [ ] 3.3 添加配置示例和注释说明
- [ ] 3.4 支持空数组表示跳过登录态检查

## 4. 重构 xuanping_browser_service.py
- [x] 4.1 集成 BrowserDetector 进行 Profile 检测
- [x] 4.2 添加浏览器运行状态验证
- [x] 4.3 添加 CDP 调试端口可用性检查
- [x] 4.4 移除所有启动新浏览器的代码
- [x] 4.5 强制使用连接模式
- [x] 4.6 添加详细的错误提示和解决方案
- [ ] 4.7 从 config.json 读取 `required_login_domains` 配置
- [ ] 4.8 调用 `validate_required_logins()` 验证登录态
- [ ] 4.9 捕获 `LoginRequiredError` 并输出详细报告后中断程序

## 5. 重构 browser_service.py
- [x] 5.1 移除启动新浏览器的代码路径
- [x] 5.2 强制要求 connect_to_existing 配置
- [x] 5.3 添加连接失败时的 RuntimeError
- [x] 5.4 提供用户友好的错误信息

## 6. 编写测试
- [x] 6.1 创建 `tests/test_browser_detector.py` 基础测试
- [x] 6.2 测试浏览器进程检测
- [x] 6.3 测试 Profile 扫描和排序
- [x] 6.4 测试登录态验证
- [x] 6.5 测试活跃 Profile 自动检测
- [x] 6.6 测试浏览器连接逻辑验证
- [ ] 6.7 新增多域名登录态检查测试
- [ ] 6.8 新增 AND 逻辑验证测试
- [ ] 6.9 新增 `LoginRequiredError` 异常测试
- [ ] 6.10 新增详细登录报告测试
- [ ] 6.11 创建 `tests/test_login_validation.py` 专项测试
- [ ] 6.12 创建 `rpa/tests/test_browser_connection.py` 集成测试
- [ ] 6.13 测试真实场景下的浏览器连接
- [ ] 6.14 测试错误场景和异常处理
- [ ] 6.15 测试跨平台兼容性

## 7. 文档和辅助工具
- [x] 7.1 创建 `start_edge_with_debug.sh` 启动脚本
- [ ] 7.2 更新项目文档说明新的使用方式
- [ ] 7.3 添加 config.json 配置说明
- [ ] 7.4 添加登录态检查的故障排查指南
- [ ] 7.5 添加多域名登录的最佳实践文档

## 8. 质量保证
- [ ] 8.1 运行所有单元测试确保通过
- [ ] 8.2 运行集成测试验证真实场景
- [ ] 8.3 测试配置为空数组时跳过检查的场景
- [ ] 8.4 测试单域名和多域名配置的场景
- [ ] 8.5 测试 LoginRequiredError 的抛出和捕获
- [ ] 8.6 在 macOS/Windows/Linux 上验证跨平台兼容性
- [ ] 8.7 检查并修复所有 Lint 错误
- [ ] 8.8 代码审查和优化
