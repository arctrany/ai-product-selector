# OZON Product Selector Tool

基于 Spring AI Alibaba 的智能选品工具，为 OZON 市场提供 AI 驱动的产品分析和推荐服务。

## 🚀 核心功能

### 🤖 AI 智能分析
- **智能产品评估**: 基于通义千问大模型进行产品潜力分析
- **市场趋势预测**: AI 驱动的市场趋势分析和预测
- **竞争强度评估**: 自动分析产品竞争环境
- **风险评估**: 智能识别产品投资风险
- **利润预估**: 基于多维度数据的利润预测

### 📊 数据采集与分析
- **OZON API 集成**: 实时获取产品数据、价格、销量等信息
- **价格监控**: 自动跟踪产品价格变化历史
- **销量分析**: 产品销售趋势和季节性分析
- **评价分析**: 用户评价数据的智能分析

### 🎯 选品推荐
- **智能推荐**: 基于 AI 分析的产品推荐排序
- **分类筛选**: 支持多维度产品筛选和搜索
- **相似产品**: 智能推荐相似产品和替代品
- **市场机会**: 识别市场空白和机会

### 📈 业务洞察
- **市场报告**: AI 生成的市场分析报告
- **趋势预测**: 基于历史数据的趋势预测
- **季节性分析**: 产品季节性特征分析
- **品类分析**: 不同品类的市场表现对比

## 🏗️ 技术架构

### 后端技术栈
- **Spring Boot 3.2**: 现代化 Java 应用框架
- **Spring AI Alibaba**: 阿里云通义千问 AI 集成
- **Spring Data JPA**: 数据持久化层
- **Spring Security**: 安全认证授权
- **Spring WebFlux**: 响应式编程支持
- **H2/MySQL**: 数据库支持

### AI 能力
- **通义千问**: 阿里云大语言模型
- **智能分析**: 自然语言处理和理解
- **数据挖掘**: 基于机器学习的数据分析
- **预测建模**: 趋势预测和风险评估

### 核心特性
- **响应式架构**: 高并发异步处理
- **缓存优化**: 智能缓存提升性能
- **弹性设计**: 重试机制和熔断保护
- **监控告警**: 全面的应用监控
- **API 文档**: Swagger/OpenAPI 3.0

## 🚀 快速开始

### 环境要求
- JDK 17+
- Maven 3.6+
- 通义千问 API Key

### 1. 克隆项目
```bash
git clone <repository-url>
cd ozon-product-selector
```

### 2. 配置环境变量
```bash
# 必需配置
export DASHSCOPE_API_KEY="your-dashscope-api-key"
export OZON_CLIENT_ID="your-ozon-client-id"
export OZON_API_KEY="your-ozon-api-key"

# 可选配置
export ADMIN_PASSWORD="admin123"
```

### 3. 编译运行
```bash
# 编译项目
mvn clean compile

# 运行应用
mvn spring-boot:run

# 或者打包后运行
mvn clean package
java -jar target/ozon-product-selector-1.0.0.jar
```

### 4. 访问应用
- 应用地址: http://localhost:8080/api
- API 文档: http://localhost:8080/api/swagger-ui.html
- H2 控制台: http://localhost:8080/api/h2-console
- 健康检查: http://localhost:8080/api/actuator/health

## 📖 API 使用指南

### 产品搜索 API
```bash
# 搜索产品
GET /api/products/search?query=智能手机&limit=20

# 获取趋势产品
GET /api/products/trending?limit=10

# 按分类获取产品
GET /api/products/category/123?limit=50
```

### AI 分析 API
```bash
# 分析单个产品
POST /api/analysis/product/123

# 批量分析产品
POST /api/analysis/batch
Content-Type: application/json
[1, 2, 3, 4, 5]

# 获取推荐产品
GET /api/analysis/recommendations?limit=10

# 生成市场分析报告
GET /api/analysis/market-summary
```

### 产品管理 API
```bash
# 从 OZON 同步产品
POST /api/products/123/sync

# 批量同步产品
POST /api/products/batch-sync
Content-Type: application/json
[123, 456, 789]

# 筛选产品
GET /api/products/local/filters?minPrice=100&maxPrice=1000&minRating=4.0
```

