# profit-calculator Specification

## MODIFIED Requirements

### Requirement: 参数输入映射
系统SHALL将输入参数映射到Excel指定单元格，包括严格的真实黑标价格、绿标价格、佣金率、重量、尺寸、定价和采购成本。

#### Scenario: 真实黑标价格输入
- **WHEN** 接收真实黑标价格参数
- **THEN** 系统SHALL将值写入单元格A2
- **AND** 系统SHALL验证输入值为有效数字
- **AND** 价格SHALL为经过价格抓取逻辑处理后的真实价格

#### Scenario: 真实绿标价格输入
- **WHEN** 接收真实绿标价格参数
- **THEN** 系统SHALL将值写入单元格B2
- **AND** 系统SHALL验证输入值为有效数字
- **AND** 价格SHALL为经过价格抓取逻辑处理后的真实价格

#### Scenario: 佣金率输入
- **WHEN** 接收佣金率参数(如12表示12%)
- **THEN** 系统SHALL将百分比值转换为小数(12% -> 0.12)并写入单元格C2
- **AND** 系统SHALL验证佣金率为有效百分比数值
- **AND** 佣金率SHALL根据价格区间自动计算得出

#### Scenario: 重量输入
- **WHEN** 接收重量参数
- **THEN** 系统SHALL将值写入单元格B3
- **AND** 重量SHALL以克(g)为单位输入
- **AND** 系统SHALL验证重量为正数
- **AND** 重量SHALL从ERP插件区域采集获得

#### Scenario: 商品尺寸输入
- **WHEN** 接收商品尺寸参数
- **THEN** 系统SHALL将尺寸数据写入对应单元格
- **AND** 尺寸SHALL包含长宽高信息
- **AND** 系统SHALL验证尺寸数据的完整性

#### Scenario: 采购成本输入
- **WHEN** 接收采购成本参数
- **THEN** 系统SHALL将采购成本写入对应单元格
- **AND** 采购成本SHALL来自1688货源匹配结果或Mock数据
- **AND** 系统SHALL验证采购成本为有效正数

## ADDED Requirements

### Requirement: 定价自动计算
系统SHALL根据黑标价格区间自动计算商品的真实售价，并支持跟卖定价策略。

#### Scenario: 低价商品定价计算（90元以内）
- **WHEN** 黑标价格 <= 90人民币
- **THEN** 真实售价SHALL等于黑标价格
- **AND** 系统SHALL将计算结果写入定价单元格

#### Scenario: 中价商品定价计算（90-120元）
- **WHEN** 90人民币 < 黑标价格 <= 120人民币
- **THEN** 真实售价SHALL等于黑标价格 + 5元
- **AND** 系统SHALL将计算结果写入定价单元格

#### Scenario: 高价商品定价计算（120元以上）
- **WHEN** 黑标价格 > 120人民币
- **THEN** 真实售价SHALL等于 (黑标价格 - 绿标价格) * 2.2 + 黑标价格
- **AND** 当绿标价格不存在时，绿标价格SHALL等于黑标价格进行计算
- **AND** 系统SHALL将计算结果写入定价单元格

#### Scenario: 跟卖定价策略计算
- **WHEN** 需要计算跟卖定价
- **THEN** 系统SHALL从我们计算的真实售价和跟卖价格中找到最低值作为市场最低价
- **AND** 跟卖定价SHALL为市场最低价 * 跟卖折扣参数（默认0.95）
- **AND** 跟卖折扣参数SHALL支持配置调整
- **AND** 系统SHALL验证跟卖定价的合理性

### Requirement: 1688货源Mock集成
系统SHALL集成1688相似商品搜索API的Mock功能，基于alibaba.cross.similar.offer.search接口规范。

#### Scenario: 1688 API Mock成功
- **WHEN** 调用1688相似商品搜索API Mock
- **THEN** 系统SHALL模拟alibaba.cross.similar.offer.search-1接口返回
- **AND** Mock数据SHALL包含商品价格、供应商信息等关键字段
- **AND** 系统SHALL从Mock结果中提取采购价格作为采购成本输入

#### Scenario: 1688 API Mock失败
- **WHEN** Mock 1688 API调用失败
- **THEN** 系统SHALL终止当前商品的利润计算
- **AND** 系统SHALL记录API调用失败的原因
- **AND** 系统SHALL跳过该商品继续处理下一个商品

### Requirement: 严格参数验证和完整性检查
系统SHALL对所有输入参数进行严格验证，确保数据的完整性和准确性。

#### Scenario: 必需参数完整性验证
- **WHEN** 执行利润计算前
- **THEN** 系统SHALL验证以下参数均已提供且有效：
  - 真实黑标价格
  - 真实绿标价格
  - 佣金率
  - 商品重量
  - 商品尺寸
  - 定价
  - 采购成本
- **AND** 缺少任何必需参数时SHALL返回明确错误信息

#### Scenario: 参数数值合理性验证
- **WHEN** 接收到所有参数
- **THEN** 系统SHALL验证价格参数为正数
- **AND** 系统SHALL验证佣金率在合理范围内(0-100%)
- **AND** 系统SHALL验证重量和尺寸为正数
- **AND** 系统SHALL验证定价不低于采购成本

#### Scenario: 参数关联性验证
- **WHEN** 验证参数关联性
- **THEN** 系统SHALL验证绿标价格 <= 黑标价格
- **AND** 系统SHALL验证定价 >= 采购成本
- **AND** 系统SHALL验证计算结果的逻辑一致性

### Requirement: Excel文件跨平台兼容性
系统SHALL确保Excel文件操作在不同操作系统下的兼容性和一致性。

#### Scenario: Excel文件路径处理
- **WHEN** 处理Excel文件路径
- **THEN** 系统SHALL使用跨平台路径处理库（如Python的pathlib）
- **AND** 系统SHALL支持相对路径和绝对路径
- **AND** 系统SHALL避免硬编码文件路径分隔符

#### Scenario: Excel库跨平台支持
- **WHEN** 操作Excel文件
- **THEN** 系统SHALL使用跨平台Excel库（如openpyxl）
- **AND** 系统SHALL确保在Windows、macOS、Linux下功能一致
- **AND** 系统SHALL无需依赖Microsoft Excel应用程序

#### Scenario: 文件权限处理
- **WHEN** 读写Excel文件
- **THEN** 系统SHALL检查文件读写权限
- **AND** 系统SHALL处理不同操作系统的权限模型差异
- **AND** 系统SHALL提供明确的权限错误提示

#### Scenario: 临时文件管理
- **WHEN** 创建临时Excel文件
- **THEN** 系统SHALL使用操作系统标准临时目录
- **AND** 系统SHALL确保临时文件的自动清理
- **AND** 系统SHALL避免临时文件路径冲突