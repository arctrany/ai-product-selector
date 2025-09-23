# OZON选品工具数据源架构

## 📊 数据源概述

OZON选品工具采用多层次、多渠道的数据源架构，确保商品池的全面性和时效性。

## 🔄 数据流架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   外部数据源     │ -> │    数据采集层     │ -> │   商品池管理     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         v                       v                       v
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   OZON API      │    │   数据清洗过滤   │    │   AI分析引擎    │
│   第三方数据     │    │   去重合并       │    │   智能推荐      │
│   爬虫数据       │    │   质量检查       │    │   趋势分析      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🎯 主要数据源

### 1. OZON官方API
```yaml
数据源: OZON Seller API
频率: 实时/按需
覆盖范围: 全平台商品
数据类型:
  - 商品基础信息
  - 价格变动历史
  - 销量数据
  - 库存状态
  - 评价统计
  - 卖家信息
```

**API端点说明:**
- `/v2/product/list` - 商品搜索和列表
- `/v2/product/info` - 商品详细信息
- `/v2/category/tree` - 分类树结构
- `/v3/product/info/stocks` - 库存信息

### 2. 热门产品数据源
```java
// 热门产品收集
public Flux<Product> getTrendingProducts(int limit) {
    OzonSearchRequest request = new OzonSearchRequest();
    request.setSort("popularity");  // 按热度排序
    request.setLimit(limit);
    return searchProducts(request);
}
```

**特点:**
- 基于销量和浏览量排序
- 实时热度数据
- 涵盖多个品类
- 自动过滤低质量商品

### 3. 分类商品数据源
```java
// 目标分类配置
product.pool.categories:
  - 15621  # 电子产品
  - 17029  # 家居用品  
  - 6500   # 运动户外
  - 7500   # 服装鞋帽
  - 5000   # 母婴用品
  - 12345  # 美容护肤
  - 8000   # 汽车用品
  - 9000   # 图书音像
```

**收集策略:**
- 每个分类收集前50个高质量商品
- 定期更新分类排行
- 基于评分和评论数过滤
- 排除停售和缺货商品

### 4. 关键词搜索数据源
```java
// 热门关键词列表
private final List<String> TRENDING_KEYWORDS = Arrays.asList(
    "智能手机", "笔记本电脑", "健身器材", "家居用品",
    "母婴用品", "美容护肤", "运动装备", "数码配件",
    "厨房用具", "办公用品", "游戏设备", "汽车配件"
);
```

**搜索策略:**
- 基于市场热度的关键词库
- 动态调整搜索词权重
- 新品优先策略
- 多维度筛选条件

### 5. 竞品分析数据源
```java
// 竞品发现算法
private CompletableFuture<Void> findSimilarProducts(Product referenceProduct) {
    // 基于分类和价格范围搜索
    OzonSearchRequest request = new OzonSearchRequest();
    request.setCategoryId(referenceProduct.getCategoryId());
    
    // 价格范围: 参考产品的50%-150%
    BigDecimal minPrice = referenceProduct.getPrice().multiply(0.5);
    BigDecimal maxPrice = referenceProduct.getPrice().multiply(1.5);
    request.setPriceRange(new PriceRange(minPrice, maxPrice));
    
    return searchProducts(request);
}
```

**分析维度:**
- 同类商品对比
- 价格区间分析  
- 功能特性对比
- 品牌竞争态势

## 🏊‍♂️ 商品池管理

### 商品池构成
```
商品池 (Product Pool)
├── 热门商品池 (30%)
│   ├── 全站热销
│   ├── 分类热销  
│   └── 新品热销
├── 分类商品池 (40%)
│   ├── 目标分类覆盖
│   ├── 长尾分类挖掘
│   └── 细分市场发现
├── 关键词商品池 (20%)
│   ├── 搜索热词
│   ├── 季节性词汇
│   └── 趋势词汇
└── 竞品分析池 (10%)
    ├── 对标产品
    ├── 替代产品
    └── 互补产品
```