## 🔧 配置说明

### 应用配置 (application.yml)
```yaml
# OZON API 配置
ozon:
  api:
    base-url: https://api-seller.ozon.ru
    client-id: ${OZON_CLIENT_ID}
    api-key: ${OZON_API_KEY}
    rate-limit:
      requests-per-minute: 100

# AI 分析配置
product:
  analysis:
    batch-size: 50
    cache-duration: PT1H
    ai:
      prompt-template: |
        分析以下 OZON 产品数据并提供选品建议...

# Spring AI Alibaba 配置
spring:
  ai:
    alibaba:
      dashscope:
        chat:
          api-key: ${DASHSCOPE_API_KEY}
          model: qwen-plus
          options:
            temperature: 0.3
            max-tokens: 2000
```

### 数据库配置
```yaml
# 开发环境 (H2)
spring:
  datasource:
    url: jdbc:h2:mem:ozondb
    driver-class-name: org.h2.Driver
  jpa:
    hibernate:
      ddl-auto: create-drop

# 生产环境 (MySQL)
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/ozon_selector
    username: ${DB_USERNAME}
    password: ${DB_PASSWORD}
    driver-class-name: com.mysql.cj.jdbc.Driver
  jpa:
    hibernate:
      ddl-auto: validate
```

## 🎯 使用场景

### 1. 产品选品分析
```java
// 1. 搜索候选产品
OzonSearchRequest request = new OzonSearchRequest("智能手表", 50);
Flux<Product> products = ozonApiService.searchProducts(request);

// 2. AI 分析产品潜力
CompletableFuture<ProductAnalysis> analysis = 
    analysisService.analyzeProduct(product);

// 3. 获取推荐结果
List<ProductAnalysis> recommendations = 
    analysisService.getTopRecommendedProducts(10);
```

### 2. 市场趋势分析
```java
// 生成市场分析报告
CompletableFuture<String> marketSummary = 
    analysisService.generateMarketAnalysisSummary(productIds);

// 获取趋势分析
CompletableFuture<String> trends = 
    analysisService.getAnalysisTrends(30);
```

### 3. 批量产品处理
```java
// 批量同步产品数据
CompletableFuture<List<Product>> products = 
    ozonApiService.batchGetProductDetails(productIds);

// 批量 AI 分析
CompletableFuture<List<ProductAnalysis>> analyses = 
    analysisService.batchAnalyzeProducts(products);
```

## 🔒 安全配置

### 认证授权
- Basic Authentication (开发环境)
- 支持扩展 JWT、OAuth2 等认证方式
- 基于角色的访问控制

### API 安全
- 请求频率限制
- 参数验证和清理
- 错误信息脱敏

## 📊 监控运维

### 应用监控
- Spring Boot Actuator 健康检查
- Micrometer 指标收集
- 支持 Prometheus 集成

### 日志管理
- 结构化日志输出
- 不同级别日志配置
- 支持日志文件轮转

### 性能优化
- 数据库连接池优化
- Redis 缓存集成
- 异步处理优化

## 🚀 部署指南

### Docker 部署
```dockerfile
FROM openjdk:17-jdk-slim
COPY target/ozon-product-selector-1.0.0.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app.jar"]
```

### Kubernetes 部署
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ozon-product-selector
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ozon-product-selector
  template:
    metadata:
      labels:
        app: ozon-product-selector
    spec:
      containers:
      - name: app
        image: ozon-product-selector:1.0.0
        ports:
        - containerPort: 8080
        env:
        - name: DASHSCOPE_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-secrets
              key: dashscope-api-key
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 Apache 2.0 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📧 联系我们

- 项目地址: [GitHub Repository]
- 问题反馈: [GitHub Issues]
- 技术交流: [Discord/WeChat Group]

## 🎉 致谢

感谢以下开源项目的支持：
- [Spring AI Alibaba](https://github.com/alibaba/spring-ai-alibaba)
- [Spring Boot](https://spring.io/projects/spring-boot)
- [阿里云通义千问](https://tongyi.aliyun.com/)

---

**让 AI 赋能您的选品决策！** 🚀
