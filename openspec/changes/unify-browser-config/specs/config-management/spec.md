## MODIFIED Requirements

### Requirement: 配置类定义和管理
系统SHALL提供统一的浏览器配置管理，支持向后兼容的配置加载。

#### Scenario: 使用新的 BrowserConfig 配置
- **WHEN** 配置文件包含 `browser` 字段
- **THEN** 系统应正确加载 BrowserConfig 配置
- **AND** 配置包含所有浏览器相关字段（browser_type, headless, timeout_seconds, required_login_domains, debug_port）
- **AND** 配置验证通过

#### Scenario: 向后兼容旧的 scraping 配置
- **WHEN** 配置文件包含 `scraping` 字段
- **THEN** 系统应正确加载配置（向后兼容）
- **AND** 输出警告日志："⚠️ 警告：'scraping' 配置字段已废弃，请迁移到 'browser' 字段"
- **AND** 配置功能正常工作

#### Scenario: 配置字段优先级
- **WHEN** 配置文件同时包含 `browser` 和 `scraping` 字段
- **THEN** 系统应优先使用 `browser` 字段
- **AND** 忽略 `scraping` 字段
- **AND** 输出信息日志说明使用了 browser 配置

#### Scenario: ScrapingConfig 别名支持
- **WHEN** 代码中使用 ScrapingConfig 类
- **THEN** 系统应正常工作（ScrapingConfig 是 BrowserConfig 的别名）
- **AND** 功能与使用 BrowserConfig 完全相同
- **AND** 类文档字符串标注废弃信息

#### Scenario: 配置序列化
- **WHEN** 调用配置的 to_dict() 方法
- **THEN** 系统应输出包含 `browser` 字段的字典
- **AND** 不输出 `scraping` 字段
- **AND** 所有配置值正确序列化

#### Scenario: 配置验证
- **WHEN** 加载配置后进行验证
- **THEN** 系统应验证所有必需字段存在
- **AND** 验证字段值在合理范围内
- **AND** 验证失败时抛出明确的错误信息

### Requirement: 配置文件格式支持
系统SHALL支持新旧两种配置文件格式，确保平滑迁移。

#### Scenario: 新格式配置文件
- **WHEN** 使用新格式配置文件（包含 browser 字段）
- **THEN** 系统应正确解析所有配置项
- **AND** 支持新增的配置字段（如 required_login_domains）
- **AND** 无警告日志输出

#### Scenario: 旧格式配置文件
- **WHEN** 使用旧格式配置文件（包含 scraping 字段）
- **THEN** 系统应正确解析所有配置项
- **AND** 映射到对应的 BrowserConfig 字段
- **AND** 输出废弃警告日志

#### Scenario: 配置文件缺失
- **WHEN** 配置文件不存在或格式错误
- **THEN** 系统应使用默认配置
- **AND** 输出警告日志说明使用默认配置
- **AND** 系统继续正常运行

### Requirement: 废弃标记和迁移提示
系统SHALL为废弃的配置提供清晰的标记和迁移指导。

#### Scenario: ScrapingConfig 废弃标记
- **WHEN** 查看 ScrapingConfig 类定义
- **THEN** 类文档字符串应包含废弃信息
- **AND** 说明应使用 BrowserConfig 替代
- **AND** 提供迁移示例代码

#### Scenario: 配置加载警告日志
- **WHEN** 使用 scraping 字段加载配置
- **THEN** 系统应输出清晰的警告日志
- **AND** 日志包含具体的迁移建议
- **AND** 日志包含新旧配置的对比示例

#### Scenario: 代码注释迁移提示
- **WHEN** 查看配置相关代码
- **THEN** 注释应标注废弃信息
- **AND** 提供迁移到新配置的方法
- **AND** 说明向后兼容的保证期限

## ADDED Requirements

### Requirement: BrowserConfig 统一配置类
系统SHALL提供统一的 BrowserConfig 配置类，整合所有浏览器相关配置。

#### Scenario: BrowserConfig 类定义
- **WHEN** 创建 BrowserConfig 实例
- **THEN** 类应包含所有浏览器配置字段
- **AND** 所有字段都有类型注解
- **AND** 所有字段都有合理的默认值
- **AND** 支持配置验证方法

#### Scenario: 配置字段完整性
- **WHEN** 查看 BrowserConfig 字段
- **THEN** 应包含基础配置（browser_type, headless, window_width, window_height）
- **AND** 应包含超时配置（timeout_seconds, max_retries）
- **AND** 应包含登录配置（required_login_domains）
- **AND** 应包含调试配置（debug_port）

#### Scenario: 配置方法支持
- **WHEN** 使用 BrowserConfig 配置方法
- **THEN** 支持 from_dict() 从字典创建
- **AND** 支持 to_dict() 转换为字典
- **AND** 支持 validate() 验证配置
- **AND** 支持 from_json_file() 从文件加载

### Requirement: 配置加载优先级
系统SHALL实现清晰的配置加载优先级逻辑。

#### Scenario: 配置字段优先级规则
- **WHEN** 配置文件包含多个配置源
- **THEN** 优先级应为：browser > scraping > 默认值
- **AND** 高优先级配置覆盖低优先级配置
- **AND** 日志记录使用的配置源

#### Scenario: 环境变量覆盖
- **WHEN** 设置环境变量配置
- **THEN** 环境变量应覆盖文件配置
- **AND** 支持所有关键配置字段的环境变量
- **AND** 环境变量命名遵循统一规范

#### Scenario: 配置合并逻辑
- **WHEN** 合并多个配置源
- **THEN** 系统应正确合并所有配置
- **AND** 字段级别的覆盖（而非整体覆盖）
- **AND** 保留未覆盖字段的原始值
