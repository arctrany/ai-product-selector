package com.ozon.tools.dto.ozon;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.math.BigDecimal;
import java.util.List;

/**
 * OZON API product response DTO
 * 
 * @author AI Assistant
 */
public class OzonProductResponse {

    private Result result;

    public Result getResult() {
        return result;
    }

    public void setResult(Result result) {
        this.result = result;
    }

    public static class Result {
        private List<ProductItem> items;
        private int total;
        private boolean hasNext;

        @JsonProperty("has_next")
        public boolean isHasNext() {
            return hasNext;
        }

        public void setHasNext(boolean hasNext) {
            this.hasNext = hasNext;
        }

        public List<ProductItem> getItems() {
            return items;
        }

        public void setItems(List<ProductItem> items) {
            this.items = items;
        }

        public int getTotal() {
            return total;
        }

        public void setTotal(int total) {
            this.total = total;
        }
    }

    public static class ProductItem {
        private Long id;
        private String name;
        private BigDecimal price;

        @JsonProperty("old_price")
        private BigDecimal oldPrice;

        @JsonProperty("currency_code")
        private String currencyCode;

        private BigDecimal rating;

        @JsonProperty("reviews_count")
        private Integer reviewsCount;

        @JsonProperty("main_image")
        private String mainImage;

        @JsonProperty("category_id")
        private Long categoryId;

        @JsonProperty("category_name")
        private String categoryName;

        private String brand;

        @JsonProperty("seller_id")
        private Long sellerId;

        @JsonProperty("seller_name")
        private String sellerName;

        @JsonProperty("is_premium")
        private Boolean isPremium;

        @JsonProperty("in_stock")
        private Boolean inStock;

        // Getters and Setters
        public Long getId() {
            return id;
        }

        public void setId(Long id) {
            this.id = id;
        }

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public BigDecimal getPrice() {
            return price;
        }

        public void setPrice(BigDecimal price) {
            this.price = price;
        }

        public BigDecimal getOldPrice() {
            return oldPrice;
        }

        public void setOldPrice(BigDecimal oldPrice) {
            this.oldPrice = oldPrice;
        }

        public String getCurrencyCode() {
            return currencyCode;
        }

        public void setCurrencyCode(String currencyCode) {
            this.currencyCode = currencyCode;
        }

        public BigDecimal getRating() {
            return rating;
        }

        public void setRating(BigDecimal rating) {
            this.rating = rating;
        }

        public Integer getReviewsCount() {
            return reviewsCount;
        }

        public void setReviewsCount(Integer reviewsCount) {
            this.reviewsCount = reviewsCount;
        }

        public String getMainImage() {
            return mainImage;
        }

        public void setMainImage(String mainImage) {
            this.mainImage = mainImage;
        }

        public Long getCategoryId() {
            return categoryId;
        }

        public void setCategoryId(Long categoryId) {
            this.categoryId = categoryId;
        }

        public String getCategoryName() {
            return categoryName;
        }

        public void setCategoryName(String categoryName) {
            this.categoryName = categoryName;
        }

        public String getBrand() {
            return brand;
        }

        public void setBrand(String brand) {
            this.brand = brand;
        }

        public Long getSellerId() {
            return sellerId;
        }

        public void setSellerId(Long sellerId) {
            this.sellerId = sellerId;
        }

        public String getSellerName() {
            return sellerName;
        }

        public void setSellerName(String sellerName) {
            this.sellerName = sellerName;
        }

        public Boolean getIsPremium() {
            return isPremium;
        }

        public void setIsPremium(Boolean isPremium) {
            this.isPremium = isPremium;
        }

        public Boolean getInStock() {
            return inStock;
        }

        public void setInStock(Boolean inStock) {
            this.inStock = inStock;
        }

        @Override
        public String toString() {
            return "ProductItem{" +
                    "id=" + id +
                    ", name='" + name + '\'' +
                    ", price=" + price +
                    ", rating=" + rating +
                    ", reviewsCount=" + reviewsCount +
                    ", inStock=" + inStock +
                    '}';
        }
    }
}
