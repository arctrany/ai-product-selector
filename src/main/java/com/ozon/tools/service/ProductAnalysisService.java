package com.ozon.tools.service;

import com.alibaba.cloud.ai.dashscope.chat.DashScopeChatModel;
import com.ozon.tools.domain.entity.Product;
import com.ozon.tools.domain.entity.ProductAnalysis;
import com.ozon.tools.repository.ProductAnalysisRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * Service for AI-powered product analysis using Spring AI Alibaba
 * 
 * @author AI Assistant
 */
@Service
@Transactional
public class ProductAnalysisService {

    private static final Logger logger = LoggerFactory.getLogger(ProductAnalysisService.class);

    private final DashScopeChatModel chatModel;
    private final ProductAnalysisRepository analysisRepository;
    private final ObjectMapper objectMapper;
    private final String promptTemplate;

    public ProductAnalysisService(DashScopeChatModel chatModel,
                                ProductAnalysisRepository analysisRepository,
                                ObjectMapper objectMapper,
                                @Value("${product.analysis.ai.prompt-template}") String promptTemplate) {
        this.chatModel = chatModel;
        this.analysisRepository = analysisRepository;
        this.objectMapper = objectMapper;
        this.promptTemplate = promptTemplate;
    }

    /**
     * Analyze a product using AI
     * 
     * @param product Product to analyze
     * @return ProductAnalysis with AI insights
     */
    public CompletableFuture<ProductAnalysis> analyzeProduct(Product product) {
        return CompletableFuture.supplyAsync(() -> {
            long startTime = System.currentTimeMillis();
            logger.info("Starting AI analysis for product: {} (ID: {})", product.getName(), product.getId());

            try {
                // Check if recent analysis exists
                ProductAnalysis existingAnalysis = analysisRepository
                        .findTopByProductIdOrderByCreatedAtDesc(product.getId());
                
                if (existingAnalysis != null && 
                    existingAnalysis.getCreatedAt().isAfter(LocalDateTime.now().minusHours(24))) {
                    logger.info("Using existing analysis for product: {}", product.getName());
                    return existingAnalysis;
                }

                // Generate AI analysis
                String prompt = buildAnalysisPrompt(product);
                UserMessage userMessage = new UserMessage(prompt);
                Prompt aiPrompt = new Prompt(userMessage);

                String aiResponse = chatModel.call(aiPrompt).getResult().getOutput().getText();
                logger.debug("AI analysis response: {}", aiResponse);

                // Parse AI response
                ProductAnalysis analysis = parseAiResponse(product, aiResponse);
                analysis.setAnalysisDurationMs(System.currentTimeMillis() - startTime);
                analysis.setAiModelUsed("qwen-plus");

                // Save analysis
                ProductAnalysis savedAnalysis = analysisRepository.save(analysis);
                logger.info("Completed AI analysis for product: {} in {}ms", 
                           product.getName(), analysis.getAnalysisDurationMs());

                return savedAnalysis;

            } catch (Exception e) {
                logger.error("Error analyzing product {}: {}", product.getName(), e.getMessage(), e);
                return createFallbackAnalysis(product, System.currentTimeMillis() - startTime);
            }
        });
    }

