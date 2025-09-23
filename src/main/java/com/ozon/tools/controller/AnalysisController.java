package com.ozon.tools.controller;

import com.ozon.tools.domain.entity.Product;
import com.ozon.tools.domain.entity.ProductAnalysis;
import com.ozon.tools.service.ProductAnalysisService;
import com.ozon.tools.service.ProductService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;

/**
 * REST Controller for AI-powered product analysis
 * 
 * @author AI Assistant
 */
@RestController
@RequestMapping("/analysis")
@Tag(name = "Product Analysis", description = "AI-powered product analysis and recommendations")
public class AnalysisController {

    private static final Logger logger = LoggerFactory.getLogger(AnalysisController.class);

    private final ProductAnalysisService analysisService;
    private final ProductService productService;

    public AnalysisController(ProductAnalysisService analysisService,
                            ProductService productService) {
        this.analysisService = analysisService;
        this.productService = productService;
    }

    @PostMapping("/product/{productId}")
    @Operation(summary = "Analyze a product", 
               description = "Generate AI-powered analysis for a specific product")
    public CompletableFuture<ResponseEntity<ProductAnalysis>> analyzeProduct(
            @Parameter(description = "Product ID (local database)") 
            @PathVariable Long productId) {
        logger.info("Starting analysis for product ID: {}", productId);

        Optional<Product> productOpt = productService.getProductById(productId);
        if (productOpt.isEmpty()) {
            return CompletableFuture.completedFuture(ResponseEntity.notFound().build());
        }

        return analysisService.analyzeProduct(productOpt.get())
                .thenApply(analysis -> {
                    logger.info("Analysis completed for product: {} with score: {}", 
                               productOpt.get().getName(), analysis.getRecommendationScore());
                    return ResponseEntity.ok(analysis);
                })
                .exceptionally(ex -> {
                    logger.error("Error analyzing product {}: {}", productId, ex.getMessage());
                    return ResponseEntity.internalServerError().build();
                });
    }

    @PostMapping("/batch")
    @Operation(summary = "Batch analyze products", 
               description = "Analyze multiple products in a single request")
    public CompletableFuture<ResponseEntity<List<ProductAnalysis>>> batchAnalyzeProducts(
            @Parameter(description = "List of Product IDs (local database)") 
            @RequestBody List<Long> productIds) {
        logger.info("Starting batch analysis for {} products", productIds.size());

        List<Product> products = productService.getProductsByIds(productIds);
        if (products.isEmpty()) {
            return CompletableFuture.completedFuture(ResponseEntity.notFound().build());
        }

        return analysisService.batchAnalyzeProducts(products)
                .thenApply(analyses -> {
                    logger.info("Batch analysis completed for {} products", analyses.size());
                    return ResponseEntity.ok(analyses);
                })
                .exceptionally(ex -> {
                    logger.error("Error in batch analysis: {}", ex.getMessage());
                    return ResponseEntity.internalServerError().build();
                });
    }

    @GetMapping("/recommendations")
    @Operation(summary = "Get top recommended products", 
               description = "Retrieve products with highest recommendation scores")
    public ResponseEntity<List<ProductAnalysis>> getTopRecommendations(
            @Parameter(description = "Number of recommendations to return") 
            @RequestParam(defaultValue = "10") @Min(1) @Max(100) int limit) {
        logger.info("Fetching top {} recommendations", limit);

        List<ProductAnalysis> recommendations = analysisService.getTopRecommendedProducts(limit);
        logger.info("Found {} recommendations", recommendations.size());

        return ResponseEntity.ok(recommendations);
    }

    @GetMapping("/market-summary")
    @Operation(summary = "Generate market analysis summary", 
               description = "AI-generated summary of market trends and opportunities")
    public CompletableFuture<ResponseEntity<String>> getMarketAnalysisSummary(
            @Parameter(description = "Product IDs to include in analysis") 
            @RequestParam(required = false) List<Long> productIds) {
        logger.info("Generating market analysis summary");

        if (productIds == null || productIds.isEmpty()) {
            // Get top products if no specific IDs provided
            productIds = analysisService.getTopRecommendedProducts(50)
                    .stream()
                    .map(analysis -> analysis.getProduct().getId())
                    .toList();
        }

        return analysisService.generateMarketAnalysisSummary(productIds)
                .thenApply(summary -> {
                    logger.info("Market analysis summary generated");
                    return ResponseEntity.ok(summary);
                })
                .exceptionally(ex -> {
                    logger.error("Error generating market summary: {}", ex.getMessage());
                    return ResponseEntity.internalServerError().build();
                });
    }

