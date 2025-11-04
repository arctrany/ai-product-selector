# data-scraping Specification

## Purpose
定义数据抓取模块，专门负责从各个平台和插件抓取数据，支持多平台配置化抓取，包括但不限于Seerfar、OZON、1688等平台。

## Requirements

### Requirement: 平台配置化管理
系统SHALL支持多平台配置化管理，避免硬编码平台特定信息，实现平台无关的抓取架构。

#### Scenario: 平台配置定义
- **WHEN** 配置抓取平台
- **THEN** 系统SHALL支持通过配置文件定义平台信息：
  - 平台名称和标识符
  - 基础URL和API端点
  - 页面元素选择器映射
  - 平台特定的业务规则
- **AND** 系统SHALL支持运行时动态加载平台配置
- **AND** 系统SHALL验证平台配置的完整性和有效性

#### Scenario: 多平台适配器模式
- **WHEN** 实现平台抓取逻辑
- **THEN** 系统SHALL使用适配器模式支持不同平台：
  - 定义统一的抓取接口
  - 为每个平台实现专用适配器
  - 支持平台特定的数据转换逻辑
- **AND** 系统SHALL支持新平台的插件式扩展
- **AND** 系统SHALL提供平台兼容性检查机制

#### Scenario: 平台URL配置化
- **WHEN** 访问平台页面
- **THEN** 系统SHALL从配置中读取平台URL模板
- **AND** 系统SHALL支持URL参数的动态替换
- **AND** 系统SHALL支持多环境URL配置（开发、测试、生产）
- **AND** 系统SHALL提供URL有效性验证

### Requirement: Excel数据读取和处理
系统SHALL读取用户提交的Excel表单数据，提供标准化的数据接口。

#### Scenario: Excel文件读取
- **WHEN** 读取用户提交的Excel文件
- **THEN** 系统SHALL验证包含三列：店铺ID、是否为好店（是｜否｜空）、状态（已处理｜未处理｜空）
- **AND** 系统SHALL验证数据格式的完整性和有效性
- **AND** 系统SHALL返回标准化的店铺数据列表

#### Scenario: Excel状态筛选
- **WHEN** 筛选待处理店铺
- **THEN** 系统SHALL仅返回状态为"未处理"的店铺
- **AND** 系统SHALL跳过状态为"已处理"或空的店铺
- **AND** 系统SHALL提供筛选结果统计信息

### Requirement: 店铺数据抓取（平台无关）
系统SHALL从配置的平台抓取店铺的销售数据和基本信息，支持多平台适配。

#### Scenario: 店铺页面访问
- **WHEN** 访问店铺详情页
- **THEN** 系统SHALL根据平台配置构建访问URL
- **AND** 系统SHALL支持平台特定的认证和会话管理
- **AND** 系统SHALL等待页面完全加载
- **AND** 系统SHALL处理页面加载异常和重试机制

#### Scenario: 店铺销售数据抓取
- **WHEN** 抓取店铺销售数据
- **THEN** 系统SHALL根据平台配置的选择器抓取销售数据
- **AND** 系统SHALL支持可配置的数据字段映射：
  - 销售额字段（如：sold_30days）
  - 销量字段
  - 日均销量字段
- **AND** 系统SHALL验证数据的数值格式和合理性
- **AND** 系统SHALL支持平台特定的数据单位转换

### Requirement: 商品数据抓取（平台无关）
系统SHALL从配置的电商平台抓取商品的详细信息，包括价格、图片和基本属性。

#### Scenario: 商品列表遍历
- **WHEN** 遍历店铺商品列表
- **THEN** 系统SHALL根据平台配置的选择器采集商品信息：
  - 商品图片URL（可配置选择器）
  - 品牌名称（可配置选择器）
  - SKU信息（可配置选择器）
- **AND** 系统SHALL提供商品列表的分页处理
- **AND** 系统SHALL支持平台特定的商品列表结构

#### Scenario: 商品详情页数据抓取
- **WHEN** 访问商品详情页
- **THEN** 系统SHALL根据平台配置点击商品链接
- **AND** 系统SHALL根据平台配置的价格选择器抓取价格信息：
  - 主要价格（如：绿标价格）
  - 次要价格（如：黑标价格）
  - 促销价格
- **AND** 系统SHALL处理价格不存在的情况

#### Scenario: 竞品价格和店铺信息抓取
- **WHEN** 抓取竞品信息
- **THEN** 系统SHALL根据平台配置的价格对比逻辑选择抓取策略
- **AND** 系统SHALL支持可配置的竞品信息采集：
  - 竞品数量限制（可配置）
  - 竞品店铺信息字段
  - 竞品价格比较规则
- **AND** 系统SHALL处理平台特定的竞品展示方式

### Requirement: 插件数据抓取（可扩展）
系统SHALL支持从各种浏览器插件抓取数据，提供可扩展的插件适配机制。

#### Scenario: 插件数据源配置
- **WHEN** 配置插件数据源
- **THEN** 系统SHALL支持插件信息的配置化定义：
  - 插件名称和版本
  - 数据渲染区域选择器
  - 数据字段映射规则
- **AND** 系统SHALL支持多插件数据源
- **AND** 系统SHALL提供插件兼容性检查

#### Scenario: 佣金率数据抓取（可配置规则）
- **WHEN** 抓取商品佣金率
- **THEN** 系统SHALL从配置中读取佣金率计算规则：
  - 价格区间定义（可配置货币单位）
  - 佣金率映射表
  - 特殊规则处理逻辑
- **AND** 系统SHALL支持多货币和汇率转换
- **AND** 系统SHALL验证佣金率数据的有效性

