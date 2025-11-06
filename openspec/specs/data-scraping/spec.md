# good-store-selection Specification

## Purpose
定义好店筛选系统，专门负责从Seerfar平台抓取OZON店铺和商品数据，通过Excel利润计算器进行利润计算，实现自动化的好店筛选和利润评估的完整业务流程。

## Requirements

### Requirement: Excel数据读取和处理
系统SHALL读取用户提交的Excel表单数据，提供标准化的店铺数据接口。

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

### Requirement: Seerfar店铺信息抓取
系统SHALL从Seerfar平台抓取OZON店铺的销售数据，进行初筛验证，实现店铺级别的筛选。

#### Scenario: Seerfar店铺页面访问
- **WHEN** 访问店铺详情页
- **THEN** 系统SHALL构建Seerfar访问URL：`https://seerfar.cn/admin/store-detail.html?storeId={店铺ID}&platform=OZON`
- **AND** 系统SHALL等待页面完全加载
- **AND** 系统SHALL处理页面加载异常和重试机制

#### Scenario: 店铺销售数据抓取
- **WHEN** 抓取店铺销售数据
- **THEN** 系统SHALL抓取以下关键指标：
  - 店铺销售额_30天 (sold_30days)
  - 店铺销量_30天 (sold_count_30days)
  - 日均销量 (daily_avg_sold)
- **AND** 系统SHALL验证数据的数值格式和合理性
- **AND** 系统SHALL支持数据单位转换（卢布等）

#### Scenario: 店铺初筛条件验证
- **WHEN** 验证店铺是否符合初筛条件
- **THEN** 系统SHALL检查店铺销售额_30天 > 50万
- **AND** 系统SHALL检查店铺销量_30天 > 250单
- **AND** 如果不符合条件，系统SHALL标记"是否为好店"为"否"，状态为"已处理"并跳过该店铺
- **AND** 系统SHALL支持初筛条件参数的配置调整（利润计算参数值会调整）

### Requirement: Seerfar店铺商品列表抓取
系统SHALL从Seerfar平台抓取店铺的商品列表信息，为后续商品详情抓取提供基础数据。

#### Scenario: 商品列表遍历
- **WHEN** 遍历店铺商品列表
- **THEN** 系统SHALL循环商品表格，从商品表格第二列采集：
  - 商品图片URL
  - 品牌名称
  - SKU信息
- **AND** 系统SHALL提供商品列表的分页处理
- **AND** 系统SHALL支持商品列表的完整遍历
- **AND** 系统SHALL通过抓取商品信息和利润计算器判断店铺是否需要"裂变"

### Requirement: OZON商品最低价抓取
系统SHALL从OZON平台抓取商品的价格信息，确定真实的最低价格。

#### Scenario: 商品详情页价格抓取
- **WHEN** 点击商品图片进入OZON商品详情页
- **THEN** 系统SHALL抓取价格信息：
  - 绿标价格（促销价格）
  - 黑标价格（商品原价）
  - 跟卖黑标价格 (跟卖黑标价格)
- **AND** 系统SHALL处理绿标价格不存在的情况，使用黑标价格对比
- **AND** 系统SHALL根据价格比较逻辑确定真实价格

#### Scenario: 价格比较和真实价格确定
- **WHEN** 比较绿标价格和跟卖价格
- **THEN** 如果绿标价格 <= 跟卖价格（分支1）：
  - 系统SHALL使用当前商品详情页的绿标、黑标价格作为真实价格
- **AND** 如果绿标价格 > 跟卖黑标价格（分支2）：
  - 系统SHALL点击黑标价格打开跟卖浮层
  - 系统SHALL点击浮层中的绿标跳转获取更低的价格

### Requirement: 跟卖店铺信息抓取
系统SHALL在商品利润符合预期时采集跟卖店铺信息，为店铺裂变提供竞争对手数据。

