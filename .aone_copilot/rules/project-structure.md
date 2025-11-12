# 智能选品系统项目结构

智能选品系统是一个用于从电商平台抓取店铺和商品信息，进行利润计算和好店筛选的自动化系统。

## 主要目录结构

- `cli/`: 命令行接口实现
  - 负责任务的启动、暂停、恢复、停止等操作
  - 管理UI状态和配置

- `common/`: 核心业务逻辑
  - `business/`: 业务逻辑处理
    - `pricing_calculator.py`: 定价计算
    - `profit_evaluator.py`: 利润评估
    - `store_evaluator.py`: 店铺评估
    - `source_matcher.py`: 货源匹配
  - `config/`: 配置管理
    - `config.py`: 主配置文件
    - `ozon_selectors.py`: OZON选择器配置
    - `seerfar_selectors.py`: Seerfar选择器配置
  - `scrapers/`: 数据抓取器
    - `ozon_scraper.py`: OZON平台数据抓取
    - `seerfar_scraper.py`: Seerfar平台数据抓取
    - `competitor_scraper.py`: 跟卖店铺抓取
    - `erp_plugin_scraper.py`: ERP插件数据抓取
    - `xuanping_browser_service.py`: 浏览器服务封装
  - `good_store_selector.py`: 好店筛选主流程

- `rpa/`: 浏览器自动化框架
  - `browser/`: 浏览器服务核心实现
    - `browser_service.py`: 精简版浏览器服务
    - `core/`: 核心组件
      - `config/`: 配置管理
      - `exceptions/`: 异常处理
      - `interfaces/`: 接口定义
      - `implementations/`: 具体实现

- `docs/`: 文档
  - `req/`: 需求文档
  - `sol/`: 解决方案文档
  - `specs/`: 技术规范文档

- `tests/`: 测试文件
  - 各种平台的测试用例

## 关键文件

- `xp_cli.py`: 命令行控制工具
- `common/good_store_selector.py`: 好店筛选主流程
- `common/config.py`: 系统配置管理
- `rpa/browser/browser_service.py`: 浏览器服务核心
- `common/scrapers/ozon_scraper.py`: OZON数据抓取器
- `common/scrapers/seerfar_scraper.py`: Seerfar数据抓取器

## 构建和运行

```bash
# 启动任务
python xp_cli.py start --config config.json

# 暂停任务
python xp_cli.py pause

# 恢复任务
python xp_cli.py resume

# 停止任务
python xp_cli.py stop

# 查看状态
python xp_cli.py status
```