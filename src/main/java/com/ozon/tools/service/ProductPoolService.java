package com.ozon.tools.service;

import com.ozon.tools.domain.entity.Product;
import com.ozon.tools.dto.ozon.OzonSearchRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * 商品池管理服务 - 负责构建和维护候选商品数据池
 * 
 * @author AI Assistant
 */
@Service
@Transactional
public class ProductPoolService {

    private static final Logger logger = LoggerFactory.getLogger(ProductPoolService.class);

    private final OzonApiService ozonApiService;
    private final ProductService productService;
    private final ProductAnalysisService analysisService;

    @Value("${product.pool.batch-size:100}")
    private int batchSize;

    @Value("${product.pool.categories}")
    private List<Long> targetCategories;

    @Value("${product.pool.min-rating:3.0}")
    private BigDecimal minRating;

    @Value("${product.pool.min-reviews:10}")
    private Integer minReviews;

    public ProductPoolService(OzonApiService ozonApiService,
                            ProductService productService,
                            ProductAnalysisService analysisService) {
        this.ozonApiService = ozonApiService;
        this.productService = productService;
        this.analysisService = analysisService;
    }

    /**
     * 初始化商品池 - 从多个数据源收集候选商品
     */
    @Async
    public CompletableFuture<Void> initializeProductPool() {
        logger.info("开始初始化商品池");

        try {
            // 1. 从热门产品获取
            collectTrendingProducts().join();
            
            // 2. 从目标分类获取
            collectCategoryProducts().join();
            
            // 3. 从竞品分析获取
            collectCompetitorProducts().join();
            
            // 4. 从关键词搜索获取
            collectKeywordProducts().join();
            
            logger.info("商品池初始化完成");
            
        } catch (Exception e) {
            logger.error("商品池初始化失败: {}", e.getMessage(), e);
            throw new RuntimeException("商品池初始化失败", e);
        }

        return CompletableFuture.completedFuture(null);
    }

    /**
     * 收集热门产品到商品池
     */
    private CompletableFuture<Void> collectTrendingProducts() {
        logger.info("收集热门产品");

        return ozonApiService.getTrendingProducts(batchSize)
                .filter(this::isQualifiedProduct)
                .collectList()
                .flatMap(products -> {
                    logger.info("找到 {} 个符合条件的热门产品", products.size());
                    return saveProductsToPool(products, "trending");
                })
                .toFuture()
                .thenApply(v -> null);
    }

