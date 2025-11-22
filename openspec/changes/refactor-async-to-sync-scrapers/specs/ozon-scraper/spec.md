## MODIFIED Requirements

### Requirement: 同步化OZON商品抓取流程
OZON Scraper SHALL使用完全同步的抓取流程，消除所有异步调用警告。

#### Scenario: 商品信息抓取
- **WHEN** 抓取OZON商品信息
- **THEN** 使用同步的页面操作方法
- **AND** 所有DOM查询都是同步执行，无RuntimeWarning

#### Scenario: 跟卖店铺交互  
- **WHEN** 需要统计跟卖数量或展开跟卖列表
- **THEN** 使用同步的元素计数和点击操作
- **AND** 移除未await的Locator.count()调用

#### Scenario: 错误处理
- **WHEN** 抓取过程中出现错误
- **THEN** 使用同步的异常处理机制
- **AND** 不依赖异步的错误恢复流程

### Requirement: BeautifulSoup API更新
ERP Plugin Scraper SHALL使用最新的BeautifulSoup API，移除废弃警告。

#### Scenario: HTML内容搜索
- **WHEN** 搜索包含特定文本的HTML元素
- **THEN** 使用string参数而非废弃的text参数
- **AND** 调用find_all(string=pattern)而非find_all(text=pattern)

## ADDED Requirements

### Requirement: 同步元素计数方法
Scraper SHALL提供同步的元素计数方法，替代异步的Locator.count()。

#### Scenario: 跟卖数量统计
- **WHEN** 需要统计页面中的跟卖店铺数量
- **THEN** 使用query_selector_all()获取元素列表
- **AND** 通过len()计算数量，避免异步count()调用
