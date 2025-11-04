# data-scraping Specification

## ADDED Requirements

### Requirement: Excel数据读取和店铺筛选
系统SHALL读取用户提交的Excel表单数据，包含店铺ID、好店标记和处理状态，并按状态进行筛选处理。

#### Scenario: Excel数据结构验证
- **WHEN** 读取Excel文件
- **THEN** 系统SHALL验证包含三列：店铺ID、是否为好店（是｜否｜空）、状态（已处理｜未处理｜空）
- **AND** 系统SHALL验证数据格式的完整性

#### Scenario: 未处理店铺筛选
- **WHEN** 遍历Excel数据行
- **THEN** 系统SHALL仅处理状态为"未处理"的店铺
- **AND** 系统SHALL跳过状态为"已处理"或空的店铺

### Requirement: 店铺页面数据抓取
系统SHALL访问店铺详情页面并抓取销售数据，包括30天销售额、销量和日均销量。

#### Scenario: 店铺页面访问
- **WHEN** 处理未处理状态的店铺
- **THEN** 系统SHALL访问 https://seerfar.cn/admin/store-detail.html?storeId={店铺ID}&platform=OZON
- **AND** 系统SHALL等待页面完全加载
- **AND** URL中的storeId参数SHALL使用Excel第一列中的店铺ID值
- **AND** platform参数SHALL固定为"OZON"

#### Scenario: 店铺销售数据抓取
- **WHEN** 店铺页面加载完成
- **THEN** 系统SHALL抓取店铺销售额_30天数据
- **AND** 系统SHALL抓取店铺销量_30天数据
- **AND** 系统SHALL抓取日均销量数据
- **AND** 所有数据SHALL为数值格式

### Requirement: 店铺初筛条件验证
系统SHALL根据销售数据进行店铺初筛，不符合条件的店铺标记为"否"并跳过。

#### Scenario: 销售额和销量筛选
- **WHEN** 获取到店铺销售数据
- **THEN** 系统SHALL验证店铺销售额_30天 > 50万
- **AND** 系统SHALL验证店铺销量_30天 > 250单
- **AND** 不符合条件的店铺SHALL标记第二列为"否"，第三列为"已处理"

### Requirement: 商品信息采集
系统SHALL从商品列表中采集商品图片、品牌名称和SKU信息。

#### Scenario: 商品列表遍历
- **WHEN** 店铺通过初筛
- **THEN** 系统SHALL遍历商品表格
- **AND** 系统SHALL从表格第二列采集商品图片、品牌名称、SKU信息

#### Scenario: 商品详情页访问
- **WHEN** 点击商品图片
- **THEN** 系统SHALL进入OZON商品详情页
- **AND** 系统SHALL等待页面加载完成

### Requirement: 商品价格抓取和处理
系统SHALL抓取商品的绿标价格和黑标价格，当绿标价格不存在时使用黑标价格进行对比。

#### Scenario: 绿标价格存在时的处理
- **WHEN** 商品详情页加载完成且绿标价格存在
- **THEN** 系统SHALL获取绿标价格和黑标价格
- **AND** 系统SHALL获取跟卖黑标价格

#### Scenario: 绿标价格不存在时的降级处理
- **WHEN** 商品详情页绿标价格不存在
- **THEN** 系统SHALL将绿标价格设置为等于黑标价格
- **AND** 系统SHALL使用黑标价格进行所有后续计算
- **AND** 系统SHALL记录绿标价格缺失并使用黑标替代的情况

### Requirement: 真实价格计算逻辑
系统SHALL根据绿标和跟卖价格的对比关系，计算真实的绿标和黑标价格。

#### Scenario: 绿标价格小于等于跟卖价格
- **WHEN** 绿标价格 <= 跟卖黑标价格
- **THEN** 真实绿标价格SHALL为当前商品详情页的绿标价格
- **AND** 真实黑标价格SHALL为当前商品详情页的黑标价格
- **AND** 系统SHALL采集前N个跟卖店铺信息

#### Scenario: 绿标价格大于跟卖价格
- **WHEN** 绿标价格 > 跟卖黑标价格
- **THEN** 系统SHALL点击黑标价格打开跟卖浮层
- **AND** 系统SHALL采集跟卖店铺列表
- **AND** 系统SHALL点击浮层中的绿标跳转到商品详情页
- **AND** 系统SHALL获取真实的绿标价格和黑标价格

### Requirement: 跟卖店铺信息采集
系统SHALL从跟卖浮层中采集店铺信息，包括店铺ID等关键数据。

