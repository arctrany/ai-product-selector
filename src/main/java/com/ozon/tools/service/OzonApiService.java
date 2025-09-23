package com.ozon.tools.service;

import com.ozon.tools.domain.entity.Product;
import com.ozon.tools.dto.ozon.OzonProductResponse;
import com.ozon.tools.dto.ozon.OzonSearchRequest;
import com.ozon.tools.dto.ozon.OzonProductDetailsResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.util.retry.Retry;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * Service for integrating with OZON API
 * 
 * @author AI Assistant
 */
@Service
public class OzonApiService {

    private static final Logger logger = LoggerFactory.getLogger(OzonApiService.class);

    private final WebClient webClient;
    private final String clientId;
    private final String apiKey;

    public OzonApiService(WebClient.Builder webClientBuilder,
                         @Value("${ozon.api.base-url}") String baseUrl,
                         @Value("${ozon.api.client-id}") String clientId,
                         @Value("${ozon.api.api-key}") String apiKey) {
        this.clientId = clientId;
        this.apiKey = apiKey;
        this.webClient = webClientBuilder
                .baseUrl(baseUrl)
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .defaultHeader("Client-Id", clientId)
                .defaultHeader("Api-Key", apiKey)
                .build();
    }

    /**
     * Search products on OZON marketplace
     * 
     * @param request Search request parameters
     * @return Flux of products
     */
    public Flux<Product> searchProducts(OzonSearchRequest request) {
        logger.info("Searching OZON products with query: {}", request.getQuery());

        return webClient.post()
                .uri("/v2/product/list")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(OzonProductResponse.class)
                .retryWhen(Retry.backoff(3, Duration.ofSeconds(1))
                        .filter(throwable -> throwable instanceof WebClientResponseException.TooManyRequests))
                .doOnError(error -> logger.error("Error searching products: {}", error.getMessage()))
                .flatMapMany(response -> Flux.fromIterable(response.getResult().getItems()))
                .map(this::mapToProduct)
                .doOnNext(product -> logger.debug("Found product: {}", product.getName()));
    }

    /**
     * Get detailed product information
     * 
     * @param productId OZON product ID
     * @return Product details
     */
    @Cacheable(value = "productDetails", key = "#productId")
    public Mono<Product> getProductDetails(Long productId) {
        logger.info("Fetching product details for ID: {}", productId);

        return webClient.post()
                .uri("/v2/product/info")
                .bodyValue(new OzonProductDetailsRequest(productId))
                .retrieve()
                .bodyToMono(OzonProductDetailsResponse.class)
                .retryWhen(Retry.backoff(3, Duration.ofSeconds(1))
                        .filter(throwable -> throwable instanceof WebClientResponseException.TooManyRequests))
                .doOnError(error -> logger.error("Error fetching product details for ID {}: {}", productId, error.getMessage()))
                .map(response -> mapToDetailedProduct(response.getResult()))
                .doOnNext(product -> logger.debug("Fetched detailed product: {}", product.getName()));
    }

    /**
     * Get products by category
     * 
     * @param categoryId Category ID
     * @param limit Number of products to fetch
     * @return Flux of products
     */
    public Flux<Product> getProductsByCategory(Long categoryId, int limit) {
        logger.info("Fetching products for category: {}, limit: {}", categoryId, limit);

        OzonSearchRequest request = new OzonSearchRequest();
        request.setCategoryId(categoryId);
        request.setLimit(limit);

        return searchProducts(request);
    }

    /**
     * Get trending products
     * 
     * @param limit Number of products to fetch
     * @return Flux of trending products
     */
    public Flux<Product> getTrendingProducts(int limit) {
        logger.info("Fetching trending products, limit: {}", limit);

        OzonSearchRequest request = new OzonSearchRequest();
        request.setSort("popularity");
        request.setLimit(limit);

        return searchProducts(request);
    }

    /**
     * Batch fetch product details
     * 
     * @param productIds List of product IDs
     * @return CompletableFuture with list of products
     */
    public CompletableFuture<List<Product>> batchGetProductDetails(List<Long> productIds) {
        logger.info("Batch fetching {} product details", productIds.size());

        return Flux.fromIterable(productIds)
                .flatMap(this::getProductDetails, 5) // Limit concurrent requests
                .collectList()
                .toFuture();
    }

    /**
     * Check product availability
     * 
     * @param productId Product ID
     * @return True if product is available
     */
    public Mono<Boolean> isProductAvailable(Long productId) {
        return getProductDetails(productId)
                .map(product -> product.getStatus() == Product.ProductStatus.ACTIVE && 
                               product.getStockQuantity() != null && 
                               product.getStockQuantity() > 0)
                .onErrorReturn(false);
    }

    /**
     * Map OZON API response to Product entity
     */
    private Product mapToProduct(OzonProductResponse.ProductItem item) {
        Product product = new Product();
        product.setOzonId(item.getId());
        product.setName(item.getName());
        product.setPrice(item.getPrice());
        product.setOldPrice(item.getOldPrice());
        product.setCurrency(item.getCurrencyCode());
        product.setRating(item.getRating());
        product.setReviewsCount(item.getReviewsCount());
        product.setImageUrl(item.getMainImage());
        product.setHasDiscount(item.getOldPrice() != null && 
                              item.getOldPrice().compareTo(item.getPrice()) > 0);
        
        return product;
    }

    /**
     * Map detailed OZON API response to Product entity
     */
    private Product mapToDetailedProduct(OzonProductDetailsResponse.ProductDetails details) {
        Product product = new Product();
        product.setOzonId(details.getId());
        product.setName(details.getName());
        product.setDescription(details.getDescription());
        product.setCategoryId(details.getCategoryId());
        product.setPrice(details.getPrice());
        product.setOldPrice(details.getOldPrice());
        product.setCurrency(details.getCurrencyCode());
        product.setRating(details.getRating());
        product.setReviewsCount(details.getReviewsCount());
        product.setBrand(details.getBrand());
        product.setImageUrl(details.getMainImage());
        product.setStockQuantity(details.getStocks());
        product.setHasDiscount(details.getOldPrice() != null && 
                              details.getOldPrice().compareTo(details.getPrice()) > 0);
        
        return product;
    }

    /**
     * Internal class for product details request
     */
    private static class OzonProductDetailsRequest {
        private final Long productId;

        public OzonProductDetailsRequest(Long productId) {
            this.productId = productId;
        }

        public Long getProductId() {
            return productId;
        }
    }
}
