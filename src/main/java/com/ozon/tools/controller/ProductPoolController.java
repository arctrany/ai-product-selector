package com.ozon.tools.controller;

import com.ozon.tools.service.ProductPoolService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.concurrent.CompletableFuture;

/**
 * 商品池管理控制器
 * 
 * @author AI Assistant
 */
@RestController
@RequestMapping("/product-pool")
@Tag(name = "Product Pool Management", description = "商品池管理和数据源控制")
public class ProductPoolController {

    private static final Logger logger = LoggerFactory.getLogger(ProductPoolController.class);

    private final ProductPoolService productPoolService;

    public ProductPoolController(ProductPoolService productPoolService) {
        this.productPoolService = productPoolService;
    }

    @PostMapping("/initialize")
    @Operation(summary = "初始化商品池", 
               description = "从多个数据源初始化商品池，包括热门产品、分类产品、竞品分析等")
    public CompletableFuture<ResponseEntity<String>> initializePool() {
        logger.info("接收到商品池初始化请求");

        return productPoolService.initializeProductPool()
                .thenApply(v -> {
                    logger.info("商品池初始化完成");
                    return ResponseEntity.ok("商品池初始化成功启动，请查看日志了解进度");
                })
                .exceptionally(ex -> {
                    logger.error("商品池初始化失败: {}", ex.getMessage());
                    return ResponseEntity.internalServerError()
                            .body("商品池初始化失败: " + ex.getMessage());
                });
    }

    @PostMapping("/refresh")
    @Operation(summary = "刷新商品池", 
               description = "手动触发商品池刷新，更新现有产品数据并补充新产品")
    public ResponseEntity<String> refreshPool() {
        logger.info("接收到商品池刷新请求");

        try {
            productPoolService.scheduledRefreshProductPool();
            return ResponseEntity.ok("商品池刷新任务已启动");
        } catch (Exception e) {
            logger.error("商品池刷新失败: {}", e.getMessage());
            return ResponseEntity.internalServerError()
                    .body("商品池刷新失败: " + e.getMessage());
        }
    }

    @GetMapping("/statistics")
    @Operation(summary = "获取商品池统计信息", 
               description = "查看商品池的统计数据，包括产品数量、分类分布、更新状态等")
    public ResponseEntity<ProductPoolService.ProductPoolStatistics> getPoolStatistics() {
        logger.info("获取商品池统计信息");

        try {
            ProductPoolService.ProductPoolStatistics stats = productPoolService.getPoolStatistics();
            return ResponseEntity.ok(stats);
        } catch (Exception e) {
            logger.error("获取商品池统计信息失败: {}", e.getMessage());
            return ResponseEntity.internalServerError().build();
        }
    }

    @GetMapping("/health")
    @Operation(summary = "商品池健康检查", 
               description = "检查商品池服务的健康状态")
    public ResponseEntity<String> healthCheck() {
        return ResponseEntity.ok("商品池服务运行正常");
    }
}
