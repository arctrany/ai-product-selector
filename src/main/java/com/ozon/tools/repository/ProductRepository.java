package com.ozon.tools.repository;

import com.ozon.tools.domain.entity.Product;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * Repository for Product entity
 * 
 * @author AI Assistant
 */
@Repository
public interface ProductRepository extends JpaRepository<Product, Long> {

    /**
     * Find product by OZON ID
     */
    Optional<Product> findByOzonId(Long ozonId);

    /**
     * Find products by category
     */
    Page<Product> findByCategoryId(Long categoryId, Pageable pageable);

    /**
     * Find products by category name
     */
    Page<Product> findByCategoryNameContainingIgnoreCase(String categoryName, Pageable pageable);

    /**
     * Find products by brand
     */
    Page<Product> findByBrandContainingIgnoreCase(String brand, Pageable pageable);

    /**
     * Find products within price range
     */
    @Query("SELECT p FROM Product p WHERE p.price BETWEEN :minPrice AND :maxPrice")
    Page<Product> findByPriceRange(@Param("minPrice") BigDecimal minPrice, 
                                   @Param("maxPrice") BigDecimal maxPrice, 
                                   Pageable pageable);

    /**
     * Find products with minimum rating
     */
    @Query("SELECT p FROM Product p WHERE p.rating >= :minRating")
    Page<Product> findByRatingGreaterThanEqual(@Param("minRating") BigDecimal minRating, 
                                               Pageable pageable);

    /**
     * Find products with discounts
     */
    @Query("SELECT p FROM Product p WHERE p.hasDiscount = true AND p.oldPrice > p.price")
    Page<Product> findProductsWithDiscounts(Pageable pageable);

    /**
     * Find products by seller
     */
    Page<Product> findBySellerId(Long sellerId, Pageable pageable);

    /**
     * Find top-rated products
     */
    @Query("SELECT p FROM Product p WHERE p.rating >= 4.0 AND p.reviewsCount >= 10 " +
           "ORDER BY p.rating DESC, p.reviewsCount DESC")
    Page<Product> findTopRatedProducts(Pageable pageable);

    /**
     * Find trending products (high sales volume)
     */
    @Query("SELECT p FROM Product p WHERE p.salesVolume > 0 " +
           "ORDER BY p.salesVolume DESC, p.reviewsCount DESC")
    Page<Product> findTrendingProducts(Pageable pageable);

    /**
     * Search products by name
     */
    @Query("SELECT p FROM Product p WHERE p.name LIKE %:query% OR p.description LIKE %:query%")
    Page<Product> searchByQuery(@Param("query") String query, Pageable pageable);

    /**
     * Find recently updated products
     */
    @Query("SELECT p FROM Product p WHERE p.lastUpdated >= :since ORDER BY p.lastUpdated DESC")
    List<Product> findRecentlyUpdated(@Param("since") LocalDateTime since);

    /**
     * Find products needing price update
     */
    @Query("SELECT p FROM Product p WHERE p.lastUpdated < :threshold")
    List<Product> findProductsNeedingUpdate(@Param("threshold") LocalDateTime threshold);

    /**
     * Get products count by category
     */
    @Query("SELECT p.categoryName, COUNT(p) FROM Product p " +
           "WHERE p.status = 'ACTIVE' " +
           "GROUP BY p.categoryName " +
           "ORDER BY COUNT(p) DESC")
    List<Object[]> getProductCountByCategory();

    /**
     * Get average price by category
     */
    @Query("SELECT p.categoryName, AVG(p.price) FROM Product p " +
           "WHERE p.status = 'ACTIVE' AND p.price > 0 " +
           "GROUP BY p.categoryName")
    List<Object[]> getAveragePriceByCategory();

    /**
     * Find premium products
     */
    @Query("SELECT p FROM Product p WHERE p.isPremium = true")
    Page<Product> findPremiumProducts(Pageable pageable);

    /**
     * Complex search with multiple filters
     */
    @Query("SELECT p FROM Product p WHERE " +
           "(:categoryId IS NULL OR p.categoryId = :categoryId) AND " +
           "(:minPrice IS NULL OR p.price >= :minPrice) AND " +
           "(:maxPrice IS NULL OR p.price <= :maxPrice) AND " +
           "(:minRating IS NULL OR p.rating >= :minRating) AND " +
           "(:hasDiscount IS NULL OR p.hasDiscount = :hasDiscount) AND " +
           "(:brand IS NULL OR p.brand LIKE %:brand%) AND " +
           "p.status = 'ACTIVE'")
    Page<Product> findWithFilters(@Param("categoryId") Long categoryId,
                                  @Param("minPrice") BigDecimal minPrice,
                                  @Param("maxPrice") BigDecimal maxPrice,
                                  @Param("minRating") BigDecimal minRating,
                                  @Param("hasDiscount") Boolean hasDiscount,
                                  @Param("brand") String brand,
                                  Pageable pageable);

    /**
     * Find similar products by category and price range
     */
    @Query("SELECT p FROM Product p WHERE " +
           "p.categoryId = :categoryId AND " +
           "p.price BETWEEN :minPrice AND :maxPrice AND " +
           "p.id != :excludeId " +
           "ORDER BY ABS(p.price - :targetPrice)")
    List<Product> findSimilarProducts(@Param("categoryId") Long categoryId,
                                      @Param("minPrice") BigDecimal minPrice,
                                      @Param("maxPrice") BigDecimal maxPrice,
                                      @Param("targetPrice") BigDecimal targetPrice,
                                      @Param("excludeId") Long excludeId,
                                      Pageable pageable);

    /**
     * Get market statistics
     */
    @Query("SELECT " +
           "COUNT(p) as totalProducts, " +
           "AVG(p.price) as avgPrice, " +
           "AVG(p.rating) as avgRating, " +
           "SUM(p.salesVolume) as totalSales " +
           "FROM Product p WHERE p.status = 'ACTIVE'")
    Object[] getMarketStatistics();

    /**
     * Check if product exists by OZON ID
     */
    boolean existsByOzonId(Long ozonId);

    /**
     * Count products by status
     */
    @Query("SELECT p.status, COUNT(p) FROM Product p GROUP BY p.status")
    List<Object[]> countByStatus();
}

