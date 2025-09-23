package com.ozon.tools.dto.ozon;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Size;

/**
 * OZON API search request DTO
 * 
 * @author AI Assistant
 */
public class OzonSearchRequest {

    @Size(max = 200, message = "Query must not exceed 200 characters")
    private String query;

    private Long categoryId;

    @Min(value = 1, message = "Limit must be at least 1")
    @Max(value = 1000, message = "Limit must not exceed 1000")
    private Integer limit = 50;

    @Min(value = 0, message = "Offset must not be negative")
    private Integer offset = 0;

    private String sort = "popularity"; // popularity, price_asc, price_desc, rating, new

    private PriceRange priceRange;

    private Boolean hasDiscount;

    private Double minRating;

    private Integer minReviewsCount;

    private String brand;

    private Boolean inStock = true;

    // Constructors
    public OzonSearchRequest() {}

    public OzonSearchRequest(String query, Integer limit) {
        this.query = query;
        this.limit = limit;
    }

    // Getters and Setters
    public String getQuery() {
        return query;
    }

    public void setQuery(String query) {
        this.query = query;
    }

    public Long getCategoryId() {
        return categoryId;
    }

    public void setCategoryId(Long categoryId) {
        this.categoryId = categoryId;
    }

    public Integer getLimit() {
        return limit;
    }

    public void setLimit(Integer limit) {
        this.limit = limit;
    }

    public Integer getOffset() {
        return offset;
    }

    public void setOffset(Integer offset) {
        this.offset = offset;
    }

    public String getSort() {
        return sort;
    }

    public void setSort(String sort) {
        this.sort = sort;
    }

    public PriceRange getPriceRange() {
        return priceRange;
    }

    public void setPriceRange(PriceRange priceRange) {
        this.priceRange = priceRange;
    }

    public Boolean getHasDiscount() {
        return hasDiscount;
    }

    public void setHasDiscount(Boolean hasDiscount) {
        this.hasDiscount = hasDiscount;
    }

    public Double getMinRating() {
        return minRating;
    }

    public void setMinRating(Double minRating) {
        this.minRating = minRating;
    }

    public Integer getMinReviewsCount() {
        return minReviewsCount;
    }

    public void setMinReviewsCount(Integer minReviewsCount) {
        this.minReviewsCount = minReviewsCount;
    }

    public String getBrand() {
        return brand;
    }

    public void setBrand(String brand) {
        this.brand = brand;
    }

    public Boolean getInStock() {
        return inStock;
    }

    public void setInStock(Boolean inStock) {
        this.inStock = inStock;
    }

    @Override
    public String toString() {
        return "OzonSearchRequest{" +
                "query='" + query + '\'' +
                ", categoryId=" + categoryId +
                ", limit=" + limit +
                ", offset=" + offset +
                ", sort='" + sort + '\'' +
                ", hasDiscount=" + hasDiscount +
                ", minRating=" + minRating +
                ", inStock=" + inStock +
                '}';
    }

    /**
     * Price range filter
     */
    public static class PriceRange {
        private Double min;
        private Double max;

        public PriceRange() {}

        public PriceRange(Double min, Double max) {
            this.min = min;
            this.max = max;
        }

        public Double getMin() {
            return min;
        }

        public void setMin(Double min) {
            this.min = min;
        }

        public Double getMax() {
            return max;
        }

        public void setMax(Double max) {
            this.max = max;
        }

        @Override
        public String toString() {
            return "PriceRange{" +
                    "min=" + min +
                    ", max=" + max +
                    '}';
        }
    }
}