    /**
     * 按分类收集产品
     */
    private CompletableFuture<Void> collectCategoryProducts() {
        logger.info("按分类收集产品，目标分类: {}", targetCategories);

        List<CompletableFuture<Void>> futures = targetCategories.stream()
                .map(this::collectProductsFromCategory)
                .toList();

        return CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]));
    }

    /**
     * 从指定分类收集产品
     */
    private CompletableFuture<Void> collectProductsFromCategory(Long categoryId) {
        logger.info("收集分类 {} 的产品", categoryId);

        return ozonApiService.getProductsByCategory(categoryId, batchSize)
                .filter(this::isQualifiedProduct)
                .collectList()
                .flatMap(products -> {
                    logger.info("从分类 {} 找到 {} 个符合条件的产品", categoryId, products.size());
                    return saveProductsToPool(products, "category-" + categoryId);
                })
                .toFuture()
                .thenApply(v -> null);
    }

    /**
     * 竞品分析 - 查找类似产品
     */
    private CompletableFuture<Void> collectCompetitorProducts() {
        logger.info("进行竞品分析收集");

        // 获取已有的高评分产品作为参考
        List<Product> referenceProducts = productService.getTopRatedProducts(
                org.springframework.data.domain.PageRequest.of(0, 10)
        ).getContent();

        List<CompletableFuture<Void>> futures = referenceProducts.stream()
                .map(this::findSimilarProducts)
                .toList();

        return CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]));
    }

    /**
     * 查找相似产品
     */
    private CompletableFuture<Void> findSimilarProducts(Product referenceProduct) {
        logger.info("查找与 {} 相似的产品", referenceProduct.getName());

        // 基于分类和价格范围搜索相似产品
        OzonSearchRequest request = new OzonSearchRequest();
        request.setCategoryId(referenceProduct.getCategoryId());
        request.setLimit(50);
        
        // 设置价格范围 (参考产品价格的 50%-150%)
        if (referenceProduct.getPrice() != null) {
            BigDecimal minPrice = referenceProduct.getPrice().multiply(BigDecimal.valueOf(0.5));
            BigDecimal maxPrice = referenceProduct.getPrice().multiply(BigDecimal.valueOf(1.5));
            
            OzonSearchRequest.PriceRange priceRange = new OzonSearchRequest.PriceRange(
                    minPrice.doubleValue(), maxPrice.doubleValue());
            request.setPriceRange(priceRange);
        }

        return ozonApiService.searchProducts(request)
                .filter(this::isQualifiedProduct)
                .filter(product -> !product.getOzonId().equals(referenceProduct.getOzonId()))
                .collectList()
                .flatMap(products -> saveProductsToPool(products, "similar"))
                .toFuture()
                .thenApply(v -> null);
    }

    /**
     * 关键词搜索收集产品
     */
    private CompletableFuture<Void> collectKeywordProducts() {
        logger.info("基于关键词搜索收集产品");

        // 定义热门关键词
        List<String> keywords = Arrays.asList(
                "智能手机", "笔记本电脑", "健身器材", "家居用品", "母婴用品",
                "美容护肤", "运动装备", "数码配件", "厨房用具", "办公用品",
                "游戏设备", "汽车配件", "宠物用品", "图书文具", "服装鞋帽"
        );

        List<CompletableFuture<Void>> futures = keywords.stream()
                .map(this::searchProductsByKeyword)
                .toList();

        return CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]));
    }

    /**
     * 按关键词搜索产品
     */
    private CompletableFuture<Void> searchProductsByKeyword(String keyword) {
        logger.info("搜索关键词: {}", keyword);

        OzonSearchRequest request = new OzonSearchRequest(keyword, 30);
        request.setMinRating(minRating.doubleValue());
        request.setMinReviewsCount(minReviews);
        request.setInStock(true);

        return ozonApiService.searchProducts(request)
                .filter(this::isQualifiedProduct)
                .collectList()
                .flatMap(products -> {
                    logger.info("关键词 '{}' 找到 {} 个符合条件的产品", keyword, products.size());
                    return saveProductsToPool(products, "keyword-" + keyword);
                })
                .toFuture()
                .thenApply(v -> null);
    }

    /**
     * 判断产品是否符合入池条件
     */
    private boolean isQualifiedProduct(Product product) {
        // 基础数据完整性检查
        if (product.getName() == null || product.getPrice() == null) {
            return false;
        }

        // 评分要求
        if (product.getRating() != null && product.getRating().compareTo(minRating) < 0) {
            return false;
        }

        // 评论数要求
        if (product.getReviewsCount() != null && product.getReviewsCount() < minReviews) {
            return false;
        }

        // 价格合理性检查
        if (product.getPrice().compareTo(BigDecimal.valueOf(10)) < 0 || 
            product.getPrice().compareTo(BigDecimal.valueOf(1000000)) > 0) {
            return false;
        }

        // 避免重复产品
        return !productService.existsByOzonId(product.getOzonId());
    }

    /**
     * 将产品保存到商品池
     */
    private reactor.core.publisher.Mono<Void> saveProductsToPool(List<Product> products, String source) {
        return reactor.core.publisher.Mono.fromCallable(() -> {
            logger.info("保存 {} 个产品到商品池，来源: {}", products.size(), source);
            
            // 保存产品基础信息
            List<Product> savedProducts = productService.saveAllProducts(products);
            
            // 异步触发AI分析
            triggerAsyncAnalysis(savedProducts);
            
            return null;
        });
    }

    /**
     * 异步触发产品AI分析
     */
    @Async
    private void triggerAsyncAnalysis(List<Product> products) {
        logger.info("触发 {} 个产品的异步AI分析", products.size());
        
        // 分批处理，避免过载
        for (int i = 0; i < products.size(); i += 10) {
            int endIndex = Math.min(i + 10, products.size());
            List<Product> batch = products.subList(i, endIndex);
            
            analysisService.batchAnalyzeProducts(batch)
                    .thenAccept(analyses -> {
                        logger.info("完成 {} 个产品的AI分析", analyses.size());
                    })
                    .exceptionally(ex -> {
                        logger.error("批量AI分析失败: {}", ex.getMessage());
                        return null;
                    });
            
            // 避免API频率限制
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }

    /**
     * 定时刷新商品池 - 每天凌晨2点执行
     */
    @Scheduled(cron = "0 0 2 * * *")
    public void scheduledRefreshProductPool() {
        logger.info("开始定时刷新商品池");
        
        try {
            // 清理过期产品
            cleanupExpiredProducts();
            
            // 更新现有产品数据
            updateExistingProducts();
            
            // 补充新产品
            supplementNewProducts();
            
            logger.info("定时刷新商品池完成");
            
        } catch (Exception e) {
            logger.error("定时刷新商品池失败: {}", e.getMessage(), e);
        }
    }

    /**
     * 清理过期产品
     */
    private void cleanupExpiredProducts() {
        logger.info("清理过期产品");
        
        // 获取7天未更新的产品
        List<Product> expiredProducts = productService.getProductsNeedingUpdate(7 * 24);
        
        for (Product product : expiredProducts) {
            // 检查产品是否仍然可用
            ozonApiService.isProductAvailable(product.getOzonId())
                    .subscribe(isAvailable -> {
                        if (!isAvailable) {
                            // 标记为不可用
                            product.setStatus(Product.ProductStatus.DISCONTINUED);
                            productService.saveProduct(product);
                            logger.info("产品 {} 已标记为停售", product.getName());
                        }
                    });
        }
    }

    /**
     * 更新现有产品数据
     */
    @Async
    private void updateExistingProducts() {
        logger.info("更新现有产品数据");
        
        // 获取需要更新的产品（24小时未更新）
        List<Product> productsToUpdate = productService.getProductsNeedingUpdate(24);
        
        // 分批更新，避免API限制
        for (int i = 0; i < productsToUpdate.size(); i += 20) {
            int endIndex = Math.min(i + 20, productsToUpdate.size());
            List<Product> batch = productsToUpdate.subList(i, endIndex);
            
            List<Long> productIds = batch.stream()
                    .map(Product::getOzonId)
                    .toList();
            
            ozonApiService.batchGetProductDetails(productIds)
                    .thenAccept(updatedProducts -> {
                        productService.saveAllProducts(updatedProducts);
                        logger.info("更新了 {} 个产品的数据", updatedProducts.size());
                    })
                    .exceptionally(ex -> {
                        logger.error("批量更新产品失败: {}", ex.getMessage());
                        return null;
                    });
            
            // API频率控制
            try {
                Thread.sleep(2000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }

    /**
     * 补充新产品到商品池
     */
    @Async
    private void supplementNewProducts() {
        logger.info("补充新产品到商品池");
        
        // 重新执行热门产品收集
        collectTrendingProducts().join();
        
        // 基于最新趋势补充产品
        collectLatestTrendProducts().join();
    }

    /**
     * 收集最新趋势产品
     */
    private CompletableFuture<Void> collectLatestTrendProducts() {
        logger.info("收集最新趋势产品");
        
        // 基于最近分析结果的热门分类
        List<String> trendingKeywords = Arrays.asList(
                "新品", "热销", "限时优惠", "爆款", "推荐"
        );
        
        List<CompletableFuture<Void>> futures = trendingKeywords.stream()
                .map(keyword -> {
                    OzonSearchRequest request = new OzonSearchRequest(keyword, 50);
                    request.setSort("new");  // 按新品排序
                    request.setMinRating(4.0);
                    
                    return ozonApiService.searchProducts(request)
                            .filter(this::isQualifiedProduct)
                            .collectList()
                            .flatMap(products -> saveProductsToPool(products, "latest-trend"))
                            .toFuture()
                            .thenApply(v -> (Void) null);
                })
                .toList();
        
        return CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]));
    }

    /**
     * 获取商品池统计信息
     */
    public ProductPoolStatistics getPoolStatistics() {
        logger.info("获取商品池统计信息");
        
        Object marketStats = productService.getMarketStatistics();
        List<ProductService.CategoryStatistics> categoryStats = productService.getCategoryStatistics();
        
        // 最近24小时新增产品数
        List<Product> recentProducts = productService.getRecentlyUpdatedProducts(24);
        
        // 待分析产品数
        // 这里需要实现获取未分析产品的逻辑
        
        return new ProductPoolStatistics(
                marketStats,
                categoryStats,
                recentProducts.size(),
                LocalDateTime.now()
        );
    }

    /**
     * 商品池统计信息数据类
     */
    public static class ProductPoolStatistics {
        private final Object marketStatistics;
        private final List<ProductService.CategoryStatistics> categoryStatistics;
        private final int recentlyAddedCount;
        private final LocalDateTime lastUpdated;

        public ProductPoolStatistics(Object marketStatistics,
                                   List<ProductService.CategoryStatistics> categoryStatistics,
                                   int recentlyAddedCount,
                                   LocalDateTime lastUpdated) {
            this.marketStatistics = marketStatistics;
            this.categoryStatistics = categoryStatistics;
            this.recentlyAddedCount = recentlyAddedCount;
            this.lastUpdated = lastUpdated;
        }

        // Getters
        public Object getMarketStatistics() { return marketStatistics; }
        public List<ProductService.CategoryStatistics> getCategoryStatistics() { return categoryStatistics; }
        public int getRecentlyAddedCount() { return recentlyAddedCount; }
        public LocalDateTime getLastUpdated() { return lastUpdated; }
    }
}
