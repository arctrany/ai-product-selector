package com.ozon.tools.repository;

import com.ozon.tools.domain.entity.ProductAnalysis;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

/**
 * Repository for ProductAnalysis entity
 * 
 * @author AI Assistant
 */
@Repository
public interface ProductAnalysisRepository extends JpaRepository<ProductAnalysis, Long> {

    /**
     * Find latest analysis for a product
     */
    ProductAnalysis findTopByProductIdOrderByCreatedAtDesc(Long productId);

    /**
     * Find analyses for multiple products
     */
    List<ProductAnalysis> findByProductIdIn(List<Long> productIds);

    /**
     * Find analyses created after a specific date
     */
    List<ProductAnalysis> findByCreatedAtAfter(LocalDateTime since);

    /**
     * Find top recommended products based on recommendation score
     */
    @Query("SELECT pa FROM ProductAnalysis pa " +
           "WHERE pa.recommendationScore >= :minScore " +
           "ORDER BY pa.recommendationScore DESC, pa.marketPotentialScore DESC")
    List<ProductAnalysis> findTopRecommendedProducts(@Param("minScore") BigDecimal minScore, 
                                                     Pageable pageable);

    /**
     * Find top recommended products (simplified version)
     */
    @Query("SELECT pa FROM ProductAnalysis pa " +
           "ORDER BY pa.recommendationScore DESC, pa.marketPotentialScore DESC")
    List<ProductAnalysis> findTopRecommendedProducts(Pageable pageable);

    /**
     * Find top recommended products using native query for better performance
     */
    @Query(value = "SELECT pa.* FROM product_analyses pa " +
                   "INNER JOIN products p ON pa.product_id = p.id " +
                   "WHERE pa.recommendation_score IS NOT NULL " +
                   "ORDER BY pa.recommendation_score DESC, pa.market_potential_score DESC " +
                   "LIMIT :limit", nativeQuery = true)
    List<ProductAnalysis> findTopRecommendedProducts(@Param("limit") int limit);

    /**
     * Find low-risk high-potential products
     */
    @Query("SELECT pa FROM ProductAnalysis pa " +
           "WHERE pa.riskAssessmentScore <= :maxRisk " +
           "AND pa.marketPotentialScore >= :minPotential " +
           "ORDER BY pa.recommendationScore DESC")
    List<ProductAnalysis> findLowRiskHighPotentialProducts(@Param("maxRisk") BigDecimal maxRisk,
                                                           @Param("minPotential") BigDecimal minPotential,
                                                           Pageable pageable);

    /**
     * Find analyses by confidence level
     */
    @Query("SELECT pa FROM ProductAnalysis pa " +
           "WHERE pa.confidenceLevel >= :minConfidence " +
           "ORDER BY pa.confidenceLevel DESC, pa.recommendationScore DESC")
    Page<ProductAnalysis> findByHighConfidence(@Param("minConfidence") BigDecimal minConfidence, 
                                              Pageable pageable);

    /**
     * Get analysis statistics
     */
    @Query("SELECT " +
           "COUNT(pa) as totalAnalyses, " +
           "AVG(pa.recommendationScore) as avgRecommendationScore, " +
           "AVG(pa.marketPotentialScore) as avgMarketPotential, " +
           "AVG(pa.competitionLevel) as avgCompetition, " +
           "AVG(pa.riskAssessmentScore) as avgRisk " +
           "FROM ProductAnalysis pa")
    Object[] getAnalysisStatistics();

    /**
     * Find analyses by category
     */
    @Query("SELECT pa FROM ProductAnalysis pa " +
           "JOIN pa.product p " +
           "WHERE p.categoryId = :categoryId " +
           "ORDER BY pa.recommendationScore DESC")
    List<ProductAnalysis> findByCategoryId(@Param("categoryId") Long categoryId, 
                                          Pageable pageable);

