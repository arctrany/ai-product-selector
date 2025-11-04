# rpa-workflow-integration Specification

## Purpose
定义选品应用的流程控制和集成模块，负责店铺+商品的循环逻辑、流程节点的定义和集成、表单的输入输出等业务流程编排。基于workflow_engine现有的循环能力实现选品业务的完整工作流。

## Requirements
### Requirement: 选品工作流DSL定义
系统SHALL基于workflow_engine的现有循环能力，定义选品业务的完整工作流DSL，实现店铺和商品的嵌套循环处理。

#### Scenario: 选品工作流DSL结构
- **WHEN** 定义选品工作流DSL
- **THEN** 系统SHALL使用以下工作流结构：
  1. 开始节点 → Excel数据读取节点
  2. 店铺循环节点（基于workflow_engine的loop_node）
  3. 店铺循环内部：店铺数据抓取 → 店铺初筛 → 商品循环节点
  4. 商品循环内部：商品抓取 → 货源匹配 → 利润计算 → 评分更新
  5. 商品循环结束 → 店铺评分 → 状态更新
  6. 店铺循环结束 → 结果汇总 → 结束节点
- **AND** DSL SHALL使用workflow_engine的标准格式定义节点和连接
- **AND** DSL SHALL支持循环的暂停、恢复和中断机制

#### Scenario: 店铺循环节点配置
- **WHEN** 配置店铺循环节点
- **THEN** 系统SHALL基于Excel中的店铺数量动态设置循环次数
- **AND** 系统SHALL在每次循环中传递当前店铺信息到循环上下文
- **AND** 系统SHALL支持循环的暂停、恢复和跳过机制
- **AND** 系统SHALL维护店铺循环的执行状态和进度

#### Scenario: 商品循环节点配置
- **WHEN** 配置商品循环节点
- **THEN** 系统SHALL基于店铺商品数量和配置限制设置循环次数
- **AND** 系统SHALL在每次循环中传递当前商品信息到循环上下文
- **AND** 系统SHALL支持基于条件的提前退出（如达到评分要求）
- **AND** 系统SHALL维护商品循环的执行状态和进度

#### Scenario: 嵌套循环数据流转
- **WHEN** 处理嵌套循环的数据流转
- **THEN** 系统SHALL在店铺循环上下文中维护店铺级别的数据
- **AND** 系统SHALL在商品循环上下文中维护商品级别的数据
- **AND** 系统SHALL支持循环间的数据传递和状态同步
- **AND** 系统SHALL确保循环退出时的数据完整性

### Requirement: 业务节点实现和集成
系统SHALL实现选品业务的专用节点，集成data-scraping、profit-calculator和ai-image-similarity模块。

#### Scenario: Excel数据读取节点
- **WHEN** 执行Excel数据读取节点
- **THEN** 节点SHALL调用data-scraping模块读取Excel文件
- **AND** 节点SHALL筛选状态为"未处理"的店铺
- **AND** 节点SHALL返回店铺列表和总数量用于循环配置
- **AND** 节点SHALL设置店铺循环的初始参数

#### Scenario: 店铺数据处理节点
- **WHEN** 在店铺循环中执行店铺数据处理
- **THEN** 节点SHALL从循环上下文获取当前店铺信息
- **AND** 节点SHALL调用data-scraping模块抓取Seerfar店铺数据
- **AND** 节点SHALL应用初筛条件（销售额>50万，销量>250单）
- **AND** 节点SHALL决定是否继续商品循环处理

#### Scenario: 商品信息处理节点
- **WHEN** 在商品循环中执行商品信息处理
- **THEN** 节点SHALL从循环上下文获取当前商品信息
- **AND** 节点SHALL调用data-scraping模块抓取OZON和ERP数据
- **AND** 节点SHALL调用ai-image-similarity模块进行货源匹配
- **AND** 节点SHALL调用profit-calculator模块计算利润
- **AND** 节点SHALL更新商品处理状态和评分

