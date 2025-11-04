# profit-calculator Specification

## Purpose
定义利润计算模块，专门负责通过Excel计算器进行利润计算，以及相关的定价策略、佣金率计算、店铺评分等核心计算功能。系统不进行复杂的自主计算，主要通过调用Excel计算器实现。

## Requirements

### Requirement: 跨操作系统兼容性
系统SHALL确保在Windows、macOS、Linux等操作系统上稳定运行，避免平台特定依赖。

#### Scenario: Excel库跨平台支持
- **WHEN** 操作Excel文件
- **THEN** 系统SHALL使用跨平台Excel库（如openpyxl）
- **AND** 系统SHALL确保在Windows、macOS、Linux下功能一致
- **AND** 系统SHALL处理不同操作系统的文件权限差异

#### Scenario: 文件路径处理兼容性
- **WHEN** 处理Excel文件路径
- **THEN** 系统SHALL使用跨平台路径处理库（如Python的pathlib.Path）
- **AND** 系统SHALL避免硬编码路径分隔符（/ 或 \）
- **AND** 系统SHALL支持相对路径和绝对路径

### Requirement: 商品定价计算
系统SHALL根据原始需求中的定价规则计算商品的真实售价。

#### Scenario: 真实售价计算规则
- **WHEN** 计算商品真实售价
- **THEN** 系统SHALL根据以下定价规则计算真实售价：
  - **规则1**: 只有黑标价格时，真实售价 = 黑标价格
  - **规则2**: 黑标价格在90以内时，真实售价 = 黑标价格
  - **规则3**: 黑标价格90-120人民币时，真实售价 = 黑标价格 + 5
  - **规则4**: 黑标价格在120人民币以上时，真实售价 = (黑标价格 - 绿标价格) * 2.2 + 黑标价格
- **AND** 系统SHALL支持配置化参数以便后续调整
- **AND** 系统SHALL处理绿标价格不存在的情况

### Requirement: 佣金率计算
系统SHALL根据原始需求中的佣金率规则计算商品佣金率。

#### Scenario: 佣金率计算规则
- **WHEN** 计算商品佣金率
- **THEN** 系统SHALL根据以下规则计算佣金率：
  - 绿标价格 <= 1500卢布时，佣金率 = 12%
  - 1500卢布 < 绿标价格 <= 5000卢布时，选择第二个label里的数字
  - 绿标价格 > 5000卢布时，选择第三个label里的数字
- **AND** 系统SHALL支持配置化参数以便后续调整
- **AND** 系统SHALL处理多货币转换

### Requirement: Excel利润计算器集成
系统SHALL集成Excel利润计算器，通过输入参数调用Excel进行利润计算。

#### Scenario: Excel计算器初始化
- **WHEN** 初始化Excel利润计算器
- **THEN** 系统SHALL使用openpyxl打开利润计算器Excel文件
- **AND** 系统SHALL验证工作表格式和版本兼容性
- **AND** 系统SHALL支持计算器文件路径的配置

#### Scenario: 利润计算参数输入
- **WHEN** 输入利润计算参数
- **THEN** 系统SHALL将以下参数写入Excel对应单元格：
  - 真实的黑标价格
  - 真实的绿标价格
  - 佣金率
  - 商品重量
  - 商品尺寸
  - 定价
  - 采购成本
- **AND** 系统SHALL验证所有输入参数的有效性

#### Scenario: 利润计算结果读取
- **WHEN** 读取利润计算结果
- **THEN** 系统SHALL从Excel计算器读取利润金额和利润率
- **AND** 系统SHALL验证计算结果的合理性
- **AND** 系统SHALL确保结果格式的一致性

### Requirement: 利润率评估和判断
系统SHALL根据利润率进行商品评估判断。

#### Scenario: 商品利润率判断
- **WHEN** 判断商品是否符合利润要求
- **THEN** 系统SHALL使用公式：利润率 = 利润 / 备货成本
- **AND** 系统SHALL使用默认阈值20%进行判断
- **AND** 如果商品利润率 >= 20%，系统SHALL标记为符合要求
- **AND** 如果利润率 < 20%，系统SHALL标记为不符合要求
- **AND** 系统SHALL支持利润率阈值的配置调整

### Requirement: 店铺评分计算
系统SHALL根据商品利润表现计算店铺评分。

#### Scenario: 店铺评分累计
- **WHEN** 累计店铺评分
- **THEN** 如果商品利润率 >= 20%，系统SHALL为店铺评分+1
- **AND** 系统SHALL记录每个商品的利润贡献
- **AND** 系统SHALL统计店铺的整体评分

#### Scenario: 好店判断标准
- **WHEN** 判断是否为好店
- **THEN** 如果店铺评分 >= 2，系统SHALL标记为好店
- **AND** 系统SHALL将店铺信息更新为"是"，状态更新为"已处理"
- **AND** 系统SHALL支持好店评分阈值的配置调整

#### Scenario: 店铺裂变判断
- **WHEN** 判断店铺是否需要裂变
- **THEN** 系统SHALL统计前x个商品中利润率 > y%的商品数量
- **AND** 如果有两个以上商品符合条件，系统SHALL判定需要裂变
- **AND** 系统SHALL支持x和y参数的配置调整

### Requirement: 跟卖店铺信息处理
系统SHALL处理符合利润要求的商品的跟卖店铺信息。

#### Scenario: 跟卖店铺信息输出
- **WHEN** 商品利润符合预期
- **THEN** 系统SHALL将跟卖店铺列表输出到Excel
- **AND** 系统SHALL包含店铺ID等关键信息
- **AND** 系统SHALL支持批量处理和验证

### Requirement: 批量计算和性能优化
系统SHALL支持大批量商品的利润计算。

#### Scenario: 批量Excel操作
- **WHEN** 处理大量商品计算
- **THEN** 系统SHALL优化Excel文件的读写操作
- **AND** 系统SHALL支持批量参数输入
- **AND** 系统SHALL提供计算进度反馈

#### Scenario: Excel文件管理
- **WHEN** 管理Excel文件访问
- **THEN** 系统SHALL避免频繁打开关闭Excel文件
- **AND** 系统SHALL处理Excel文件的并发访问
- **AND** 系统SHALL确保数据的完整性

### Requirement: 错误处理和数据验证
系统SHALL对计算过程进行错误处理和数据验证。

#### Scenario: 参数验证
- **WHEN** 验证输入参数
- **THEN** 系统SHALL检查价格数据的有效性
- **AND** 系统SHALL验证重量和尺寸数据的合理性
- **AND** 系统SHALL处理缺失或异常数据

#### Scenario: 计算结果验证
- **WHEN** 验证计算结果
- **THEN** 系统SHALL检查利润率的合理范围
- **AND** 系统SHALL识别异常的计算结果
- **AND** 系统SHALL提供详细的错误信息

#### Scenario: Excel文件错误处理
- **WHEN** 处理Excel文件错误
- **THEN** 系统SHALL处理文件不存在或损坏的情况
- **AND** 系统SHALL提供文件访问权限错误的处理
- **AND** 系统SHALL支持Excel文件格式验证