#### Scenario: 商品属性抓取（标准化）
- **WHEN** 抓取商品物理属性
- **THEN** 系统SHALL根据配置抓取商品属性：
  - 重量信息（支持多单位）
  - 尺寸信息（长宽高，支持多单位）
  - 其他平台特定属性
- **AND** 系统SHALL进行单位标准化处理
- **AND** 系统SHALL验证物理属性数据的合理性

### Requirement: API数据抓取（多平台支持）
系统SHALL通过配置的API获取货源匹配数据，支持多个供应商平台的API集成。

#### Scenario: API平台配置
- **WHEN** 配置API数据源
- **THEN** 系统SHALL支持多API平台配置：
  - API端点和认证信息
  - 请求参数映射
  - 响应数据解析规则
- **AND** 系统SHALL支持API版本管理
- **AND** 系统SHALL处理API调用的认证和限流

#### Scenario: 货源匹配API调用
- **WHEN** 调用货源匹配API
- **THEN** 系统SHALL根据平台配置调用相应API
- **AND** 系统SHALL支持多种搜索方式：
  - 图片相似度搜索
  - 关键词搜索
  - 商品属性匹配
- **AND** 系统SHALL处理不同API的响应格式

#### Scenario: API结果标准化
- **WHEN** 处理API返回结果
- **THEN** 系统SHALL将不同平台的API结果标准化：
  - 统一的商品信息格式
  - 标准化的价格和供应商信息
  - 一致的匹配度评分
- **AND** 系统SHALL提供结果质量评估
- **AND** 系统SHALL支持结果过滤和排序

### Requirement: 跨平台兼容性
系统SHALL确保在Windows、macOS、Linux等多种操作系统环境下正常运行，避免任何硬编码和平台特定依赖。

#### Scenario: 文件路径处理兼容性
- **WHEN** 处理文件路径（Excel文件、配置文件等）
- **THEN** 系统SHALL使用跨平台的路径处理方法
- **AND** 系统SHALL支持Windows路径分隔符（\）和Unix路径分隔符（/）
- **AND** 系统SHALL避免硬编码绝对路径
- **AND** 系统SHALL使用相对路径或环境变量配置路径

#### Scenario: 浏览器驱动兼容性
- **WHEN** 启动浏览器进行网页抓取
- **THEN** 系统SHALL自动检测当前操作系统类型
- **AND** 系统SHALL使用对应操作系统的浏览器驱动
- **AND** 系统SHALL支持多种浏览器（Chrome、Firefox、Edge等）
- **AND** 系统SHALL处理驱动版本兼容性问题

#### Scenario: 字符编码兼容性
- **WHEN** 处理文本数据和文件操作
- **THEN** 系统SHALL统一使用UTF-8编码
- **AND** 系统SHALL处理不同平台的字符编码差异
- **AND** 系统SHALL支持多语言内容的正确处理

### Requirement: 配置管理和验证
系统SHALL提供完整的配置管理机制，支持配置验证、热更新和版本管理。

#### Scenario: 配置文件结构
- **WHEN** 定义配置文件
- **THEN** 系统SHALL使用标准化的配置格式（JSON/YAML）
- **AND** 配置SHALL包含以下部分：
  - 平台定义（platforms）
  - 选择器映射（selectors）
  - 业务规则（business_rules）
  - API配置（api_configs）
- **AND** 系统SHALL支持配置的模块化和继承

#### Scenario: 配置验证机制
- **WHEN** 加载配置文件
- **THEN** 系统SHALL验证配置的语法和结构
- **AND** 系统SHALL验证必需字段的完整性
- **AND** 系统SHALL验证配置值的有效性和合理性
- **AND** 系统SHALL提供详细的配置错误信息

#### Scenario: 配置热更新
- **WHEN** 更新配置文件
- **THEN** 系统SHALL支持配置的热更新
- **AND** 系统SHALL验证新配置的兼容性
- **AND** 系统SHALL提供配置回滚机制
- **AND** 系统SHALL记录配置变更历史

### Requirement: 数据验证和清洗
系统SHALL对抓取的数据进行验证和清洗，确保数据质量和一致性。

#### Scenario: 数据格式验证
- **WHEN** 验证抓取数据
- **THEN** 系统SHALL验证价格数据为有效数值
- **AND** 系统SHALL验证重量和尺寸数据的合理范围
- **AND** 系统SHALL验证店铺ID和SKU格式的正确性

#### Scenario: 数据清洗处理
- **WHEN** 清洗抓取数据
- **THEN** 系统SHALL去除数据中的特殊字符和空白
- **AND** 系统SHALL标准化货币单位和数值格式
- **AND** 系统SHALL处理缺失数据和异常值

#### Scenario: 数据完整性检查
- **WHEN** 检查数据完整性
- **THEN** 系统SHALL验证必需字段的完整性
- **AND** 系统SHALL标记不完整或异常的数据记录
- **AND** 系统SHALL提供数据质量报告

### Requirement: Excel结果输出
系统SHALL将抓取和处理结果输出到Excel文件，支持状态更新和结果汇总。

#### Scenario: 店铺状态更新
- **WHEN** 更新店铺处理状态
- **THEN** 系统SHALL更新Excel中的"是否为好店"列
- **AND** 系统SHALL更新"状态"列为"已处理"
- **AND** 系统SHALL保持原有数据的完整性

#### Scenario: 竞品店铺信息输出
- **WHEN** 输出竞品店铺信息
- **THEN** 系统SHALL在Excel中新增竞品店铺信息列
- **AND** 系统SHALL包含店铺ID和相关详细信息
- **AND** 系统SHALL保持与好店Excel格式的一致性

#### Scenario: 批量数据导出
- **WHEN** 导出处理结果
- **THEN** 系统SHALL支持批量数据的Excel导出
- **AND** 系统SHALL提供数据导出的进度反馈
- **AND** 系统SHALL验证导出文件的完整性