### 数据质量标准
```yaml
商品入池标准:
  基础要求:
    - 产品信息完整 (名称、价格、图片)
    - 在售状态 (有库存)
    - 基础评分 >= 3.5
    - 评论数 >= 10
  
  价格范围:
    - 最低价格: 10 RUB
    - 最高价格: 1,000,000 RUB
    - 价格合理性检查
  
  排除条件:
    - 重复商品 (相同OZON ID)
    - 违禁商品
    - 信息不全商品
    - 长期缺货商品
```

### 更新策略
```java
// 定时更新任务
@Scheduled(cron = "0 0 2 * * *")  // 每天凌晨2点
public void scheduledRefreshProductPool() {
    // 1. 清理过期产品
    cleanupExpiredProducts();
    
    // 2. 更新现有产品数据  
    updateExistingProducts();
    
    // 3. 补充新产品
    supplementNewProducts();
}
```

**更新频率:**
- 商品基础信息: 24小时
- 价格库存信息: 6小时  
- 热门排行数据: 2小时
- 分析结果缓存: 1小时

## 🤖 AI分析集成

### 分析触发机制
```java
// 新商品入池自动触发AI分析
private void triggerAsyncAnalysis(List<Product> products) {
    // 分批处理，避免API过载
    for (int i = 0; i < products.size(); i += 10) {
        List<Product> batch = products.subList(i, Math.min(i + 10, products.size()));
        
        analysisService.batchAnalyzeProducts(batch)
                .thenAccept(analyses -> {
                    logger.info("完成 {} 个产品的AI分析", analyses.size());
                });
        
        // API频率控制
        Thread.sleep(1000);
    }
}
```

### 分析数据流
```
商品数据 -> AI提示词构建 -> 通义千问API -> 结构化解析 -> 评分存储
    │              │                │              │           │
    │              │                │              │           └── 推荐排序
    │              │                │              └── 风险评估
    │              │                └── 市场分析
    │              └── 多维度评估
    └── 基础数据准备
```

## 📈 数据监控

### 关键指标
```yaml
商品池监控:
  数量指标:
    - 总商品数
    - 日新增商品数
    - 有效商品比例
    - 分类覆盖度
  
  质量指标:
    - 平均评分
    - 平均评论数
    - AI分析覆盖率
    - 数据完整度
  
  性能指标:
    - API调用成功率
    - 数据更新延迟
    - 分析处理速度
    - 缓存命中率
```

### 监控接口
```bash
# 获取商品池统计
GET /api/product-pool/statistics

# 检查服务健康状态
GET /api/product-pool/health

# 手动刷新商品池
POST /api/product-pool/refresh
```

## 🔧 配置管理

### 环境变量配置
```bash
# OZON API配置
OZON_CLIENT_ID=your-client-id
OZON_API_KEY=your-api-key

# AI分析配置  
DASHSCOPE_API_KEY=your-dashscope-key

# 数据库配置
DB_HOST=localhost
DB_NAME=ozon_selector
DB_USERNAME=admin
DB_PASSWORD=password
```

### 应用配置
```yaml
# application.yml
product:
  pool:
    batch-size: 100          # 批处理大小
    categories: [...]        # 目标分类列表
    min-rating: 3.5         # 最低评分要求
    min-reviews: 10         # 最低评论数
    refresh-interval: PT24H  # 刷新间隔
```

## 🚀 扩展能力

### 未来数据源
1. **社交媒体数据**: 微博、抖音等平台的产品讨论
2. **搜索引擎数据**: Google Trends、百度指数等趋势数据
3. **电商平台数据**: 淘宝、京东等竞品平台数据
4. **供应链数据**: 1688等B2B平台的供应商信息
5. **用户行为数据**: 站内搜索、浏览、收藏等行为数据

### 技术优化
1. **实时数据流**: 基于Kafka的实时数据处理
2. **分布式爬虫**: 多节点并行数据采集
3. **智能去重**: 基于机器学习的商品去重算法
4. **动态调度**: 基于负载的智能任务调度

---

通过这个完整的数据源架构，OZON选品工具能够：
- ✅ 全面覆盖OZON平台商品
- ✅ 实时跟踪市场变化
- ✅ 智能筛选优质商品
- ✅ 提供AI驱动的选品建议
- ✅ 支持大规模数据处理
- ✅ 保证数据质量和时效性

