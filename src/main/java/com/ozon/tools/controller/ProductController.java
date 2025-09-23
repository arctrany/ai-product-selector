package com.ozon.tools.controller;

import com.ozon.tools.domain.entity.Product;
import com.ozon.tools.domain.entity.ProductAnalysis;
import com.ozon.tools.dto.ozon.OzonSearchRequest;
import com.ozon.tools.service.OzonApiService;
import com.ozon.tools.service.ProductAnalysisService;
import com.ozon.tools.service.ProductService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.math.BigDecimal;
import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * REST Controller for product operations
 * 
 * @author AI Assistant
 */
@RestController
@RequestMapping("/products")
@Tag(name = "Product Management", description = "APIs for product search, analysis and management")
public class ProductController {

    private static final Logger logger = LoggerFactory.getLogger(ProductController.class);

    private final OzonApiService ozonApiService;
    private final ProductService productService;
    private final ProductAnalysisService analysisService;

    public ProductController(OzonApiService ozonApiService,
                           ProductService productService,
                           ProductAnalysisService analysisService) {
        this.ozonApiService = ozonApiService;
        this.productService = productService;
        this.analysisService = analysisService;
    }

    @GetMapping("/search")
    @Operation(summary = "Search products on OZON", 
               description = "Search products using various filters and criteria")
    public Flux<Product> searchProducts(@Valid @ModelAttribute OzonSearchRequest request) {
        logger.info("Received product search request: {}", request);
        return ozonApiService.searchProducts(request);
    }

    @PostMapping("/search")
    @Operation(summary = "Advanced product search", 
               description = "Search products with POST request for complex filters")
    public Flux<Product> searchProductsPost(@Valid @RequestBody OzonSearchRequest request) {
        logger.info("Received advanced product search request: {}", request);
        return ozonApiService.searchProducts(request);
    }

    @GetMapping("/{productId}")
    @Operation(summary = "Get product details", 
               description = "Retrieve detailed information about a specific product")
    public Mono<ResponseEntity<Product>> getProductById(
            @Parameter(description = "OZON Product ID") 
            @PathVariable Long productId) {
        logger.info("Fetching product details for ID: {}", productId);
        return ozonApiService.getProductDetails(productId)
                .map(ResponseEntity::ok)
                .defaultIfEmpty(ResponseEntity.notFound().build());
    }

    @GetMapping("/category/{categoryId}")
    @Operation(summary = "Get products by category", 
               description = "Retrieve products from a specific category")
    public Flux<Product> getProductsByCategory(
            @Parameter(description = "Category ID") 
            @PathVariable Long categoryId,
            @Parameter(description = "Maximum number of products to return") 
            @RequestParam(defaultValue = "50") @Min(1) @Max(1000) int limit) {
        logger.info("Fetching products for category: {}, limit: {}", categoryId, limit);
        return ozonApiService.getProductsByCategory(categoryId, limit);
    }

    @GetMapping("/trending")
    @Operation(summary = "Get trending products", 
               description = "Retrieve currently trending products on OZON")
    public Flux<Product> getTrendingProducts(
            @Parameter(description = "Number of trending products to return") 
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int limit) {
        logger.info("Fetching trending products, limit: {}", limit);
        return ozonApiService.getTrendingProducts(limit);
    }

    @GetMapping("/local")
    @Operation(summary = "Get locally stored products", 
               description = "Retrieve products from local database with pagination")
    public ResponseEntity<Page<Product>> getLocalProducts(
            @Parameter(description = "Page number (0-based)") 
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @Parameter(description = "Page size") 
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size,
            @Parameter(description = "Sort field") 
            @RequestParam(defaultValue = "lastUpdated") String sort,
            @Parameter(description = "Sort direction") 
            @RequestParam(defaultValue = "desc") String direction) {
        
        Sort sortObj = Sort.by(Sort.Direction.fromString(direction), sort);
        Pageable pageable = PageRequest.of(page, size, sortObj);
        
        Page<Product> products = productService.getAllProducts(pageable);
        logger.info("Retrieved {} local products (page {}/{})", 
                   products.getNumberOfElements(), page + 1, products.getTotalPages());
        
        return ResponseEntity.ok(products);
    }

