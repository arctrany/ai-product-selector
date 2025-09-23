package com.ozon.tools.repository;

import com.ozon.tools.domain.entity.PriceHistory;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Repository for PriceHistory entity
 * 
 * @author AI Assistant
 */
@Repository
public interface PriceHistoryRepository extends JpaRepository<PriceHistory, Long> {

    /**
     * Find price history for a product
     */
    List<PriceHistory> findByProductIdOrderByRecordedAtDesc(Long productId);

    /**
     * Find recent price changes
     */
    @Query("SELECT ph FROM PriceHistory ph WHERE ph.recordedAt >= :since ORDER BY ph.recordedAt DESC")
    List<PriceHistory> findRecentPriceChanges(@Param("since") LocalDateTime since);

    /**
     * Find price history by product and date range
     */
    @Query("SELECT ph FROM PriceHistory ph WHERE ph.product.id = :productId " +
           "AND ph.recordedAt BETWEEN :startDate AND :endDate " +
           "ORDER BY ph.recordedAt ASC")
    List<PriceHistory> findByProductAndDateRange(@Param("productId") Long productId,
                                                @Param("startDate") LocalDateTime startDate,
                                                @Param("endDate") LocalDateTime endDate);

    /**
     * Delete old price history records
     */
    @Query("DELETE FROM PriceHistory ph WHERE ph.recordedAt < :cutoffDate")
    void deleteOldRecords(@Param("cutoffDate") LocalDateTime cutoffDate);
}
