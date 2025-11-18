## ADDED Requirements

### Requirement: 浏览器进程检测
系统SHALL提供浏览器进程检测功能，能够识别当前运行的 Edge 浏览器进程。

#### Scenario: 检测运行中的浏览器
- **WHEN** 调用浏览器检测功能
- **THEN** 系统应正确识别 Edge 浏览器是否正在运行
- **AND** 支持 macOS、Windows、Linux 三大平台

#### Scenario: 浏览器未运行时的提示
- **WHEN** 浏览器未运行时尝试连接
- **THEN** 系统应抛出明确的错误信息
- **AND** 提示用户启动浏览器的方法

### Requirement: Profile 自动检测
系统SHALL提供 Profile 自动检测功能，能够扫描所有 Profile 并识别有登录态的 Profile。

#### Scenario: 扫描所有 Profile
- **WHEN** 执行 Profile 扫描
- **THEN** 系统应列出所有存在的 Profile（Default, Profile 1, Profile 2...）
- **AND** 按最后修改时间排序

#### Scenario: 验证登录态app
- **WHEN** 检查 Profile 的登录态
- **THEN** 系统应读取 Cookies 数据库
- **AND** 验证是否存在指定域名（如 seerfar.cn）的有效 Cookie
- **AND** 返回验证结果

#### Scenario: 自动选择活跃 Profile
- **WHEN** 需要选择 Profile 进行连接
- **THEN** 系统应自动选择最近使用的有登录态的 Profile
- **AND** 如果没有找到有登录态的 Profile，应抛出错误

### Requirement: 仅连接模式
系统SHALL只支持连接到已运行的浏览器，不再支持启动新浏览器。

#### Scenario: 强制连接模式
- **WHEN** 初始化浏览器服务
- **THEN** 系统应要求 connect_to_existing 配置为 True
- **AND** 如果配置为 False，应抛出 RuntimeError

#### Scenario: 连接到现有浏览器
- **WHEN** 连接到已运行的浏览器
- **THEN** 系统应使用检测到的 Profile
- **AND** 通过 CDP 协议连接到浏览器
- **AND** 保留用户的登录态和会话信息

#### Scenario: 连接失败处理
- **WHEN** 连接浏览器失败
- **THEN** 系统应抛出 RuntimeError
- **AND** 提供详细的错误信息和解决方案
- **AND** 包括检查浏览器运行状态、调试端口、Profile 等步骤

### Requirement: CDP 调试端口验证
系统SHALL验证 CDP 调试端口的可用性，确保能够正常连接。

#### Scenario: 检查调试端口
- **WHEN** 准备连接浏览器
- **THEN** 系统应检查指定端口（默认 9222）是否开启
- **AND** 验证 CDP 端点是否可访问
- **AND** 如果端口未开启，提示用户启动带调试端口的浏览器

#### Scenario: 验证 CDP 端点
- **WHEN** 调试端口已开启
- **THEN** 系统应访问 /json/version 端点
- **AND** 验证返回的 webSocketDebuggerUrl 是否存在
- **AND** 确认 CDP 协议可用

### Requirement: 跨平台兼容性
系统SHALL支持 macOS、Windows、Linux 三大操作系统的浏览器检测和连接。

#### Scenario: macOS 平台支持
- **WHEN** 在 macOS 上运行
- **THEN** 系统应使用正确的用户数据目录路径
- **AND** 正确检测 Edge 浏览器进程
- **AND** 正确读取 Cookies 数据库

#### Scenario: Windows 平台支持
- **WHEN** 在 Windows 上运行
- **THEN** 系统应使用正确的用户数据目录路径
- **AND** 正确检测 Edge 浏览器进程
- **AND** 正确读取 Cookies 数据库

#### Scenario: Linux 平台支持
- **WHEN** 在 Linux 上运行
- **THEN** 系统应使用正确的用户数据目录路径
- **AND** 正确检测 Edge 浏览器进程
- **AND** 正确读取 Cookies 数据库

