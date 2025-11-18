# 支持浏览器自动启动和智能 Profile 选择 - 任务列表

## 阶段 1：Profile 选择和浏览器检测增强 (P0)

### Task 1.1: 创建 ProfileSelector 工具类 (P0-1)
**优先级**: P0  
**预计时间**: 2 小时  
**依赖**: 无

**描述**:
创建 `rpa/browser/utils/profile_selector.py`，实现智能 Profile 选择逻辑。

**功能要点**:
1. `scan_profiles(user_data_dir)` - 扫描所有 Profile
2. `check_login_status(profile_path, required_domains)` - 检查登录态
3. `get_last_used_profile(user_data_dir)` - 获取最近使用的 Profile
4. `select_best_profile(user_data_dir, required_domains)` - 选择最佳 Profile
   - 优先：满足登录态 + 最近使用
   - 其次：最近使用的 Profile

**验收标准**:
- ✅ 能扫描所有 Profile（Default, Profile 1, Profile 2...）
- ✅ 能检查 Cookie 文件判断登录态
- ✅ 能读取 Local State 获取最近使用的 Profile
- ✅ 选择逻辑正确（最近使用 + 登录态优先）

---

### Task 1.2: 增强 BrowserDetector 支持启动命令生成 (P0-2)
**优先级**: P0  
**预计时间**: 2 小时  
**依赖**: Task 1.1

**描述**:
在 `rpa/browser/utils/browser_detector.py` 中添加浏览器启动命令生成功能。

**功能要点**:
1. `get_browser_executable_path(browser_type, platform)` - 获取浏览器可执行文件路径
   - macOS: `/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge`
   - Windows: `C:\Program Files\Microsoft\Edge\Application\msedge.exe`
   - Linux: `/usr/bin/microsoft-edge`
2. `generate_launch_args(profile_name, debug_port, headless, window_size)` - 生成启动参数
3. `build_launch_command(browser_type, user_data_dir, profile_name, config)` - 构建完整启动命令

**验收标准**:
- ✅ 支持 Chrome/Edge/Firefox
- ✅ 支持 macOS/Windows/Linux
- ✅ 生成的命令包含所有必要参数
- ✅ 支持 headless 模式

---

## 阶段 2：XuanpingBrowserService 重构 (P0)

### Task 2.1: 修改浏览器配置创建逻辑 (P0-3)
**优先级**: P0  
**预计时间**: 3 小时  
**依赖**: Task 1.1, Task 1.2

**描述**:
重构 `common/scrapers/xuanping_browser_service.py` 中的 `_create_browser_config()` 方法。

**修改要点**:
1. 检测是否有运行中的浏览器（调用 `_check_existing_browser()`）
2. **如果有运行中的浏览器**：
   - 配置为连接模式（`connect_to_existing=True`）
   - 使用检测到的 debug_port
3. **如果没有运行中的浏览器**：
   - 调用 `ProfileSelector.select_best_profile()` 选择最佳 Profile
   - 配置为启动模式（`connect_to_existing=False`）
   - 设置 `launch_browser=True`
   - 传递 Profile 信息和启动参数

**验收标准**:
- ✅ 能正确检测运行中的浏览器
- ✅ 有浏览器时连接，没有时启动
- ✅ Profile 选择逻辑正确
- ✅ 配置参数完整

---

### Task 2.2: 添加启动后登录态验证 (P1-4)
**优先级**: P1  
**预计时间**: 1 小时  
**依赖**: Task 2.1

**描述**:
在浏览器启动成功后，验证登录态并输出提示。

**功能要点**:
1. 启动成功后调用 `ProfileSelector.check_login_status()`
2. 如果不满足登录态要求：
   - 输出警告日志
   - 列出需要登录的域名
   - 不中断程序执行

**验收标准**:
- ✅ 能检测登录态
- ✅ 警告信息清晰友好
- ✅ 不影响程序继续执行

---

## 阶段 3：PlaywrightBrowserDriver 适配 (P0)

### Task 3.1: 移除强制连接模式限制 (P0-5)
**优先级**: P0  
**预计时间**: 1 小时  
**依赖**: Task 2.1

**描述**:
修改 `rpa/browser/implementations/playwright_browser_driver.py` 中的 `initialize()` 方法。

**修改要点**:
1. 移除以下代码：
```python
if not connect_to_existing:
    error_msg = (
        "❌ 配置错误：未启用连接模式\n"
        "💡 当前版本只支持连接到已运行的浏览器，不支持启动新浏览器\n"
        "   请确保浏览器已手动启动并开启调试端口"
    )
    self.logger.error(error_msg)
    raise RuntimeError(error_msg)
```
2. 添加启动浏览器的逻辑分支

**验收标准**:
- ✅ 移除强制连接模式检查
- ✅ 支持启动新浏览器