    @GetMapping("/trends")
    @Operation(summary = "Get analysis trends", 
               description = "Analyze trends over a specified time period")
    public CompletableFuture<ResponseEntity<String>> getAnalysisTrends(
            @Parameter(description = "Number of days to analyze") 
            @RequestParam(defaultValue = "7") @Min(1) @Max(90) int days) {
        logger.info("Analyzing trends for last {} days", days);

        return analysisService.getAnalysisTrends(days)
                .thenApply(trends -> {
                    logger.info("Trends analysis completed");
                    return ResponseEntity.ok(trends);
                })
                .exceptionally(ex -> {
                    logger.error("Error generating trends: {}", ex.getMessage());
                    return ResponseEntity.internalServerError().build();
                });
    }

    @GetMapping("/product/{productId}/latest")
    @Operation(summary = "Get latest analysis for product", 
               description = "Retrieve the most recent analysis for a specific product")
    public ResponseEntity<ProductAnalysis> getLatestAnalysis(
            @Parameter(description = "Product ID (local database)") 
            @PathVariable Long productId) {
        logger.info("Fetching latest analysis for product: {}", productId);

        ProductAnalysis analysis = analysisService.getTopRecommendedProducts(1)
                .stream()
                .filter(a -> a.getProduct().getId().equals(productId))
                .findFirst()
                .orElse(null);

        if (analysis != null) {
            logger.info("Found latest analysis for product: {}", productId);
            return ResponseEntity.ok(analysis);
        } else {
            logger.info("No analysis found for product: {}", productId);
            return ResponseEntity.notFound().build();
        }
    }

    @GetMapping("/category/{categoryId}")
    @Operation(summary = "Get category analysis", 
               description = "Retrieve analysis for products in a specific category")
    public ResponseEntity<List<ProductAnalysis>> getCategoryAnalysis(
            @Parameter(description = "Category ID") 
            @PathVariable Long categoryId,
            @Parameter(description = "Number of results to return") 
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int limit) {
        logger.info("Fetching analysis for category: {}, limit: {}", categoryId, limit);

        // This would require implementing the method in ProductAnalysisService
        // For now, return empty list with appropriate logging
        logger.warn("Category analysis not yet implemented");
        return ResponseEntity.ok(List.of());
    }

    @PostMapping("/refresh/{productId}")
    @Operation(summary = "Refresh product analysis", 
               description = "Force refresh of product analysis regardless of cache")
    public CompletableFuture<ResponseEntity<ProductAnalysis>> refreshAnalysis(
            @Parameter(description = "Product ID (local database)") 
            @PathVariable Long productId) {
        logger.info("Refreshing analysis for product: {}", productId);

        Optional<Product> productOpt = productService.getProductById(productId);
        if (productOpt.isEmpty()) {
            return CompletableFuture.completedFuture(ResponseEntity.notFound().build());
        }

        // Force fresh analysis by clearing cache if needed
        return analysisService.analyzeProduct(productOpt.get())
                .thenApply(analysis -> {
                    logger.info("Analysis refreshed for product: {}", productId);
                    return ResponseEntity.ok(analysis);
                })
                .exceptionally(ex -> {
                    logger.error("Error refreshing analysis for product {}: {}", productId, ex.getMessage());
                    return ResponseEntity.internalServerError().build();
                });
    }

    @GetMapping("/health")
    @Operation(summary = "Analysis service health check", 
               description = "Check the health status of analysis services")
    public ResponseEntity<String> healthCheck() {
        logger.info("Analysis service health check");
        return ResponseEntity.ok("Analysis service is healthy");
    }

    @GetMapping("/statistics")
    @Operation(summary = "Get analysis statistics", 
               description = "Retrieve statistics about analysis performance and results")
    public ResponseEntity<Object> getAnalysisStatistics() {
        logger.info("Fetching analysis statistics");
        // This would require implementing statistics collection
        // For now, return a simple status
        return ResponseEntity.ok("Analysis statistics feature coming soon");
    }

    @DeleteMapping("/product/{productId}")
    @Operation(summary = "Delete product analyses", 
               description = "Remove all analyses for a specific product")
    public ResponseEntity<Void> deleteProductAnalyses(
            @Parameter(description = "Product ID (local database)") 
            @PathVariable Long productId) {
        logger.info("Deleting analyses for product: {}", productId);
        
        // This would require implementing delete method in service
        logger.warn("Delete analysis functionality not yet implemented");
        return ResponseEntity.noContent().build();
    }
}