### Requirement: 配置化多域名登录态检查
系统SHALL支持通过配置文件指定需要检查登录态的域名列表，并验证所有配置的域名都已登录。

#### Scenario: 从配置文件读取域名列表
- **WHEN** 初始化浏览器服务
- **THEN** 系统应从 config.json 的 browser.required_login_domains 读取域名列表
- **AND** 支持配置多个域名（如 ["seerfar.cn", "www.maozierp.com"]）
- **AND** 如果配置为空数组或不存在，则跳过登录态检查

#### Scenario: AND 逻辑验证所有域名
- **WHEN** 配置了多个域名需要检查登录态
- **THEN** 系统应验证所有配置的域名都有登录态（AND 逻辑）
- **AND** 只要有一个域名未登录，就应该抛出 LoginRequiredError
- **AND** 错误信息中列出所有未登录的域名

#### Scenario: 输出所有 Profile 的详细登录报告
- **WHEN** 检测到有域名未登录
- **THEN** 系统应输出所有 Profile 的登录状态详细报告
- **AND** 报告包含每个 Profile 对每个域名的登录状态
- **AND** 报告包含 Cookie 数量和最后更新时间等详细信息

#### Scenario: 未登录时中断程序
- **WHEN** 检测到必需域名未登录
- **THEN** 系统应抛出 LoginRequiredError 异常
- **AND** 异常信息包含未登录的域名列表
- **AND** 异常信息包含登录指导（如何在浏览器中登录）
- **AND** 程序立即中断，不继续执行

#### Scenario: 跳过登录态检查
- **WHEN** config.json 中 required_login_domains 为空数组
- **THEN** 系统应跳过所有登录态检查
- **AND** 直接使用最近使用的 Profile 进行连接
- **AND** 不抛出 LoginRequiredError

### Requirement: 登录态详细分析
系统SHALL提供详细的登录态分析功能，帮助用户了解当前浏览器的登录情况。

#### Scenario: 分析所有 Profile 的登录状态
- **WHEN** 调用登录状态分析功能
- **THEN** 系统应扫描所有 Profile
- **AND** 对每个 Profile 检查所有配置域名的登录态
- **AND** 返回结构化的登录状态报告

#### Scenario: 登录状态报告内容
- **WHEN** 生成登录状态报告
- **THEN** 报告应包含 Profile 名称
- **AND** 报告应包含每个域名的登录状态（是/否）
- **AND** 报告应包含 Cookie 数量
- **AND** 报告应包含最后修改时间
- **AND** 报告应以易读的格式输出（表格或列表）

### Requirement: 错误提示和用户指导
系统SHALL在各种错误场景下提供清晰的错误信息和解决方案。

#### Scenario: 浏览器未运行
- **WHEN** 检测到浏览器未运行
- **THEN** 系统应提示"未检测到运行中的 Edge 浏览器"
- **AND** 提供启动浏览器的命令或脚本

#### Scenario: 无登录态 Profile
- **WHEN** 所有 Profile 都没有必需域名的登录态
- **THEN** 系统应提示"未找到有必需域名登录态的 Profile"
- **AND** 列出所有未登录的域名
- **AND** 提示用户在浏览器中登录这些域名

#### Scenario: 调试端口未开启
- **WHEN** 调试端口未开启
- **THEN** 系统应提示"调试端口未开启"
- **AND** 提供启动带调试端口浏览器的方法

#### Scenario: 部分域名未登录
- **WHEN** 配置了多个域名但只有部分已登录
- **THEN** 系统应抛出 LoginRequiredError
- **AND** 明确指出哪些域名已登录，哪些未登录
- **AND** 提供针对性的登录指导

## REMOVED Requirements

### Requirement: 浏览器自动启动
**Reason**: 自动启动浏览器会导致丢失用户登录态，且无法利用已有的浏览器会话。系统改为仅支持连接模式。

**Migration**: 用户需要：
1. 手动启动 Edge 浏览器并开启调试端口（使用提供的脚本或命令）
2. 在浏览器中登录 seerfar.cn
3. 系统会自动检测并连接到该浏览器