---

### Task 3.2: 实现浏览器启动逻辑 (P0-6)
**优先级**: P0  
**预计时间**: 3 小时  
**依赖**: Task 3.1, Task 1.2

**描述**:
在 `PlaywrightBrowserDriver` 中实现浏览器启动功能。

**功能要点**:
1. 读取配置中的 `launch_browser` 标志
2. 如果 `launch_browser=True`：
   - 使用 `BrowserDetector.build_launch_command()` 生成启动命令
   - 使用 `subprocess.Popen()` 启动浏览器进程
   - 等待浏览器启动完成（检查 CDP 端口）
   - 连接到启动的浏览器
3. 如果 `launch_browser=False`：
   - 直接连接到已运行的浏览器（原有逻辑）

**验收标准**:
- ✅ 能成功启动浏览器
- ✅ 能连接到启动的浏览器
- ✅ 启动失败时报错退出
- ✅ 支持 headless 模式

---

### Task 3.3: 添加浏览器进程管理 (P1-7)
**优先级**: P1  
**预计时间**: 2 小时  
**依赖**: Task 3.2

**描述**:
管理启动的浏览器进程生命周期。

**功能要点**:
1. 记录启动的浏览器进程 PID
2. 在 `close()` 方法中：
   - 如果是自己启动的浏览器，关闭进程
   - 如果是连接的浏览器，只断开连接
3. 异常处理：确保进程不会泄漏

**验收标准**:
- ✅ 能正确管理浏览器进程
- ✅ 关闭时清理进程
- ✅ 无进程泄漏

---

## 阶段 4：错误处理和日志优化 (P1)

### Task 4.1: 优化错误提示信息 (P1-8)
**优先级**: P1  
**预计时间**: 1 小时  
**依赖**: Task 3.2

**描述**:
优化各种错误场景的提示信息。

**场景覆盖**:
1. 浏览器可执行文件不存在
2. Profile 被占用
3. 启动超时
4. CDP 连接失败
5. 权限不足

**验收标准**:
- ✅ 错误信息清晰明确
- ✅ 提供解决方案
- ✅ 包含必要的调试信息

---

### Task 4.2: 完善日志输出 (P1-9)
**优先级**: P1  
**预计时间**: 1 小时  
**依赖**: Task 4.1

**描述**:
添加详细的日志输出，便于调试。

**日志要点**:
1. 浏览器检测结果
2. Profile 选择过程
3. 启动命令详情
4. 启动进度（等待 CDP 可用）
5. 登录态检查结果

**验收标准**:
- ✅ 日志信息完整
- ✅ 日志级别合理
- ✅ 便于问题排查

---

## 阶段 5：测试和验证 (P0)

### Task 5.1: 功能测试 (P0-10)
**优先级**: P0  
**预计时间**: 2 小时  
**依赖**: Task 3.2, Task 4.1

**测试场景**:
1. ✅ 没有运行中的浏览器 → 自动启动
2. ✅ 有运行中的浏览器 → 连接
3. ✅ 多个 Profile，选择最佳
4. ✅ 无满足登录态的 Profile → 启动默认 + 警告
5. ✅ headless 模式
6. ✅ 启动失败 → 报错退出

**验收标准**:
- ✅ 所有场景测试通过
- ✅ 无回归问题

---

### Task 5.2: 跨平台测试 (P1-11)
**优先级**: P1  
**预计时间**: 2 小时  
**依赖**: Task 5.1

**测试平台**:
- macOS
- Windows
- Linux

**验收标准**:
- ✅ 所有平台功能正常
- ✅ 路径处理正确
- ✅ 浏览器检测准确

---

## 阶段 6：文档和清理 (P2)

### Task 6.1: 更新文档 (P2-12)
**优先级**: P2  
**预计时间**: 1 小时  
**依赖**: Task 5.2

**文档内容**:
1. 更新 README（如果有）
2. 添加配置说明
3. 添加故障排查指南

**验收标准**:
- ✅ 文档完整准确
- ✅ 示例清晰

---

### Task 6.2: 代码清理和提交 (P2-13)
**优先级**: P2  
**预计时间**: 1 小时  
**依赖**: Task 6.1

**清理内容**:
1. 移除调试代码
2. 移除无用注释
3. 统一代码风格
4. 运行 lint 检查

**验收标准**:
- ✅ 无 lint 错误
- ✅ 代码整洁
- ✅ Git 提交成功

---

## 总结

**总任务数**: 13 个  
**P0 任务**: 6 个（关键路径）  
**P1 任务**: 5 个（重要但非阻塞）  
**P2 任务**: 2 个（优化和文档）

**预计总时间**: 24 小时（3 个工作日）

**关键路径**:
Task 1.1 → Task 1.2 → Task 2.1 → Task 3.1 → Task 3.2 → Task 5.1