#### Scenario: 循环控制节点
- **WHEN** 管理循环执行逻辑
- **THEN** 节点SHALL基于workflow_engine的loop_node实现循环控制
- **AND** 节点SHALL支持动态循环次数配置
- **AND** 节点SHALL处理循环条件判断和提前退出
- **AND** 节点SHALL维护循环计数器和进度信息

### Requirement: 表单输入和配置管理
系统SHALL管理选品应用的表单输入和业务配置参数。

#### Scenario: 用户表单输入处理
- **WHEN** 用户提交选品表单
- **THEN** 系统SHALL验证表单的完整性和有效性
- **AND** 系统SHALL包含以下表单字段（参考apps/sample_app/flow1/web/templates/index.htm）：
  - **文件配置**：
    - 好店模版文件（good_shop_file，必填，Excel格式）
    - 采品文件（item_collect_file，可选，Excel格式）
    - 计算器文件（margin_calculator，可选，Excel格式）
  - **筛选参数**：
    - 利润率大于等于（margin，默认0.1，范围0-1）
    - 商品创建天数小于等于（item_created_days，默认150天）
    - 跟卖数量小于（follow_buy_cnt，默认37个）
    - 月销量大于等于（max_monthly_sold，默认0）
    - 月销量小于等于（monthly_sold_min，默认100）
    - 商品最小重量（item_min_weight，默认0g）
    - 商品最大重量（item_max_weight，默认1000g）
    - G01商品最小售价（g01_item_min_price，默认0₽）
    - G01商品最大售价（g01_item_max_price，默认1000₽）
    - 每店铺最大商品数（max_products_per_store，默认50，范围1-200）
    - 输出格式（output_format，可选xlsx/csv/json）
  - **界面选项**：
    - 记住我的配置（remember_settings，复选框）
- **AND** 系统SHALL将表单配置转换为工作流执行参数

#### Scenario: 配置参数验证
- **WHEN** 验证配置参数
- **THEN** 系统SHALL验证文件路径的存在性和可访问性
- **AND** 系统SHALL验证数值参数的合理范围
- **AND** 系统SHALL提供参数验证失败的详细错误信息

#### Scenario: 应用配置管理
- **WHEN** 管理选品应用的配置参数
- **THEN** 系统SHALL维护以下应用级配置（不在表单中显示）：
  - 店铺评分阈值（默认2分）
  - 跟卖店铺采集数量（默认10个）
  - 店铺销售额阈值（默认50万）
  - 店铺销量阈值（默认250单）
- **AND** 系统SHALL支持配置参数的动态调整和热更新
- **AND** 系统SHALL提供配置参数的验证和范围检查

#### Scenario: 工作流参数映射
- **WHEN** 将表单参数映射到工作流
- **THEN** 系统SHALL将表单配置转换为工作流引擎的参数格式
- **AND** 系统SHALL合并表单参数和应用配置参数
- **AND** 系统SHALL设置循环节点的动态参数
- **AND** 系统SHALL配置业务节点的执行参数

### Requirement: 业务逻辑控制和决策
系统SHALL实现选品业务的核心逻辑控制和决策机制。

#### Scenario: 店铺初筛逻辑控制
- **WHEN** 执行店铺初筛
- **THEN** 系统SHALL根据销售额和销量阈值进行判断
- **AND** 如果不符合条件，系统SHALL标记为"否"并跳过商品循环
- **AND** 如果符合条件，系统SHALL继续执行商品循环处理

#### Scenario: 商品处理数量控制
- **WHEN** 处理店铺商品
- **THEN** 系统SHALL支持前x个商品的处理限制（x可配置）
- **AND** 系统SHALL记录每个商品的处理结果
- **AND** 系统SHALL支持基于条件的循环提前终止

#### Scenario: 店铺评分逻辑控制
- **WHEN** 计算店铺评分
- **THEN** 系统SHALL累计符合利润要求的商品数量
- **AND** 系统SHALL根据评分阈值判断是否为好店
- **AND** 系统SHALL支持店铺裂变判断（两个以上商品利润率>阈值）

