# Browser Profile Detection - Spec Delta

## REMOVED Requirements

### Requirement: Cookie-based Login Detection
**移除原因**: Playwright 的 `launch_persistent_context` 无法读取现有 Profile 的 Cookies，导致检测逻辑失效且误判率高。

**原功能描述**:
- 系统通过读取浏览器 Cookies 数据库来检测 Profile 是否有特定域名的登录态
- 使用 `_has_login_cookies()` 方法检查 Cookies 文件
- 使用 `validate_required_logins()` 验证所有必需域名的登录态

**迁移方案**:
- 用户需要在启动程序前手动确保已在浏览器中登录所需网站
- 程序将使用最近使用的 Profile，不再进行登录态检测
- 如果未登录，程序会在实际访问网站时报错，错误提示会引导用户登录

### Requirement: Profile Selection Based on Login Status
**移除原因**: 基于登录态选择 Profile 的逻辑依赖于 Cookie 检测，现已移除。

**原功能描述**:
- `detect_active_profile(target_domain)` 会遍历所有 Profile
- 检查每个 Profile 是否有目标域名的登录态
- 返回第一个有登录态的 Profile

**迁移方案**:
- 简化为只返回最近使用的 Profile
- 移除 `target_domain` 参数
- 用户通过浏览器的 Profile 管理功能确保使用正确的 Profile

## MODIFIED Requirements

### Requirement: Profile Detection
系统应能检测并返回最近使用的浏览器 Profile。

**修改内容**:
- **之前**: 检测有特定域名登录态的 Profile
- **之后**: 只检测最近使用的 Profile（基于文件修改时间）

#### Scenario: 检测最近使用的 Profile
- **WHEN** 系统需要选择浏览器 Profile
- **THEN** 返回最近修改时间最新的 Profile
- **AND** 不检查登录态
- **AND** 记录日志说明选择的 Profile

#### Scenario: 没有可用的 Profile
- **WHEN** 用户数据目录中没有任何 Profile
- **THEN** 返回 None
- **AND** 记录警告日志

### Requirement: Error Handling
系统应在用户未登录时提供清晰的错误提示。

**修改内容**:
- **之前**: 在启动前检测登录态，未登录则报错
- **之后**: 在实际访问网站时检测，提供引导性错误提示

#### Scenario: 用户未登录所需网站
- **WHEN** 程序尝试访问需要登录的网站
- **AND** 用户未登录
- **THEN** 抛出明确的错误
- **AND** 错误消息包含需要登录的网站列表
- **AND** 错误消息提供登录步骤指引

## ADDED Requirements

### Requirement: Simplified Profile Selection
系统应提供简化的 Profile 选择机制，基于最近使用时间。

#### Scenario: 选择默认 Profile
- **WHEN** 系统启动浏览器
- **AND** 存在多个 Profile
- **THEN** 选择最近使用的 Profile
- **AND** 记录选择的 Profile 名称
- **AND** 不进行登录态验证

#### Scenario: 用户手动指定 Profile
- **WHEN** 用户通过配置指定 Profile 名称
- **THEN** 使用指定的 Profile
- **AND** 不检查该 Profile 是否存在或有登录态
- **AND** 如果 Profile 不存在，在启动时报错

### Requirement: User Guidance
系统应在文档和错误提示中明确说明用户需要预先登录。

#### Scenario: 启动提示
- **WHEN** 系统启动
- **THEN** 在日志中提示用户确保已登录所需网站
- **AND** 列出需要登录的网站域名

#### Scenario: 错误提示优化
- **WHEN** 因未登录导致操作失败
- **THEN** 错误消息包含具体的登录步骤
- **AND** 提供需要登录的网站 URL
- **AND** 说明如何在浏览器中登录
