## Context

选品（xuanping）应用需要实现两个核心业务流程：店铺裂变和智能选品。这两个流程都需要大量的浏览器自动化操作，同时要与现有的 Excel 利润计算器集成。

**背景约束**:
- 必须基于现有的 workflow_engine 架构
- 需要利用 src_new/rpa/browser 的 Playwright 浏览器自动化能力
- 要集成已有的 apps/xuanping/common/excel_calculator.py 利润计算功能
- 遵循项目的跨平台兼容性和异步性能原则

**利益相关者**:
- 业务用户：需要自动化的店铺发现和商品选择能力
- 开发团队：需要可维护和可扩展的架构设计
- 运维团队：需要稳定可靠的 RPA 执行环境

## Goals / Non-Goals

**Goals**:
- 实现完整的店铺裂变工作流，支持自动化店铺发现、数据采集和分析
- 实现智能选品工作流，结合利润计算和 RPA 的商品筛选能力
- 扩展 workflow_engine 支持 RPA 节点类型，实现浏览器操作的工作流化
- 建立工作流间的数据传递机制，支持复杂业务场景
- 提供专用的 Web 控制台界面，优化用户体验

**Non-Goals**:
- 不重新实现浏览器自动化基础设施（复用现有 RPA 组件）
- 不修改 workflow_engine 的核心架构（通过扩展实现）
- 不替换现有的利润计算器（集成使用）

## Decisions

### 决策1: RPA 节点架构设计
**决策**: 创建专门的 RPA 节点类型，继承自现有的 workflow_engine 节点基类，封装浏览器操作。

**理由**: 
- 保持与现有工作流架构的一致性
- 支持工作流的暂停、恢复、错误处理等标准功能
- 便于调试和监控 RPA 操作

**替代方案考虑**:
- 直接在 Python 节点中调用 RPA 功能：缺乏标准化，难以管理
- 创建独立的 RPA 服务：增加系统复杂度，通信开销大

### 决策2: 工作流数据传递机制
**决策**: 使用 workflow_engine 的状态管理机制，通过共享状态在工作流间传递数据。

**理由**:
- 利用现有的 LangGraph 状态管理能力
- 支持数据持久化和恢复
- 便于实现复杂的数据依赖关系

### 决策3: 错误处理策略
**决策**: 实现分层错误处理：RPA 节点级别的重试 + 工作流级别的异常处理 + 应用级别的降级策略。

**理由**:
- RPA 操作容易受网络、页面加载等因素影响
- 需要针对不同类型的错误采用不同的处理策略
- 保证系统的鲁棒性和用户体验

### 决策4: 利润计算器集成方式
**决策**: 将现有的 ExcelProfitCalculator 封装为工作流节点，支持批量计算和结果缓存。

**理由**:
- 复用现有的成熟功能
- 保持计算逻辑的一致性
- 支持高性能的批量处理

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Xuanping Application                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │  Shop Discovery │    │    Product Selection Flow      │ │
│  │     Flow        │────▶│                                │ │
│  │                 │    │  ┌─────────────────────────────┐ │ │
│  │  ┌─────────────┐│    │  │      RPA Nodes             │ │ │
│  │  │ RPA Nodes   ││    │  │  - Page Navigation         │ │ │
│  │  │ - Search    ││    │  │  - Data Extraction         │ │ │
│  │  │ - Extract   ││    │  │  - Form Interaction        │ │ │
│  │  │ - Navigate  ││    │  └─────────────────────────────┘ │ │
│  │  └─────────────┘│    │                                │ │
│  └─────────────────┘    │  ┌─────────────────────────────┐ │ │
│                         │  │   Profit Calculator Node   │ │ │
│                         │  │  - Excel Integration       │ │ │
│                         │  │  - Batch Processing        │ │ │
│                         │  └─────────────────────────────┘ │ │
│                         └─────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                  Workflow Engine Extensions                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                  RPA Node Types                         │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │ │
│  │  │   Browser   │ │   Page      │ │   Data          │   │ │
│  │  │   Control   │ │   Action    │ │   Extraction    │   │ │
│  │  │   Node      │ │   Node      │ │   Node          │   │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘   │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Core Infrastructure                      │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐  │
│  │  Workflow       │ │   RPA Browser   │ │    Excel      │  │
│  │  Engine         │ │   Service       │ │  Calculator   │  │
│  │  (LangGraph)    │ │  (Playwright)   │ │  (OpenPyXL)   │  │
│  └─────────────────┘ └─────────────────┘ └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. RPA Node Types

#### BrowserControlNode
- **职责**: 管理浏览器实例的生命周期
- **功能**: 启动/关闭浏览器、页面管理、会话保持
- **接口**: 
  ```python
  class BrowserControlNode(BaseNode):
      async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
          # 浏览器控制逻辑
  ```

#### PageActionNode
- **职责**: 执行页面交互操作
- **功能**: 点击、输入、导航、等待元素
- **配置**: 支持选择器、超时、重试策略

#### DataExtractionNode
- **职责**: 从页面提取结构化数据
- **功能**: 元素定位、文本提取、数据清洗、格式转换
- **输出**: 标准化的数据结构

### 2. Workflow Definitions

