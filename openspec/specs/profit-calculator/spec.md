# profit-calculator Specification

## Purpose
TBD - created by archiving change add-excel-profit-calculator. Update Purpose after archive.
## Requirements
### Requirement: Excel Calculator Component
系统SHALL实现基于Excel文件的利润计算器组件，使用openpyxl库操作"利润计算表"工作表进行跨平台利润计算。

#### Scenario: Excel文件初始化
- **WHEN** 提供Excel计算器文件路径（支持web upload目录或本地路径）
- **THEN** 系统SHALL使用openpyxl打开Excel文件并定位到"利润计算表"工作表
- **AND** 系统SHALL支持绝对路径和相对路径格式
- **AND** 组件实例SHALL可复用处理多次计算请求（支持1秒钟一次频率）

#### Scenario: 工作表定位和版本验证
- **WHEN** 初始化Excel计算器
- **THEN** 系统SHALL定位到名为"利润计算表"的工作表
- **AND** 系统SHALL验证工作表存在，如格式过旧SHALL提示"版本过旧"

### Requirement: 参数输入映射
系统SHALL将输入参数映射到Excel指定单元格：黑标价格(A2)、绿标价格(B2)、佣金率(C2)、重量(B3)。

#### Scenario: 黑标价格输入
- **WHEN** 接收黑标价格参数
- **THEN** 系统SHALL将值写入单元格A2
- **AND** 系统SHALL验证输入值为有效数字

#### Scenario: 绿标价格输入
- **WHEN** 接收绿标价格参数
- **THEN** 系统SHALL将值写入单元格B2
- **AND** 系统SHALL验证输入值为有效数字

#### Scenario: 佣金率输入
- **WHEN** 接收佣金率参数(如12表示12%)
- **THEN** 系统SHALL将百分比值转换为小数(12% -> 0.12)并写入单元格C2
- **AND** 系统SHALL验证佣金率为有效百分比数值

#### Scenario: 重量输入
- **WHEN** 接收重量参数
- **THEN** 系统SHALL将值写入单元格B3
- **AND** 重量SHALL以克(g)为单位输入
- **AND** 系统SHALL验证重量为正数

### Requirement: 计算结果读取
系统SHALL从Excel指定单元格读取计算结果：利润金额(G10)、利润率(H10)。

#### Scenario: 利润金额读取
- **WHEN** Excel计算完成后
- **THEN** 系统SHALL从单元格G10读取利润金额
- **AND** 利润金额SHALL以人民币格式返回

#### Scenario: 利润率读取
- **WHEN** Excel计算完成后
- **THEN** 系统SHALL从单元格H10读取利润率
- **AND** 利润率SHALL以百分比格式返回

### Requirement: Excel计算引擎调用
系统SHALL调用Excel计算引擎执行公式计算，确保所有依赖公式正确执行。

#### Scenario: 公式计算触发
- **WHEN** 所有输入参数设置完成
- **THEN** 系统SHALL触发Excel重新计算
- **AND** 系统SHALL等待所有公式计算完成

#### Scenario: 计算结果验证
- **WHEN** 读取计算结果
- **THEN** 系统SHALL验证结果为有效数值
- **AND** 异常结果SHALL返回明确的错误信息

### Requirement: 输出格式和验证
系统SHALL提供人性化的输出格式，支持日志系统集成，并验证结果合理性。

#### Scenario: 人性化输出格式
- **WHEN** 返回计算结果
- **THEN** 系统SHALL以易读格式输出利润信息
- **AND** 输出SHALL包含：利润金额(人民币)、利润率(百分比)、输入参数摘要

#### Scenario: 负数结果验证
- **WHEN** 计算结果为负数
- **THEN** 系统SHALL标记为"亏损"状态
- **AND** 系统SHALL返回明确的亏损提示信息
- **AND** 系统SHALL记录详细的计算过程用于日志

#### Scenario: 日志系统支持
- **WHEN** 执行任何计算操作
- **THEN** 系统SHALL生成结构化日志信息
- **AND** 日志SHALL包含：输入参数、计算过程、输出结果、执行时间

### Requirement: 性能和集成要求
系统SHALL支持高频调用和选品流程集成，确保跨平台兼容性。

#### Scenario: 高频调用支持
- **WHEN** 系统接收连续计算请求
- **THEN** 系统SHALL支持1秒钟一次的调用频率
- **AND** 系统SHALL复用Excel文件实例以提升性能
- **AND** 系统SHALL在内存中缓存工作表引用

#### Scenario: 选品流程集成
- **WHEN** 被选品流程调用
- **THEN** 系统SHALL提供函数式接口(无需REST API)
- **AND** 系统SHALL接收文件路径参数(支持web upload目录或本地路径)
- **AND** 系统SHALL验证文件路径存在性和可读性
- **AND** 系统SHALL返回标准化的计算结果对象

#### Scenario: 跨平台兼容性
- **WHEN** 在不同操作系统上运行
- **THEN** 系统SHALL使用openpyxl库确保跨平台兼容
- **AND** 系统SHALL在Windows/macOS/Linux上正常工作
- **AND** 系统SHALL无需依赖Microsoft Excel应用程序

### Requirement: 文件路径处理和验证
系统SHALL支持多种文件路径格式，确保路径安全性和可访问性。

#### Scenario: 文件路径格式支持
- **WHEN** 接收文件路径参数
- **THEN** 系统SHALL支持以下路径格式：
  - 绝对路径：`/path/to/file.xlsx`, `C:\path\to\file.xlsx`
  - 相对路径：`./uploads/file.xlsx`, `../data/file.xlsx`
  - Web upload目录路径：`uploads/profit_calc.xlsx`
- **AND** 系统SHALL自动规范化路径格式

#### Scenario: 路径安全验证
- **WHEN** 处理文件路径
- **THEN** 系统SHALL验证路径安全性，防止目录遍历攻击
- **AND** 系统SHALL检查文件扩展名为.xlsx或.xls
- **AND** 系统SHALL验证文件存在且可读

#### Scenario: 路径错误处理
- **WHEN** 文件路径无效或文件不存在
- **THEN** 系统SHALL返回明确的错误信息
- **AND** 错误信息SHALL包含：路径格式、文件存在性、权限问题等具体原因