### Requirement: 数据流转和状态管理
系统SHALL管理选品流程中的数据流转和状态跟踪。

#### Scenario: 循环数据传递
- **WHEN** 在循环节点间传递数据
- **THEN** 系统SHALL定义标准的循环上下文数据格式
- **AND** 系统SHALL包含店铺信息、商品信息、计算结果等数据
- **AND** 系统SHALL验证数据的完整性和一致性
- **AND** 系统SHALL支持循环状态的持久化和恢复

#### Scenario: 流程状态跟踪
- **WHEN** 跟踪流程执行状态
- **THEN** 系统SHALL记录每个循环迭代的执行状态和结果
- **AND** 系统SHALL支持流程进度的实时查询
- **AND** 系统SHALL提供详细的执行日志和错误信息

#### Scenario: 中间结果缓存
- **WHEN** 缓存中间处理结果
- **THEN** 系统SHALL支持关键数据的临时存储
- **AND** 系统SHALL支持流程中断后的数据恢复
- **AND** 系统SHALL管理缓存数据的生命周期

### Requirement: 异常处理和错误恢复
系统SHALL实现完善的异常处理和错误恢复机制。

#### Scenario: 循环异常处理
- **WHEN** 循环执行中发生异常
- **THEN** 系统SHALL捕获并分析异常类型
- **AND** 系统SHALL根据异常类型决定重试、跳过或终止策略
- **AND** 系统SHALL保持循环状态的一致性

#### Scenario: 业务模块异常适配
- **WHEN** 调用业务模块发生异常
- **THEN** 系统SHALL将业务异常转换为工作流标准异常
- **AND** 系统SHALL提供异常恢复建议和重试策略
- **AND** 系统SHALL记录详细的异常信息和处理过程

#### Scenario: 流程中断和恢复
- **WHEN** 流程执行中断
- **THEN** 系统SHALL保存当前循环状态和进度
- **AND** 系统SHALL支持从中断点继续执行
- **AND** 系统SHALL验证恢复时的数据一致性

### Requirement: 性能优化和资源管理
系统SHALL优化流程执行性能，合理管理系统资源。

#### Scenario: 循环性能优化
- **WHEN** 执行大量循环处理
- **THEN** 系统SHALL优化循环节点的执行效率
- **AND** 系统SHALL支持循环的批量处理优化
- **AND** 系统SHALL提供循环进度和性能监控

#### Scenario: 资源协调管理
- **WHEN** 协调各模块资源使用
- **THEN** 系统SHALL管理浏览器实例的复用和释放
- **AND** 系统SHALL协调Excel文件的并发访问
- **AND** 系统SHALL避免资源竞争和死锁

#### Scenario: 内存和存储优化
- **WHEN** 优化内存和存储使用
- **THEN** 系统SHALL优化循环数据的内存使用
- **AND** 系统SHALL支持大数据量的流式处理
- **AND** 系统SHALL提供资源使用监控和告警

### Requirement: 工作流DSL实现
系统SHALL实现具体的选品工作流DSL定义，支持workflow_engine的执行。

#### Scenario: 工作流定义文件
- **WHEN** 创建工作流定义文件
- **THEN** 系统SHALL使用workflow_engine的标准DSL格式
- **AND** 定义SHALL包含所有节点的配置和连接关系
- **AND** 定义SHALL支持参数化配置和动态调整

#### Scenario: 循环节点配置
- **WHEN** 配置循环节点
- **THEN** 系统SHALL基于workflow_engine的loop_node进行配置
- **AND** 配置SHALL包含循环次数、间隔时间、退出条件
- **AND** 配置SHALL支持嵌套循环的参数传递

#### Scenario: 工作流注册和部署
- **WHEN** 注册和部署工作流
- **THEN** 系统SHALL将工作流注册到workflow_engine
- **AND** 系统SHALL验证工作流定义的正确性
- **AND** 系统SHALL支持工作流的版本管理和热更新