#### Scenario: 跟卖店铺信息采集执行
- **WHEN** 商品利润率 >= 配置阈值（默认20%）
- **THEN** 系统SHALL点击黑标价格打开跟卖浮层
- **AND** 系统SHALL从浮层获取前N个（默认10个）店铺信息
- **AND** 如果浮层中有"更多"标签，系统SHALL先点击展开
- **AND** 采集的信息SHALL包括店铺ID等关键信息

#### Scenario: 跟卖店铺信息输出
- **WHEN** 成功采集跟卖店铺信息
- **THEN** 系统SHALL将跟卖店铺ID输出到Excel
- **AND** 系统SHALL包含店铺ID和相关详细信息
- **AND** 系统SHALL避免重复采集相同商品的跟卖信息

### Requirement: 毛子ERP插件数据抓取
系统SHALL从毛子ERP插件渲染区域一次性抓取商品的佣金率、重量和尺寸信息。

#### Scenario: 插件数据源自动加载
- **WHEN** 系统启动时
- **THEN** 系统SHALL自动检测和加载毛子ERP插件
- **AND** 系统SHALL自动配置插件数据渲染区域选择器
- **AND** 系统SHALL自动进行插件兼容性检查

#### Scenario: 佣金率数据抓取和计算
- **WHEN** 抓取商品佣金率
- **THEN** 系统SHALL从毛子ERP插件渲染区域采集佣金率信息
- **AND** 系统SHALL根据以下规则计算佣金率：
  - 绿标价格 <= 1500卢布：佣金率 = 12%
  - 1500卢布 < 绿标价格 <= 5000卢布：选择第二个label里的数字
  - 绿标价格 > 5000卢布：选择第三个label里的数字
- **AND** 系统SHALL验证佣金率数据的有效性

#### Scenario: 商品物理属性抓取
- **WHEN** 抓取商品物理属性
- **THEN** 系统SHALL从毛子ERP插件渲染区域获取：
  - 商品重量信息
  - 商品尺寸信息（长宽高）
- **AND** 系统SHALL进行单位标准化处理
- **AND** 系统SHALL验证物理属性数据的合理性

### Requirement: 利润计算和店铺评分
系统SHALL通过商品定价、货源匹配和Excel利润计算器完成利润计算，并进行店铺评分判定。

#### Scenario: 商品定价计算
- **WHEN** 计算商品定价
- **THEN** 系统SHALL使用价格比较后确定的最终价格（绿标价格、黑标价格）
- **AND** 系统SHALL根据以下规则计算真实售价：
  - 只有黑标价格：真实售价 = 黑标价格
  - 黑标价格 <= 90人民币：真实售价 = 黑标价格
  - 90人民币 < 黑标价格 <= 120人民币：真实售价 = 黑标价格 + 5
  - 黑标价格 > 120人民币：真实售价 = (黑标 - 绿标) × 2.2 + 黑标
- **AND** 系统SHALL计算商品定价：定价 = 真实售价 × 0.95（95折）
- **AND** 系统SHALL验证计算结果的合理性
- **AND** 系统SHALL支持汇率转换（卢布转人民币）
- **AND** 系统SHALL支持配置化参数以便后续调整

#### Scenario: 货源匹配检查
- **WHEN** 进行货源匹配
- **THEN** 系统SHALL调用货源匹配函数，输入商品图片信息等参数
- **AND** 系统SHALL通过Mock接口模拟1688 API和AI匹配能力
- **AND** 如果匹配成功，系统SHALL获得采购价格
- **AND** 如果匹配失败，系统SHALL跳过该商品不进行处理
- **AND** 系统SHALL为未来集成真实1688 API预留接口

#### Scenario: Excel利润计算器初始化
- **WHEN** 初始化Excel利润计算器
- **THEN** 系统SHALL使用openpyxl打开利润计算器Excel文件
- **AND** 系统SHALL验证工作表格式和版本兼容性
- **AND** 系统SHALL支持计算器文件路径的配置

