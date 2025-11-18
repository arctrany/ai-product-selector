# 支持浏览器自动启动和智能 Profile 选择

## Why - 为什么需要这个变更？

### 问题背景
当前实现存在严重的逻辑错误：
- **错误行为**：检测到没有运行中的浏览器时，直接报错退出
- **用户体验差**：用户必须手动启动浏览器，否则程序无法运行
- **不符合预期**：系统应该能够自动启动浏览器，而不是要求用户手动操作

### 存在的问题
1. **强制手动启动**：要求用户必须先手动启动浏览器
2. **缺少自动化**：没有自动启动浏览器的能力
3. **Profile 选择不智能**：没有根据登录态自动选择最佳 Profile
4. **错误提示不友好**：只提示"未检测到浏览器"，没有提供自动解决方案

### 影响范围
- `common/scrapers/xuanping_browser_service.py` - 浏览器服务主逻辑
- `rpa/browser/utils/browser_detector.py` - 浏览器检测工具
- `rpa/browser/implementations/playwright_browser_driver.py` - Playwright 驱动实现

## What Changes - 需要做什么变更？

### 核心变更：智能浏览器启动策略

#### 1. 检测运行中的浏览器
- 检测是否有运行中的浏览器（支持 Chrome/Edge/Firefox 等）
- 验证 CDP 调试端口是否可用

#### 2. 如果有运行中的浏览器
- 连接到已运行的浏览器
- 保留用户的登录态和会话

#### 3. 如果没有运行中的浏览器（核心修正）
**步骤 A：智能 Profile 选择**
1. 扫描所有 Profile（Default, Profile 1, Profile 2...）
2. 检查每个 Profile 的登录态（验证 required_login_domains）
3. 选择策略：
   - 优先选择：满足所有登录态要求 + 最近使用的 Profile
   - 如果没有满足要求的：选择最近使用的 Profile（Default 或其他）

**步骤 B：自动启动浏览器**
1. 使用选中的 Profile 的用户数据目录
2. 配置启动参数：
   - 开启调试端口（debug_port，默认 9222）
   - 设置 headless 模式（从配置读取，默认 False）
   - 设置窗口大小（从配置读取或使用默认值）
   - 禁用扩展（可选）
3. 启动浏览器进程

**步骤 C：登录态提示**
- 如果选中的 Profile 不满足登录态要求：
  - 启动浏览器后输出警告日志
  - 提示用户需要登录的域名列表
  - 继续执行（不中断程序）

#### 4. 启动失败处理
- 记录详细的错误日志
- 提供明确的错误信息和解决方案
- 退出程序（不重试）

### 配置支持

从 `config.browser` 读取配置：
```json
{
  "browser": {
    "browser_type": "edge",
    "headless": false,
    "window_width": 1920,
    "window_height": 1080,
    "timeout_seconds": 30,
    "max_retries": 3,
    "required_login_domains": ["seerfar.cn", "www.maozierp.com"],
    "debug_port": 9222
  }
}
```

### 跨浏览器支持
- Chrome
- Edge
- Firefox
- 其他 Chromium 内核浏览器

## Breaking Changes - 破坏性变更

### 无破坏性变更
本次变更是**功能增强**，不引入破坏性变更：

1. ✅ **向后兼容**：仍然支持连接到已运行的浏览器
2. ✅ **新增功能**：增加自动启动浏览器的能力
3. ✅ **配置兼容**：使用现有的 browser 配置
4. ✅ **行为改进**：从"报错退出"改为"自动启动"

### 行为变更
- **旧行为**：没有运行中的浏览器 → 报错退出
- **新行为**：没有运行中的浏览器 → 自动启动浏览器

## Implementation Plan - 实施计划

### 阶段 1：BrowserDetector 增强
1. 添加 `select_best_profile()` 方法
   - 扫描所有 Profile
   - 检查登录态
   - 返回最佳 Profile（最近使用 + 满足登录态）

2. 添加 `get_browser_launch_command()` 方法
   - 生成浏览器启动命令
   - 支持跨平台（macOS/Windows/Linux）
   - 支持多种浏览器（Chrome/Edge/Firefox）

### 阶段 2：XuanpingBrowserService 重构
1. 修改 `_create_browser_config()` 方法
   - 检测是否有运行中的浏览器
   - 如果没有：调用 BrowserDetector 选择最佳 Profile
   - 配置为启动模式（connect_to_existing=False）

2. 添加启动后的登录态验证
   - 启动成功后检查登录态
   - 如果不满足：输出警告（不中断）

### 阶段 3：PlaywrightBrowserDriver 适配
1. 移除强制连接模式的限制
2. 支持启动新浏览器
3. 使用 BrowserDetector 提供的 Profile 信息

### 阶段 4：测试验证
1. 测试自动启动功能
2. 测试 Profile 选择逻辑
3. 测试登录态验证
4. 测试跨平台兼容性

## Success Criteria - 成功标准

1. ✅ 没有运行中的浏览器时，能自动启动
2. ✅ 自动选择最佳 Profile（最近使用 + 满足登录态）
3. ✅ 如果没有满足登录态的 Profile，启动默认 Profile 并提示
4. ✅ 支持 headless 模式（默认 False）
5. ✅ 支持多种浏览器（Chrome/Edge/Firefox）
6. ✅ 跨平台兼容（macOS/Windows/Linux）
7. ✅ 启动失败时报错并退出
8. ✅ 所有现有功能正常工作

## Risks and Mitigations - 风险和缓解措施

### 风险 1：浏览器启动失败
**影响**: 高  
**概率**: 中  
**缓解措施**:
- 详细的错误日志
- 明确的失败原因和解决方案
- 验证浏览器可执行文件路径

### 风险 2：Profile 冲突
**影响**: 中  
**概率**: 低  
**缓解措施**:
- 检查 Profile 是否被其他进程占用
- 提供清晰的错误提示
- 建议用户关闭其他浏览器实例

### 风险 3：跨平台兼容性问题
**影响**: 中  
**概率**: 中  
**缓解措施**:
- 充分的跨平台测试
- 平台特定的路径处理
- 浏览器可执行文件路径检测

## Timeline - 时间线

- **Day 1**: 完成 BrowserDetector 增强
- **Day 2**: 完成 XuanpingBrowserService 重构
- **Day 3**: 完成 PlaywrightBrowserDriver 适配
- **Day 4**: 测试和验证
- **Day 5**: 代码审查和合并

## Related Changes - 相关变更

- [refactor-browser-connect-only](../archive/2025-11-18-refactor-browser-connect-only/proposal.md) - 浏览器仅连接模式重构（需要修正）
- [unify-browser-config](./unify-browser-config/proposal.md) - 统一浏览器配置管理（已完成）