#### Scenario: 跟卖浮层数据采集
- **WHEN** 点击黑标价格打开跟卖浮层
- **THEN** 系统SHALL采集前N个（默认10个）店铺信息
- **AND** 采集信息SHALL包括店铺ID
- **AND** 如果有"更多"标签，系统SHALL先点击展开

### Requirement: 佣金率计算规则
系统SHALL根据商品价格区间计算对应的佣金率。

#### Scenario: 低价商品佣金率
- **WHEN** 绿标价格 <= 1500卢布
- **THEN** 佣金率SHALL为12%

#### Scenario: 中价商品佣金率
- **WHEN** 1500卢布 < 绿标价格 <= 5000卢布
- **THEN** 佣金率SHALL选择页面上并列三个label中第二个label的数字

#### Scenario: 高价商品佣金率
- **WHEN** 绿标价格 > 5000卢布
- **THEN** 佣金率SHALL选择页面上并列三个label中第三个label的数字

#### Scenario: 佣金率获取失败处理
- **WHEN** ERP插件区域没有显示佣金率信息
- **THEN** 系统SHALL终止当前商品的计算处理
- **AND** 系统SHALL记录佣金率获取失败的原因
- **AND** 系统SHALL跳过该商品继续处理下一个商品

### Requirement: 商品重量和尺寸采集
系统SHALL从毛子ERP插件渲染区域采集商品的重量和尺寸信息。

#### Scenario: 重量信息采集和单位转换
- **WHEN** 访问商品详情页
- **THEN** 系统SHALL从ERP插件区域获取商品重量
- **AND** 系统SHALL自动将重量转换为克(g)单位
- **AND** 系统SHALL支持kg、磅等单位的自动转换
- **AND** 重量信息SHALL以克(g)为标准单位返回

#### Scenario: 尺寸信息采集
- **WHEN** 访问商品详情页
- **THEN** 系统SHALL从ERP插件区域获取商品尺寸
- **AND** 尺寸信息SHALL包含长宽高数据

### Requirement: 1688货源匹配Mock实现
系统SHALL实现1688相似商品搜索API的Mock功能，基于alibaba.cross.similar.offer.search接口规范。

#### Scenario: 1688 API Mock成功
- **WHEN** 调用1688相似商品搜索API Mock
- **THEN** 系统SHALL模拟alibaba.cross.similar.offer.search-1接口返回
- **AND** Mock数据SHALL包含商品价格、供应商信息等关键字段
- **AND** 系统SHALL从Mock结果中提取采购价格

#### Scenario: 1688 API Mock失败
- **WHEN** Mock 1688 API调用失败
- **THEN** 系统SHALL终止当前商品的处理
- **AND** 系统SHALL记录API调用失败的原因
- **AND** 系统SHALL跳过该商品继续处理下一个商品

### Requirement: 商品定价自动计算
系统SHALL根据商品价格情况和黑标价格区间自动计算商品的真实售价。

#### Scenario: 仅有黑标价格的定价
- **WHEN** 商品只有黑标价格（无绿标价格）
- **THEN** 真实售价SHALL等于黑标价格

#### Scenario: 低价商品定价（90元以内）
- **WHEN** 黑标价格 <= 90人民币
- **THEN** 真实售价SHALL等于黑标价格

#### Scenario: 中价商品定价（90-120元）
- **WHEN** 90人民币 < 黑标价格 <= 120人民币
- **THEN** 真实售价SHALL等于黑标价格 + 5元

#### Scenario: 高价商品定价（120元以上）
- **WHEN** 黑标价格 > 120人民币
- **THEN** 真实售价SHALL等于 (黑标价格 - 绿标价格) * 2.2 + 黑标价格
- **AND** 当绿标价格不存在时，绿标价格SHALL等于黑标价格进行计算

### Requirement: 跟卖定价策略
系统SHALL基于市场最低价的真实售价计算跟卖定价，建议采用95折策略。

#### Scenario: 跟卖定价计算
- **WHEN** 获取到我们计算的真实售价和跟卖价格列表
- **THEN** 系统SHALL从真实售价和跟卖价格中找到最低值作为市场最低价
- **AND** 跟卖定价SHALL为市场最低价 * 跟卖折扣参数（默认0.95）
- **AND** 跟卖折扣参数SHALL支持配置调整
- **AND** 系统SHALL验证定价的合理性

### Requirement: 利润计算集成
系统SHALL将采集的所有数据输入到利润计算器中进行利润评估。

#### Scenario: 利润计算数据输入
- **WHEN** 完成商品信息采集
- **THEN** 系统SHALL输入真实黑标价格、绿标价格、佣金率、商品重量、商品尺寸、定价、采购成本到利润计算器
- **AND** 所有输入数据SHALL经过格式验证

