package com.ozon.tools.service;

import com.ozon.tools.domain.entity.Product;
import com.ozon.tools.repository.ProductRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * Service for product management operations
 * 
 * @author AI Assistant
 */
@Service
@Transactional
public class ProductService {

    private static final Logger logger = LoggerFactory.getLogger(ProductService.class);

    private final ProductRepository productRepository;

    public ProductService(ProductRepository productRepository) {
        this.productRepository = productRepository;
    }

    /**
     * Get all products with pagination
     */
    public Page<Product> getAllProducts(Pageable pageable) {
        logger.debug("Fetching all products with pagination: {}", pageable);
        return productRepository.findAll(pageable);
    }

    /**
     * Get product by ID
     */
    @Cacheable(value = "products", key = "#id")
    public Optional<Product> getProductById(Long id) {
        logger.debug("Fetching product by ID: {}", id);
        return productRepository.findById(id);
    }

    /**
     * Get product by OZON ID
     */
    @Cacheable(value = "productsByOzonId", key = "#ozonId")
    public Optional<Product> getProductByOzonId(Long ozonId) {
        logger.debug("Fetching product by OZON ID: {}", ozonId);
        return productRepository.findByOzonId(ozonId);
    }

    /**
     * Get multiple products by IDs
     */
    public List<Product> getProductsByIds(List<Long> ids) {
        logger.debug("Fetching {} products by IDs", ids.size());
        return productRepository.findAllById(ids);
    }

    /**
     * Save or update product
     */
    @CacheEvict(value = {"products", "productsByOzonId"}, allEntries = true)
    public Product saveProduct(Product product) {
        logger.debug("Saving product: {}", product.getName());
        
        // Check if product already exists by OZON ID
        if (product.getOzonId() != null) {
            Optional<Product> existingProduct = productRepository.findByOzonId(product.getOzonId());
            if (existingProduct.isPresent()) {
                // Update existing product
                Product existing = existingProduct.get();
                updateProductFields(existing, product);
                product = existing;
            }
        }
        
        Product savedProduct = productRepository.save(product);
        logger.info("Successfully saved product: {} (ID: {})", savedProduct.getName(), savedProduct.getId());
        return savedProduct;
    }

    /**
     * Search products by query
     */
    public Page<Product> searchProducts(String query, Pageable pageable) {
        logger.debug("Searching products with query: '{}', pagination: {}", query, pageable);
        return productRepository.searchByQuery(query, pageable);
    }

    /**
     * Filter products by various criteria
     */
    public Page<Product> filterProducts(Long categoryId, BigDecimal minPrice, BigDecimal maxPrice,
                                      BigDecimal minRating, Boolean hasDiscount, String brand,
                                      Pageable pageable) {
        logger.debug("Filtering products with criteria - category: {}, price: {}-{}, rating: {}, discount: {}, brand: {}",
                    categoryId, minPrice, maxPrice, minRating, hasDiscount, brand);
        
        return productRepository.findWithFilters(categoryId, minPrice, maxPrice, 
                                                minRating, hasDiscount, brand, pageable);
    }

    /**
     * Get products by category
     */
    public Page<Product> getProductsByCategory(Long categoryId, Pageable pageable) {
        logger.debug("Fetching products for category: {}", categoryId);
        return productRepository.findByCategoryId(categoryId, pageable);
    }

    /**
     * Get top-rated products
     */
    public Page<Product> getTopRatedProducts(Pageable pageable) {
        logger.debug("Fetching top-rated products");
        return productRepository.findTopRatedProducts(pageable);
    }

    /**
     * Get trending products
     */
    public Page<Product> getTrendingProducts(Pageable pageable) {
        logger.debug("Fetching trending products");
        return productRepository.findTrendingProducts(pageable);
    }

    /**
     * Get products with discounts
     */
    public Page<Product> getProductsWithDiscounts(Pageable pageable) {
        logger.debug("Fetching products with discounts");
        return productRepository.findProductsWithDiscounts(pageable);
    }

    /**
     * Get premium products
     */
    public Page<Product> getPremiumProducts(Pageable pageable) {
        logger.debug("Fetching premium products");
        return productRepository.findPremiumProducts(pageable);
    }

    /**
     * Find similar products
     */
    public List<Product> findSimilarProducts(Product product, int limit) {
        logger.debug("Finding similar products to: {}", product.getName());
        
        if (product.getCategoryId() == null || product.getPrice() == null) {
            return List.of();
        }
        
        BigDecimal priceVariation = product.getPrice().multiply(BigDecimal.valueOf(0.2)); // 20% variation
        BigDecimal minPrice = product.getPrice().subtract(priceVariation);
        BigDecimal maxPrice = product.getPrice().add(priceVariation);
        
        return productRepository.findSimilarProducts(
                product.getCategoryId(), minPrice, maxPrice, 
                product.getPrice(), product.getId(),
                Pageable.ofSize(limit));
    }

    /**
     * Get recently updated products
     */
    public List<Product> getRecentlyUpdatedProducts(int hours) {
        logger.debug("Fetching products updated in last {} hours", hours);
        LocalDateTime since = LocalDateTime.now().minusHours(hours);
        return productRepository.findRecentlyUpdated(since);
    }

    /**
     * Get products needing update
     */
    public List<Product> getProductsNeedingUpdate(int hoursThreshold) {
        logger.debug("Fetching products needing update (older than {} hours)", hoursThreshold);
        LocalDateTime threshold = LocalDateTime.now().minusHours(hoursThreshold);
        return productRepository.findProductsNeedingUpdate(threshold);
    }

