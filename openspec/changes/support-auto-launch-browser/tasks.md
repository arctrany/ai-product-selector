# Implementation Tasks

## 1. SimplifiedBrowserService 修改
- [x] 1.1 移除 `initialize()` 方法中的强制连接检查代码
- [x] 1.2 添加启动浏览器的逻辑分支（连接 vs 启动）
- [x] 1.3 完善错误处理和日志输出
- [x] 1.4 确保 `_launch_browser()` 被正确调用

## 2. XuanpingBrowserService 修改
- [x] 2.1 修改 `_create_browser_config()` 方法支持自动启动模式
- [x] 2.2 移除所有"请手动启动浏览器"的错误提示
- [x] 2.3 添加 headless 模式配置支持
- [x] 2.4 添加启动模式配置（connect_to_existing=False）
- [x] 2.5 优化日志输出（区分启动模式和连接模式）

## 3. 功能测试
- [x] 3.1 启动模式：浏览器未运行 → 自动启动成功
- [x] 3.2 启动模式：使用正确的 Profile（有登录态）
- [x] 3.3 启动模式：扩展正确加载
- [x] 3.4 启动模式：登录态保留验证
- [x] 3.5 连接模式：浏览器已运行 → 自动连接成功
- [x] 3.6 连接模式：扩展可用
- [x] 3.7 连接模式：登录态保留

## 4. Profile 锁定测试
- [x] 4.1 Default Profile 被占用 → 提示用户关闭浏览器
- [x] 4.2 用户关闭浏览器后 → 成功启动
- [x] 4.3 启动后验证 CDP 调试端口可用

## 5. 跨平台和浏览器测试
- [x] 5.1 macOS + Edge 启动模式
- [x] 5.2 macOS + Edge 连接模式
- [x] 5.3 macOS + Chrome 启动模式
- [x] 5.4 macOS + Chrome 连接模式

## 6. 边界情况测试
- [x] 6.1 浏览器启动失败（权限问题）
- [x] 6.2 调试端口被占用（9222）
- [x] 6.3 Profile 被占用（提示用户关闭）
- [x] 6.4 CDP 调试端口连接测试

## 7. 文档和清理
- [x] 7.1 更新注释
- [x] 7.2 清理无用代码
- [x] 7.3 Git 提交代码
- [x] 7.4 更新 proposal.md（补充浏览器支持说明）
- [x] 7.5 修正 Profile 锁定解决方案
- [x] 7.6 添加 CDP 调试端口支持说明
- [x] 7.7 修复 spec.md 符合 OpenSpec 规范
