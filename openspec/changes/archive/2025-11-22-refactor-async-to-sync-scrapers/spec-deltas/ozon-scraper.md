# Spec Delta: ozon-scraper

## 变更类型
MODIFICATION - 确保OZON scraper完全同步化，消除异步调用警告

## 变更内容

### 修改 Requirement: 同步化OZON商品抓取流程
确保OZON Scraper使用完全同步的抓取流程。

#### Scenario: 同步商品信息抓取
- **WHEN** 抓取OZON商品信息时
- **THEN** 使用同步的页面操作方法
- **AND** 所有DOM查询都是同步执行
- **AND** 无RuntimeWarning警告

#### Scenario: 同步跟卖店铺交互
- **WHEN** 需要统计跟卖数量或展开跟卖列表时
- **THEN** 使用同步的元素计数和点击操作
- **AND** 移除未await的Locator.count()调用
- **AND** 使用query_selector_all()和len()计算数量

### 新增 Requirement: BeautifulSoup API更新
确保使用最新的BeautifulSoup API。

#### Scenario: HTML内容搜索
- **WHEN** 搜索包含特定文本的HTML元素时
- **THEN** 使用string参数而非废弃的text参数
- **AND** 调用find_all(string=pattern)而非find_all(text=pattern)

## 技术实现说明

**确保的功能**：
- 所有抓取方法都是同步方法
- 使用同步的元素查找和计数
- 使用最新的BeautifulSoup API

**保持不变**：
- 商品信息提取逻辑
- 跟卖店铺处理逻辑
- 数据验证和过滤规则