#### Scenario: Excel利润计算器调用
- **WHEN** 计算商品利润
- **THEN** 系统SHALL调用Excel利润计算函数，输入以下参数：
  - 商品长宽高
  - 商品重量
  - 绿标价格
  - 黑标价格
  - 佣金率
  - 商品定价（真实售价 × 0.95）
  - 采购价格（货源匹配获得）
- **AND** 系统SHALL通过Excel计算器自动输出利润和利润率
- **AND** 系统SHALL验证计算结果的准确性
- **AND** 系统SHALL为未来独立利润计算模块预留接口

#### Scenario: 商品利润评估
- **WHEN** 评估商品利润
- **THEN** 系统SHALL使用公式：利润率 = 利润 / 备货成本
- **AND** 如果商品利润率 >= 预期值（默认20%）：
  - 系统SHALL记录该商品为有利润商品
  - 系统SHALL触发跟卖店铺信息采集
- **AND** 如果商品利润率 < 预期值，系统SHALL跳过该商品
- **AND** 系统SHALL记录评估过程和结果
- **AND** 系统SHALL支持利润率阈值的配置调整

#### Scenario: 好店判定和裂变判断
- **WHEN** 店铺遍历完毕
- **THEN** 系统SHALL统计前N个商品中利润率 > 配置阈值（默认20%）的商品数量
- **AND** 如果有利润商品个数超过配置比例（默认20%），系统SHALL判定为好店（需要裂变的店铺）：
  - 系统SHALL将该店铺标记为好店
  - 系统SHALL更新状态为"已处理"
  - 系统SHALL输出店铺信息到Excel
  - 系统SHALL标记该店铺需要裂变
- **AND** 系统SHALL继续下一个店铺的遍历
- **AND** 系统SHALL提供任务完成统计
- **AND** 系统SHALL支持利润率阈值和好店比例阈值的配置调整

### Requirement: 跨平台兼容性
系统SHALL确保在Windows、macOS、Linux等多种操作系统环境下正常运行。

#### Scenario: 文件路径处理兼容性
- **WHEN** 处理文件路径（Excel文件、配置文件等）
- **THEN** 系统SHALL使用跨平台的路径处理方法（如Python的pathlib.Path）
- **AND** 系统SHALL支持Windows路径分隔符（\）和Unix路径分隔符（/）
- **AND** 系统SHALL避免硬编码绝对路径

#### Scenario: 浏览器驱动兼容性
- **WHEN** 启动浏览器进行网页抓取
- **THEN** 系统SHALL自动检测当前操作系统类型
- **AND** 系统SHALL使用对应操作系统的浏览器驱动
- **AND** 系统SHALL支持多种浏览器（Chrome、Firefox、Edge等）

#### Scenario: Excel库跨平台支持
- **WHEN** 操作Excel文件
- **THEN** 系统SHALL使用跨平台Excel库（如openpyxl）
- **AND** 系统SHALL确保在Windows、macOS、Linux下功能一致
- **AND** 系统SHALL处理不同操作系统的文件权限差异

#### Scenario: 字符编码兼容性
- **WHEN** 处理文本数据和文件操作
- **THEN** 系统SHALL统一使用UTF-8编码
- **AND** 系统SHALL处理不同平台的字符编码差异
- **AND** 系统SHALL支持多语言内容的正确处理

### Requirement: 数据验证和错误处理
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

### Requirement: 批量处理和性能优化
系统SHALL支持大批量商品的数据抓取和利润计算。

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

### Requirement: Excel结果输出
系统SHALL将抓取和处理结果输出到Excel文件，支持状态更新和结果汇总。

#### Scenario: 店铺状态更新
- **WHEN** 更新店铺处理状态
- **THEN** 系统SHALL更新Excel中的"是否为好店"列
- **AND** 系统SHALL更新"状态"列为"已处理"
- **AND** 系统SHALL保持原有数据的完整性

#### Scenario: 批量数据导出
- **WHEN** 导出处理结果
- **THEN** 系统SHALL支持批量数据的Excel导出
- **AND** 系统SHALL提供数据导出的进度反馈
- **AND** 系统SHALL验证导出文件的完整性