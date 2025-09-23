package com.ozon.tools.domain.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import org.hibernate.annotations.CreationTimestamp;
import com.fasterxml.jackson.annotation.JsonIgnore;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * Product analysis entity containing AI-generated insights
 * 
 * @author AI Assistant
 */
@Entity
@Table(name = "product_analyses", indexes = {
    @Index(name = "idx_analysis_product", columnList = "product_id"),
    @Index(name = "idx_analysis_score", columnList = "recommendationScore"),
    @Index(name = "idx_analysis_created", columnList = "createdAt")
})
public class ProductAnalysis {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "product_id", nullable = false)
    @JsonIgnore
    private Product product;

    @Column(name = "analysis_version", length = 20)
    @Size(max = 20)
    private String analysisVersion = "1.0";

    @Column(name = "recommendation_score", precision = 3, scale = 1)
    @DecimalMin(value = "0.0")
    @DecimalMax(value = "10.0")
    private BigDecimal recommendationScore;

    @Column(name = "market_potential_score", precision = 3, scale = 1)
    @DecimalMin(value = "0.0")
    @DecimalMax(value = "10.0")
    private BigDecimal marketPotentialScore;

    @Column(name = "competition_level", precision = 3, scale = 1)
    @DecimalMin(value = "0.0")
    @DecimalMax(value = "10.0")
    private BigDecimal competitionLevel;

    @Column(name = "profit_margin_estimation", precision = 5, scale = 2)
    private BigDecimal profitMarginEstimation;

    @Column(name = "risk_assessment_score", precision = 3, scale = 1)
    @DecimalMin(value = "0.0")
    @DecimalMax(value = "10.0")
    private BigDecimal riskAssessmentScore;

    @Enumerated(EnumType.STRING)
    @Column(name = "seasonality_trend")
    private SeasonalityTrend seasonalityTrend;

    @Enumerated(EnumType.STRING)
    @Column(name = "market_trend")
    private MarketTrend marketTrend;

    @Column(name = "analysis_summary", columnDefinition = "TEXT")
    private String analysisSummary;

    @Column(name = "key_insights", columnDefinition = "TEXT")
    private String keyInsights;

    @Column(name = "risks_identified", columnDefinition = "TEXT")
    private String risksIdentified;

    @Column(name = "opportunities", columnDefinition = "TEXT")
    private String opportunities;

    @Column(name = "recommended_actions", columnDefinition = "TEXT")
    private String recommendedActions;

    @Column(name = "ai_model_used", length = 50)
    @Size(max = 50)
    private String aiModelUsed;

    @Column(name = "confidence_level", precision = 3, scale = 2)
    @DecimalMin(value = "0.0")
    @DecimalMax(value = "1.0")
    private BigDecimal confidenceLevel;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "analysis_duration_ms")
    private Long analysisDurationMs;

    // Constructors
    public ProductAnalysis() {}

    public ProductAnalysis(Product product) {
        this.product = product;
    }

    // Getters and Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Product getProduct() {
        return product;
    }

    public void setProduct(Product product) {
        this.product = product;
    }

    public String getAnalysisVersion() {
        return analysisVersion;
    }

    public void setAnalysisVersion(String analysisVersion) {
        this.analysisVersion = analysisVersion;
    }

    public BigDecimal getRecommendationScore() {
        return recommendationScore;
    }

    public void setRecommendationScore(BigDecimal recommendationScore) {
        this.recommendationScore = recommendationScore;
    }

    public BigDecimal getMarketPotentialScore() {
        return marketPotentialScore;
    }

    public void setMarketPotentialScore(BigDecimal marketPotentialScore) {
        this.marketPotentialScore = marketPotentialScore;
    }

    public BigDecimal getCompetitionLevel() {
        return competitionLevel;
    }

    public void setCompetitionLevel(BigDecimal competitionLevel) {
        this.competitionLevel = competitionLevel;
    }

    public BigDecimal getProfitMarginEstimation() {
        return profitMarginEstimation;
    }

    public void setProfitMarginEstimation(BigDecimal profitMarginEstimation) {
        this.profitMarginEstimation = profitMarginEstimation;
    }

    public BigDecimal getRiskAssessmentScore() {
        return riskAssessmentScore;
    }

    public void setRiskAssessmentScore(BigDecimal riskAssessmentScore) {
        this.riskAssessmentScore = riskAssessmentScore;
    }

    public SeasonalityTrend getSeasonalityTrend() {
        return seasonalityTrend;
    }

    public void setSeasonalityTrend(SeasonalityTrend seasonalityTrend) {
        this.seasonalityTrend = seasonalityTrend;
    }

    public MarketTrend getMarketTrend() {
        return marketTrend;
    }

    public void setMarketTrend(MarketTrend marketTrend) {
        this.marketTrend = marketTrend;
    }

    public String getAnalysisSummary() {
        return analysisSummary;
    }

    public void setAnalysisSummary(String analysisSummary) {
        this.analysisSummary = analysisSummary;
    }

    public String getKeyInsights() {
        return keyInsights;
    }

    public void setKeyInsights(String keyInsights) {
        this.keyInsights = keyInsights;
    }

    public String getRisksIdentified() {
        return risksIdentified;
    }

    public void setRisksIdentified(String risksIdentified) {
        this.risksIdentified = risksIdentified;
    }

    public String getOpportunities() {
        return opportunities;
    }

    public void setOpportunities(String opportunities) {
        this.opportunities = opportunities;
    }

    public String getRecommendedActions() {
        return recommendedActions;
    }

    public void setRecommendedActions(String recommendedActions) {
        this.recommendedActions = recommendedActions;
    }

    public String getAiModelUsed() {
        return aiModelUsed;
    }

    public void setAiModelUsed(String aiModelUsed) {
        this.aiModelUsed = aiModelUsed;
    }

    public BigDecimal getConfidenceLevel() {
        return confidenceLevel;
    }

    public void setConfidenceLevel(BigDecimal confidenceLevel) {
        this.confidenceLevel = confidenceLevel;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public Long getAnalysisDurationMs() {
        return analysisDurationMs;
    }

    public void setAnalysisDurationMs(Long analysisDurationMs) {
        this.analysisDurationMs = analysisDurationMs;
    }

    // Business methods
    public boolean isHighlyRecommended() {
        return recommendationScore != null && 
               recommendationScore.compareTo(BigDecimal.valueOf(8.0)) >= 0;
    }

    public boolean isLowRisk() {
        return riskAssessmentScore != null && 
               riskAssessmentScore.compareTo(BigDecimal.valueOf(3.0)) <= 0;
    }

    @Override
    public String toString() {
        return "ProductAnalysis{" +
                "id=" + id +
                ", recommendationScore=" + recommendationScore +
                ", marketPotentialScore=" + marketPotentialScore +
                ", competitionLevel=" + competitionLevel +
                ", riskAssessmentScore=" + riskAssessmentScore +
                ", createdAt=" + createdAt +
                '}';
    }

    /**
     * Seasonality trend enumeration
     */
    public enum SeasonalityTrend {
        STABLE,
        SEASONAL_HIGH,
        SEASONAL_LOW,
        GROWING,
        DECLINING,
        UNKNOWN
    }

    /**
     * Market trend enumeration
     */
    public enum MarketTrend {
        BULLISH,
        BEARISH,
        STABLE,
        VOLATILE,
        EMERGING,
        DECLINING,
        UNKNOWN
    }
}