    /**
     * Get market statistics
     */
    public Object getMarketStatistics() {
        logger.debug("Fetching market statistics");
        Object[] stats = productRepository.getMarketStatistics();
        
        // Convert to a more readable format
        if (stats != null && stats.length == 4) {
            return new MarketStatistics(
                    ((Number) stats[0]).longValue(),   // totalProducts
                    (BigDecimal) stats[1],             // avgPrice
                    (BigDecimal) stats[2],             // avgRating
                    ((Number) stats[3]).longValue()    // totalSales
            );
        }
        
        return new MarketStatistics(0L, BigDecimal.ZERO, BigDecimal.ZERO, 0L);
    }

    /**
     * Get category statistics
     */
    public List<CategoryStatistics> getCategoryStatistics() {
        logger.debug("Fetching category statistics");
        
        List<Object[]> countResults = productRepository.getProductCountByCategory();
        List<Object[]> priceResults = productRepository.getAveragePriceByCategory();
        
        return countResults.stream().map(result -> {
            String categoryName = (String) result[0];
            Long count = ((Number) result[1]).longValue();
            
            BigDecimal avgPrice = priceResults.stream()
                    .filter(pr -> categoryName.equals(pr[0]))
                    .map(pr -> (BigDecimal) pr[1])
                    .findFirst()
                    .orElse(BigDecimal.ZERO);
            
            return new CategoryStatistics(categoryName, count, avgPrice);
        }).toList();
    }

    /**
     * Delete product
     */
    @CacheEvict(value = {"products", "productsByOzonId"}, allEntries = true)
    public boolean deleteProduct(Long productId) {
        logger.info("Deleting product with ID: {}", productId);
        
        if (productRepository.existsById(productId)) {
            productRepository.deleteById(productId);
            logger.info("Successfully deleted product: {}", productId);
            return true;
        } else {
            logger.warn("Product not found for deletion: {}", productId);
            return false;
        }
    }

    /**
     * Check if product exists by OZON ID
     */
    public boolean existsByOzonId(Long ozonId) {
        return productRepository.existsByOzonId(ozonId);
    }

    /**
     * Bulk save products
     */
    @CacheEvict(value = {"products", "productsByOzonId"}, allEntries = true)
    public List<Product> saveAllProducts(List<Product> products) {
        logger.info("Bulk saving {} products", products.size());
        
        List<Product> savedProducts = productRepository.saveAll(products);
        logger.info("Successfully bulk saved {} products", savedProducts.size());
        
        return savedProducts;
    }

    /**
     * Update product fields from new data
     */
    private void updateProductFields(Product existing, Product newData) {
        if (newData.getName() != null) existing.setName(newData.getName());
        if (newData.getDescription() != null) existing.setDescription(newData.getDescription());
        if (newData.getCategoryId() != null) existing.setCategoryId(newData.getCategoryId());
        if (newData.getCategoryName() != null) existing.setCategoryName(newData.getCategoryName());
        if (newData.getPrice() != null) existing.setPrice(newData.getPrice());
        if (newData.getOldPrice() != null) existing.setOldPrice(newData.getOldPrice());
        if (newData.getRating() != null) existing.setRating(newData.getRating());
        if (newData.getReviewsCount() != null) existing.setReviewsCount(newData.getReviewsCount());
        if (newData.getSalesVolume() != null) existing.setSalesVolume(newData.getSalesVolume());
        if (newData.getStockQuantity() != null) existing.setStockQuantity(newData.getStockQuantity());
        if (newData.getBrand() != null) existing.setBrand(newData.getBrand());
        if (newData.getSellerId() != null) existing.setSellerId(newData.getSellerId());
        if (newData.getSellerName() != null) existing.setSellerName(newData.getSellerName());
        if (newData.getImageUrl() != null) existing.setImageUrl(newData.getImageUrl());
        if (newData.getProductUrl() != null) existing.setProductUrl(newData.getProductUrl());
        if (newData.getStatus() != null) existing.setStatus(newData.getStatus());
        if (newData.getIsPremium() != null) existing.setIsPremium(newData.getIsPremium());
        if (newData.getHasDiscount() != null) existing.setHasDiscount(newData.getHasDiscount());
    }

    /**
     * Market statistics data class
     */
    public static class MarketStatistics {
        private final Long totalProducts;
        private final BigDecimal averagePrice;
        private final BigDecimal averageRating;
        private final Long totalSales;

        public MarketStatistics(Long totalProducts, BigDecimal averagePrice, 
                              BigDecimal averageRating, Long totalSales) {
            this.totalProducts = totalProducts;
            this.averagePrice = averagePrice;
            this.averageRating = averageRating;
            this.totalSales = totalSales;
        }

        // Getters
        public Long getTotalProducts() { return totalProducts; }
        public BigDecimal getAveragePrice() { return averagePrice; }
        public BigDecimal getAverageRating() { return averageRating; }
        public Long getTotalSales() { return totalSales; }
    }

    /**
     * Category statistics data class
     */
    public static class CategoryStatistics {
        private final String categoryName;
        private final Long productCount;
        private final BigDecimal averagePrice;

        public CategoryStatistics(String categoryName, Long productCount, BigDecimal averagePrice) {
            this.categoryName = categoryName;
            this.productCount = productCount;
            this.averagePrice = averagePrice;
        }

        // Getters
        public String getCategoryName() { return categoryName; }
        public Long getProductCount() { return productCount; }
        public BigDecimal getAveragePrice() { return averagePrice; }
    }
}