    /**
     * Find trending analysis results
     */
    @Query("SELECT pa FROM ProductAnalysis pa " +
           "WHERE pa.createdAt >= :since " +
           "AND pa.recommendationScore >= :minScore " +
           "ORDER BY pa.createdAt DESC, pa.recommendationScore DESC")
    List<ProductAnalysis> findTrendingAnalyses(@Param("since") LocalDateTime since,
                                              @Param("minScore") BigDecimal minScore,
                                              Pageable pageable);

    /**
     * Get daily analysis count
     */
    @Query("SELECT DATE(pa.createdAt) as analysisDate, COUNT(pa) as count " +
           "FROM ProductAnalysis pa " +
           "WHERE pa.createdAt >= :since " +
           "GROUP BY DATE(pa.createdAt) " +
           "ORDER BY analysisDate DESC")
    List<Object[]> getDailyAnalysisCount(@Param("since") LocalDateTime since);

    /**
     * Find analyses needing refresh
     */
    @Query("SELECT pa FROM ProductAnalysis pa " +
           "WHERE pa.createdAt < :threshold " +
           "ORDER BY pa.createdAt ASC")
    List<ProductAnalysis> findAnalysesNeedingRefresh(@Param("threshold") LocalDateTime threshold,
                                                     Pageable pageable);

    /**
     * Get recommendation score distribution
     */
    @Query("SELECT " +
           "FLOOR(pa.recommendationScore) as scoreRange, " +
           "COUNT(pa) as count " +
           "FROM ProductAnalysis pa " +
           "WHERE pa.recommendationScore IS NOT NULL " +
           "GROUP BY FLOOR(pa.recommendationScore) " +
           "ORDER BY scoreRange")
    List<Object[]> getRecommendationScoreDistribution();

    /**
     * Find analyses by AI model
     */
    List<ProductAnalysis> findByAiModelUsed(String aiModel);

    /**
     * Get performance metrics
     */
    @Query("SELECT " +
           "pa.aiModelUsed, " +
           "AVG(pa.analysisDurationMs) as avgDuration, " +
           "AVG(pa.confidenceLevel) as avgConfidence, " +
           "COUNT(pa) as totalAnalyses " +
           "FROM ProductAnalysis pa " +
           "WHERE pa.analysisDurationMs IS NOT NULL " +
           "GROUP BY pa.aiModelUsed")
    List<Object[]> getPerformanceMetrics();

    /**
     * Count analyses by product
     */
    @Query("SELECT p.name, COUNT(pa) " +
           "FROM ProductAnalysis pa " +
           "JOIN pa.product p " +
           "GROUP BY p.id, p.name " +
           "ORDER BY COUNT(pa) DESC")
    List<Object[]> countAnalysesByProduct();

    /**
     * Find products with multiple analyses
     */
    @Query("SELECT pa.product.id, COUNT(pa) as analysisCount " +
           "FROM ProductAnalysis pa " +
           "GROUP BY pa.product.id " +
           "HAVING COUNT(pa) > 1 " +
           "ORDER BY COUNT(pa) DESC")
    List<Object[]> findProductsWithMultipleAnalyses();

    /**
     * Get category-wise analysis summary
     */
    @Query("SELECT " +
           "p.categoryName, " +
           "COUNT(pa) as totalAnalyses, " +
           "AVG(pa.recommendationScore) as avgScore, " +
           "AVG(pa.marketPotentialScore) as avgPotential " +
           "FROM ProductAnalysis pa " +
           "JOIN pa.product p " +
           "WHERE p.categoryName IS NOT NULL " +
           "GROUP BY p.categoryName " +
           "ORDER BY AVG(pa.recommendationScore) DESC")
    List<Object[]> getCategoryAnalysisSummary();

    /**
     * Delete old analyses
     */
    @Query("DELETE FROM ProductAnalysis pa WHERE pa.createdAt < :cutoffDate")
    void deleteOldAnalyses(@Param("cutoffDate") LocalDateTime cutoffDate);
}