    @GetMapping("/local/search")
    @Operation(summary = "Search local products", 
               description = "Search products in local database by query")
    public ResponseEntity<Page<Product>> searchLocalProducts(
            @Parameter(description = "Search query") 
            @RequestParam String query,
            @Parameter(description = "Page number (0-based)") 
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @Parameter(description = "Page size") 
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        
        Pageable pageable = PageRequest.of(page, size);
        Page<Product> products = productService.searchProducts(query, pageable);
        
        logger.info("Found {} local products for query: '{}'", 
                   products.getTotalElements(), query);
        
        return ResponseEntity.ok(products);
    }

    @GetMapping("/local/filters")
    @Operation(summary = "Filter local products", 
               description = "Filter products by various criteria")
    public ResponseEntity<Page<Product>> filterProducts(
            @Parameter(description = "Category ID") 
            @RequestParam(required = false) Long categoryId,
            @Parameter(description = "Minimum price") 
            @RequestParam(required = false) BigDecimal minPrice,
            @Parameter(description = "Maximum price") 
            @RequestParam(required = false) BigDecimal maxPrice,
            @Parameter(description = "Minimum rating") 
            @RequestParam(required = false) BigDecimal minRating,
            @Parameter(description = "Has discount") 
            @RequestParam(required = false) Boolean hasDiscount,
            @Parameter(description = "Brand name") 
            @RequestParam(required = false) String brand,
            @Parameter(description = "Page number (0-based)") 
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @Parameter(description = "Page size") 
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        
        Pageable pageable = PageRequest.of(page, size);
        Page<Product> products = productService.filterProducts(
                categoryId, minPrice, maxPrice, minRating, hasDiscount, brand, pageable);
        
        logger.info("Filtered products: {} results", products.getTotalElements());
        
        return ResponseEntity.ok(products);
    }

    @PostMapping("/{productId}/sync")
    @Operation(summary = "Sync product from OZON", 
               description = "Fetch and store product data from OZON API")
    public CompletableFuture<ResponseEntity<Product>> syncProduct(
            @Parameter(description = "OZON Product ID") 
            @PathVariable Long productId) {
        logger.info("Syncing product from OZON: {}", productId);
        
        return ozonApiService.getProductDetails(productId)
                .map(productService::saveProduct)
                .toFuture()
                .thenApply(ResponseEntity::ok)
                .exceptionally(ex -> {
                    logger.error("Error syncing product {}: {}", productId, ex.getMessage());
                    return ResponseEntity.internalServerError().build();
                });
    }

    @PostMapping("/batch-sync")
    @Operation(summary = "Batch sync products", 
               description = "Sync multiple products from OZON API")
    public CompletableFuture<ResponseEntity<List<Product>>> batchSyncProducts(
            @Parameter(description = "List of OZON Product IDs") 
            @RequestBody List<Long> productIds) {
        logger.info("Batch syncing {} products", productIds.size());
        
        return ozonApiService.batchGetProductDetails(productIds)
                .thenApply(products -> {
                    List<Product> savedProducts = products.stream()
                            .map(productService::saveProduct)
                            .toList();
                    logger.info("Successfully synced {} products", savedProducts.size());
                    return ResponseEntity.ok(savedProducts);
                })
                .exceptionally(ex -> {
                    logger.error("Error in batch sync: {}", ex.getMessage());
                    return ResponseEntity.internalServerError().build();
                });
    }

    @GetMapping("/{productId}/availability")
    @Operation(summary = "Check product availability", 
               description = "Check if a product is currently available on OZON")
    public Mono<ResponseEntity<Boolean>> checkProductAvailability(
            @Parameter(description = "OZON Product ID") 
            @PathVariable Long productId) {
        logger.info("Checking availability for product: {}", productId);
        return ozonApiService.isProductAvailable(productId)
                .map(ResponseEntity::ok)
                .defaultIfEmpty(ResponseEntity.notFound().build());
    }

    @GetMapping("/statistics")
    @Operation(summary = "Get market statistics", 
               description = "Retrieve general market statistics")
    public ResponseEntity<Object> getMarketStatistics() {
        logger.info("Fetching market statistics");
        Object stats = productService.getMarketStatistics();
        return ResponseEntity.ok(stats);
    }

    @DeleteMapping("/{productId}")
    @Operation(summary = "Delete product", 
               description = "Remove a product from local database")
    public ResponseEntity<Void> deleteProduct(
            @Parameter(description = "Product ID (local database)") 
            @PathVariable Long productId) {
        logger.info("Deleting product: {}", productId);
        boolean deleted = productService.deleteProduct(productId);
        return deleted ? ResponseEntity.noContent().build() : ResponseEntity.notFound().build();
    }
}