    /**
     * Batch analyze multiple products
     * 
     * @param products List of products to analyze
     * @return CompletableFuture with list of analyses
     */
    public CompletableFuture<List<ProductAnalysis>> batchAnalyzeProducts(List<Product> products) {
        logger.info("Starting batch analysis for {} products", products.size());

        List<CompletableFuture<ProductAnalysis>> futures = products.stream()
                .map(this::analyzeProduct)
                .toList();

        return CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]))
                .thenApply(v -> futures.stream()
                        .map(CompletableFuture::join)
                        .toList());
    }

    /**
     * Get analysis summary for multiple products
     * 
     * @param productIds List of product IDs
     * @return Market analysis summary
     */
    public CompletableFuture<String> generateMarketAnalysisSummary(List<Long> productIds) {
        return CompletableFuture.supplyAsync(() -> {
            logger.info("Generating market analysis summary for {} products", productIds.size());

            try {
                List<ProductAnalysis> analyses = analysisRepository.findByProductIdIn(productIds);
                
                String summaryPrompt = buildMarketSummaryPrompt(analyses);
                UserMessage userMessage = new UserMessage(summaryPrompt);
                Prompt aiPrompt = new Prompt(userMessage);

                String summary = chatModel.call(aiPrompt).getResult().getOutput().getText();
                logger.info("Generated market analysis summary");
                return summary;

            } catch (Exception e) {
                logger.error("Error generating market analysis summary: {}", e.getMessage(), e);
                return "Error generating market analysis summary. Please try again later.";
            }
        });
    }

    /**
     * Find top recommended products based on analysis scores
     * 
     * @param limit Number of products to return
     * @return List of top recommended products
     */
    public List<ProductAnalysis> getTopRecommendedProducts(int limit) {
        logger.info("Fetching top {} recommended products", limit);
        return analysisRepository.findTopRecommendedProducts(limit);
    }

    /**
     * Get analysis trends
     * 
     * @param days Number of days to analyze
     * @return Analysis trends data
     */
    public CompletableFuture<String> getAnalysisTrends(int days) {
        return CompletableFuture.supplyAsync(() -> {
            logger.info("Analyzing trends for last {} days", days);

            try {
                LocalDateTime since = LocalDateTime.now().minusDays(days);
                List<ProductAnalysis> recentAnalyses = analysisRepository.findByCreatedAtAfter(since);

                String trendsPrompt = buildTrendsPrompt(recentAnalyses, days);
                UserMessage userMessage = new UserMessage(trendsPrompt);
                Prompt aiPrompt = new Prompt(userMessage);

                String trends = chatModel.call(aiPrompt).getResult().getOutput().getText();
                logger.info("Generated analysis trends");
                return trends;

            } catch (Exception e) {
                logger.error("Error generating analysis trends: {}", e.getMessage(), e);
                return "Error generating trends analysis. Please try again later.";
            }
        });
    }

    /**
     * Build analysis prompt for AI
     */
    private String buildAnalysisPrompt(Product product) {
        return promptTemplate
                .replace("{productName}", product.getName() != null ? product.getName() : "Unknown")
                .replace("{category}", product.getCategoryName() != null ? product.getCategoryName() : "Unknown")
                .replace("{price}", product.getPrice() != null ? product.getPrice().toString() : "0")
                .replace("{salesVolume}", product.getSalesVolume() != null ? product.getSalesVolume().toString() : "0")
                .replace("{rating}", product.getRating() != null ? product.getRating().toString() : "0")
                .replace("{reviewsCount}", product.getReviewsCount() != null ? product.getReviewsCount().toString() : "0");
    }

    /**
     * Parse AI response into ProductAnalysis
     */
    private ProductAnalysis parseAiResponse(Product product, String aiResponse) {
        ProductAnalysis analysis = new ProductAnalysis(product);
        
        try {
            // Try to parse as JSON
            JsonNode responseJson = objectMapper.readTree(aiResponse);
            
            // Extract scores
            if (responseJson.has("recommendation_score")) {
                analysis.setRecommendationScore(new BigDecimal(responseJson.get("recommendation_score").asText()));
            }
            if (responseJson.has("market_potential")) {
                analysis.setMarketPotentialScore(new BigDecimal(responseJson.get("market_potential").asText()));
            }
            if (responseJson.has("competition_level")) {
                analysis.setCompetitionLevel(new BigDecimal(responseJson.get("competition_level").asText()));
            }
            if (responseJson.has("risk_score")) {
                analysis.setRiskAssessmentScore(new BigDecimal(responseJson.get("risk_score").asText()));
            }
            if (responseJson.has("profit_margin")) {
                analysis.setProfitMarginEstimation(new BigDecimal(responseJson.get("profit_margin").asText()));
            }
            
            // Extract text insights
            if (responseJson.has("summary")) {
                analysis.setAnalysisSummary(responseJson.get("summary").asText());
            }
            if (responseJson.has("key_insights")) {
                analysis.setKeyInsights(responseJson.get("key_insights").asText());
            }
            if (responseJson.has("risks")) {
                analysis.setRisksIdentified(responseJson.get("risks").asText());
            }
            if (responseJson.has("opportunities")) {
                analysis.setOpportunities(responseJson.get("opportunities").asText());
            }
            if (responseJson.has("recommendations")) {
                analysis.setRecommendedActions(responseJson.get("recommendations").asText());
            }

            analysis.setConfidenceLevel(BigDecimal.valueOf(0.85));

        } catch (Exception e) {
            logger.warn("Failed to parse AI response as JSON, using fallback parsing: {}", e.getMessage());
            
            // Fallback: extract basic information from text
            analysis.setAnalysisSummary(aiResponse);
            analysis.setRecommendationScore(extractScoreFromText(aiResponse, "recommendation"));
            analysis.setMarketPotentialScore(extractScoreFromText(aiResponse, "market potential"));
            analysis.setCompetitionLevel(extractScoreFromText(aiResponse, "competition"));
            analysis.setRiskAssessmentScore(extractScoreFromText(aiResponse, "risk"));
            analysis.setConfidenceLevel(BigDecimal.valueOf(0.60));
        }

        return analysis;
    }

    /**
     * Extract score from text using pattern matching
     */
    private BigDecimal extractScoreFromText(String text, String scoreName) {
        try {
            String pattern = scoreName + ".*?(\\d+\\.?\\d*)";
            java.util.regex.Pattern p = java.util.regex.Pattern.compile(pattern, java.util.regex.Pattern.CASE_INSENSITIVE);
            java.util.regex.Matcher m = p.matcher(text);
            if (m.find()) {
                return new BigDecimal(m.group(1));
            }
        } catch (Exception e) {
            logger.debug("Could not extract {} score from text", scoreName);
        }
        return BigDecimal.valueOf(5.0); // Default middle score
    }

    /**
     * Create fallback analysis when AI analysis fails
     */
    private ProductAnalysis createFallbackAnalysis(Product product, long duration) {
        ProductAnalysis analysis = new ProductAnalysis(product);
        analysis.setRecommendationScore(BigDecimal.valueOf(5.0));
        analysis.setMarketPotentialScore(BigDecimal.valueOf(5.0));
        analysis.setCompetitionLevel(BigDecimal.valueOf(5.0));
        analysis.setRiskAssessmentScore(BigDecimal.valueOf(5.0));
        analysis.setAnalysisSummary("Analysis temporarily unavailable. Basic scoring applied.");
        analysis.setConfidenceLevel(BigDecimal.valueOf(0.30));
        analysis.setAnalysisDurationMs(duration);
        analysis.setAiModelUsed("fallback");
        
        return analysisRepository.save(analysis);
    }

    /**
     * Build market summary prompt
     */
    private String buildMarketSummaryPrompt(List<ProductAnalysis> analyses) {
        StringBuilder prompt = new StringBuilder();
        prompt.append("Analyze the following product analyses and provide a market summary:\n\n");
        
        for (ProductAnalysis analysis : analyses) {
            prompt.append(String.format("Product: %s, Score: %.1f, Market Potential: %.1f, Competition: %.1f\n",
                    analysis.getProduct().getName(),
                    analysis.getRecommendationScore(),
                    analysis.getMarketPotentialScore(),
                    analysis.getCompetitionLevel()));
        }
        
        prompt.append("\nProvide insights on market trends, opportunities, and recommendations.");
        return prompt.toString();
    }

    /**
     * Build trends analysis prompt
     */
    private String buildTrendsPrompt(List<ProductAnalysis> analyses, int days) {
        StringBuilder prompt = new StringBuilder();
        prompt.append(String.format("Analyze product selection trends over the last %d days based on %d analyses:\n\n", 
                                   days, analyses.size()));
        
        // Group by date and calculate averages
        analyses.stream()
                .collect(java.util.stream.Collectors.groupingBy(
                        a -> a.getCreatedAt().toLocalDate(),
                        java.util.stream.Collectors.averagingDouble(
                                a -> a.getRecommendationScore().doubleValue())))
                .forEach((date, avgScore) -> 
                        prompt.append(String.format("Date: %s, Avg Score: %.2f\n", date, avgScore)));
        
        prompt.append("\nIdentify trends, patterns, and provide market insights.");
        return prompt.toString();
    }
}