#### Scenario: 利润评估和店铺评分
- **WHEN** 利润计算完成
- **THEN** 系统SHALL计算利润率（利润率 = 利润 / 备货成本）
- **AND** 如果商品利润率 >= 利润率阈值（表单输入时指定），系统SHALL为当前店铺评分+1
- **AND** 系统SHALL将跟卖卖家列表输出到Excel（与好店excel格式保持一致）
- **AND** 如果利润率 < 阈值，系统SHALL跳过该商品

### Requirement: 店铺最终评估和状态更新
系统SHALL根据店铺评分进行最终评估并更新Excel状态。

#### Scenario: 好店标记
- **WHEN** 店铺遍历完毕且店铺评分 >= 好店评分阈值（可配置，默认2）
- **THEN** 系统SHALL将该店铺标记为好店
- **AND** 系统SHALL更新状态为"已处理"
- **AND** 系统SHALL在原Excel表格中新增列输出跟卖店铺信息

#### Scenario: 非好店处理
- **WHEN** 店铺遍历完毕且店铺评分 < 好店评分阈值
- **THEN** 系统SHALL标记第二列为"否"
- **AND** 系统SHALL更新状态为"已处理"

### Requirement: 商品数量和利润率判断逻辑
系统SHALL根据前x个商品的利润率表现判断店铺是否需要"裂变"。

#### Scenario: 商品数量限制
- **WHEN** 遍历店铺商品列表
- **THEN** 系统SHALL处理前x个产品（x为可配置参数）
- **AND** 系统SHALL记录每个商品的利润率计算结果

#### Scenario: 店铺裂变判断标准
- **WHEN** 完成前x个商品的利润率计算
- **THEN** 系统SHALL统计利润率大于y%的商品数量
- **AND** 如果有两个以上商品利润率 > y%，系统SHALL判定该店铺需要"裂变"
- **AND** y%为利润率阈值（表单输入时指定）

#### Scenario: 利润率计算公式
- **WHEN** 计算商品利润率
- **THEN** 利润率SHALL按公式计算：利润率 = 利润 / 备货成本
- **AND** 备货成本SHALL包含采购成本和相关运营成本
- **AND** 系统SHALL验证备货成本为正数

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
- **AND** 系统SHALL根据操作系统选择对应的浏览器驱动程序
- **AND** 系统SHALL支持Chrome、Firefox等主流浏览器的跨平台版本
- **AND** 驱动程序路径SHALL通过配置文件或自动检测获得

#### Scenario: 字符编码兼容性
- **WHEN** 读写Excel文件或处理文本数据
- **THEN** 系统SHALL使用UTF-8编码确保跨平台字符兼容性
- **AND** 系统SHALL正确处理中文、俄文等多语言字符
- **AND** 系统SHALL避免因编码差异导致的乱码问题

#### Scenario: 网络请求兼容性
- **WHEN** 发起HTTP请求或API调用
- **THEN** 系统SHALL使用跨平台的网络库
- **AND** 系统SHALL正确处理不同操作系统的SSL证书验证
- **AND** 系统SHALL支持代理配置的跨平台设置

#### Scenario: 进程和线程管理兼容性
- **WHEN** 创建子进程或管理并发任务
- **THEN** 系统SHALL使用跨平台的进程管理方法
- **AND** 系统SHALL避免使用平台特定的系统调用
- **AND** 系统SHALL确保信号处理在不同操作系统下的一致性

#### Scenario: 环境变量和配置兼容性
- **WHEN** 读取系统环境变量或配置信息
- **THEN** 系统SHALL提供跨平台的配置管理机制
- **AND** 系统SHALL支持不同操作系统的环境变量格式
- **AND** 配置文件SHALL使用标准格式（JSON、YAML等）
- **AND** 系统SHALL提供默认配置以确保开箱即用

### Requirement: 配置参数管理
系统SHALL支持关键业务参数的配置化管理，提高系统的灵活性。

#### Scenario: 利润率阈值配置
- **WHEN** 用户在表单中输入利润率阈值
- **THEN** 系统SHALL使用该阈值进行商品利润评估
- **AND** 系统SHALL验证阈值为有效百分比数值

#### Scenario: 好店评分阈值配置
- **WHEN** 系统需要判断好店标准
- **THEN** 系统SHALL使用可配置的好店评分阈值（默认2）
- **AND** 系统SHALL支持运行时调整该阈值

#### Scenario: 跟卖折扣参数配置
- **WHEN** 计算跟卖定价
- **THEN** 系统SHALL使用可配置的跟卖折扣参数（默认0.95）
- **AND** 系统SHALL支持按需调整折扣比例