#### 店铺裂变流程 (Shop Discovery Flow)
```python
def create_shop_discovery_workflow():
    builder = WorkflowBuilder("shop_discovery")
    
    # 1. 初始化浏览器
    builder.add_node("init_browser", BrowserControlNode({
        "action": "start",
        "headless": False,
        "viewport": {"width": 1920, "height": 1080}
    }))
    
    # 2. 搜索目标店铺
    builder.add_node("search_shops", PageActionNode({
        "url": "https://target-platform.com/search",
        "actions": [
            {"type": "input", "selector": "#search", "value": "{search_keyword}"},
            {"type": "click", "selector": "#search-btn"},
            {"type": "wait", "selector": ".shop-list"}
        ]
    }))
    
    # 3. 提取店铺信息
    builder.add_node("extract_shops", DataExtractionNode({
        "selectors": {
            "shop_name": ".shop-item .name",
            "shop_url": ".shop-item .link",
            "shop_rating": ".shop-item .rating",
            "product_count": ".shop-item .product-count"
        },
        "pagination": True
    }))
    
    # 4. 分析店铺数据
    builder.add_node("analyze_shops", PythonNode({
        "function": "analyze_shop_data",
        "module": "xuanping.shop_selector.analyzer"
    }))
    
    # 构建流程
    builder.add_edge("init_browser", "search_shops")
    builder.add_edge("search_shops", "extract_shops")
    builder.add_edge("extract_shops", "analyze_shops")
    
    return builder.build()
```

#### 智能选品流程 (Product Selection Flow)
```python
def create_product_selection_workflow():
    builder = WorkflowBuilder("product_selection")
    
    # 1. 获取店铺列表（来自店铺裂变流程）
    builder.add_node("load_shops", PythonNode({
        "function": "load_shop_data",
        "source": "shop_discovery_result"
    }))
    
    # 2. 遍历店铺商品
    builder.add_node("browse_products", PageActionNode({
        "action": "iterate_shops",
        "extract_products": True
    }))
    
    # 3. 提取商品信息
    builder.add_node("extract_products", DataExtractionNode({
        "selectors": {
            "product_name": ".product .title",
            "price": ".product .price",
            "image_url": ".product .image",
            "description": ".product .desc"
        }
    }))
    
    # 4. 利润计算
    builder.add_node("calculate_profit", ProfitCalculatorNode({
        "excel_path": "config/profit_calculator.xlsx",
        "batch_size": 100
    }))
    
    # 5. 商品筛选
    builder.add_node("filter_products", PythonNode({
        "function": "filter_profitable_products",
        "criteria": {
            "min_profit_rate": 0.15,
            "min_profit_amount": 10.0
        }
    }))
    
    # 构建流程
    builder.add_edge("load_shops", "browse_products")
    builder.add_edge("browse_products", "extract_products")
    builder.add_edge("extract_products", "calculate_profit")
    builder.add_edge("calculate_profit", "filter_products")
    
    return builder.build()
```

### 3. Data Models

```python
@dataclass
class ShopInfo:
    shop_id: str
    name: str
    url: str
    rating: float
    product_count: int
    category: str
    extracted_at: datetime

@dataclass
class ProductInfo:
    product_id: str
    shop_id: str
    name: str
    price: float
    image_url: str
    description: str
    profit_calculation: Optional[ProfitCalculatorResult] = None
    
@dataclass
class WorkflowState:
    current_step: str
    shops: List[ShopInfo]
    products: List[ProductInfo]
    selected_products: List[ProductInfo]
    browser_session: Optional[Dict[str, Any]] = None
    error_count: int = 0
```

## Risks / Trade-offs

### 风险1: RPA 操作的不稳定性
**风险**: 网页结构变化、网络延迟、反爬虫机制可能导致 RPA 操作失败
**缓解措施**: 
- 实现多层重试机制
- 使用多种元素定位策略
- 添加智能等待和错误恢复

### 风险2: 性能和资源消耗
**风险**: 浏览器实例和大量数据处理可能消耗大量系统资源
**缓解措施**:
- 实现浏览器实例池管理
- 使用批量处理和数据分页
- 添加资源监控和限流

### 风险3: 数据一致性
**风险**: 工作流间的数据传递可能出现不一致
**缓解措施**:
- 使用事务性状态更新
- 实现数据校验和修复机制
- 添加详细的审计日志

## Migration Plan

### 阶段1: 基础设施准备 (1-2周)
1. 扩展 workflow_engine 支持 RPA 节点类型
2. 实现 RPA 节点的基础类和接口
3. 集成现有的浏览器服务和利润计算器

### 阶段2: 核心流程实现 (2-3周)
1. 实现店铺裂变工作流
2. 实现智能选品工作流
3. 建立工作流间的数据传递机制

### 阶段3: 用户界面和优化 (1-2周)
1. 创建 xuanping 专用的 Web 控制台
2. 实现错误处理和监控
3. 性能优化和测试

### 回滚计划
- 保持现有 apps/xuanping 结构不变
- 新功能通过配置开关控制
- 出现问题时可快速禁用新功能

## Open Questions

1. **数据存储策略**: 大量的店铺和商品数据应该如何存储和管理？是否需要引入专门的数据库？

2. **并发控制**: 多个工作流实例同时运行时，如何避免浏览器资源冲突？

3. **监控和告警**: 需要什么级别的监控和告警机制来保证 RPA 操作的可靠性？

4. **扩展性考虑**: 未来如果需要支持更多电商平台，架构如何扩展？

5. **合规性问题**: RPA 操作是否需要考虑目标网站的使用条款和反爬虫策略？