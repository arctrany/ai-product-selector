# 智能选品系统主要功能模块

智能选品系统是一个用于从电商平台抓取店铺和商品信息，进行利润计算和好店筛选的自动化系统。

## 核心功能

### 1. 数据抓取

系统支持从多个电商平台抓取数据：

#### OZON平台抓取
- 商品价格信息抓取（绿标价格、黑标价格）
- 跟卖店铺信息抓取
- 商品详情页数据提取

相关代码目录:
- `common/scrapers/ozon_scraper.py`: OZON平台数据抓取器
- `common/scrapers/competitor_scraper.py`: 跟卖店铺抓取器

主要特点:
- 基于browser_service架构实现
- 支持价格信息提取
- 支持跟卖店铺检测和信息提取

#### Seerfar平台抓取
- 店铺销售数据抓取（30天销售额、销量、日均销量）
- 店铺商品列表抓取
- 商品详情信息提取

相关代码目录:
- `common/scrapers/seerfar_scraper.py`: Seerfar平台数据抓取器

主要特点:
- 支持店铺销售数据提取
- 支持商品列表抓取
- 支持OZON商品详情页跳转处理

#### ERP插件数据抓取
- 商品佣金率抓取
- 商品重量、尺寸信息抓取

相关代码目录:
- `common/scrapers/erp_plugin_scraper.py`: ERP插件数据抓取器

### 2. 利润计算

系统支持基于抓取数据进行利润计算：

#### 定价计算
- 真实售价计算（根据规格要求的价格计算规则）
- 商品定价计算（95折）
- 汇率转换（卢布转人民币）

相关代码目录:
- `common/business/pricing_calculator.py`: 定价计算器

#### 利润评估
- 基于Excel利润计算器的精确利润计算
- 商品利润评估
- 批量利润评估

相关代码目录:
- `common/business/profit_evaluator.py`: 利润评估器

### 3. 好店筛选

系统支持根据配置条件筛选好店：

#### 店铺评估
- 店铺初筛条件验证（销售额、销量）
- 商品利润评估
- 好店判定

相关代码目录:
- `common/business/store_evaluator.py`: 店铺评估器
- `common/good_store_selector.py`: 好店筛选主流程

#### 跟卖店铺收集
- 有利润商品的跟卖店铺信息收集
- 跟卖价格提取

### 4. 任务管理

系统支持命令行方式控制任务的启动、暂停、取消、恢复：

#### CLI控制
- 任务启动、暂停、恢复、停止
- 状态查看、进度查看、日志查看
- 配置管理

相关代码目录:
- `cli/`: 命令行接口实现
- `xp_cli.py`: 命令行控制工具

## 配置与服务

- `common/config.py`: 系统配置管理，包括店铺筛选、价格计算、网页抓取、Excel处理、日志、性能等配置
- `rpa/browser/browser_service.py`: 浏览器服务核心，提供精简版浏览器服务
- `common/scrapers/xuanping_browser_service.py`: 项目特定的浏览器服务封装
- `common/task_control.py`: 任务执行控制，支持任务的暂停、恢复、停止

## 数据模型

- `common/models.py`: 系统核心数据结构定义，包括店铺、商品、价格等信息
- 使用dataclass确保类型安全和数据验证
- 定义了完整的数据模型层次结构