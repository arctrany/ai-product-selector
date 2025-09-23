package com.ozon.tools.dto.ozon;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.math.BigDecimal;
import java.util.List;

/**
 * OZON API product details response DTO
 * 
 * @author AI Assistant
 */
public class OzonProductDetailsResponse {

    private ProductDetails result;

    public ProductDetails getResult() {
        return result;
    }

    public void setResult(ProductDetails result) {
        this.result = result;
    }

    public static class ProductDetails {
        private Long id;
        private String name;
        private String description;

        @JsonProperty("category_id")
        private Long categoryId;

        @JsonProperty("category_name")
        private String categoryName;

        private BigDecimal price;

        @JsonProperty("old_price")
        private BigDecimal oldPrice;

        @JsonProperty("currency_code")
        private String currencyCode;

        private BigDecimal rating;

        @JsonProperty("reviews_count")
        private Integer reviewsCount;

        private String brand;

        @JsonProperty("main_image")
        private String mainImage;

        private List<String> images;

        @JsonProperty("seller_id")
        private Long sellerId;

        @JsonProperty("seller_name")
        private String sellerName;

        private Integer stocks;

        @JsonProperty("is_premium")
        private Boolean isPremium;

        @JsonProperty("marketing_color")
        private String marketingColor;

        private List<Attribute> attributes;

        @JsonProperty("sales_volume")
        private Integer salesVolume;

        @JsonProperty("product_url")
        private String productUrl;

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

        public String getDescription() {
            return description;
        }

        public void setDescription(String description) {
            this.description = description;
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

        public String getBrand() {
            return brand;
        }

        public void setBrand(String brand) {
            this.brand = brand;
        }

        public String getMainImage() {
            return mainImage;
        }

        public void setMainImage(String mainImage) {
            this.mainImage = mainImage;
        }

        public List<String> getImages() {
            return images;
        }

        public void setImages(List<String> images) {
            this.images = images;
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

        public Integer getStocks() {
            return stocks;
        }

        public void setStocks(Integer stocks) {
            this.stocks = stocks;
        }

        public Boolean getIsPremium() {
            return isPremium;
        }

        public void setIsPremium(Boolean isPremium) {
            this.isPremium = isPremium;
        }

        public String getMarketingColor() {
            return marketingColor;
        }

        public void setMarketingColor(String marketingColor) {
            this.marketingColor = marketingColor;
        }

        public List<Attribute> getAttributes() {
            return attributes;
        }

        public void setAttributes(List<Attribute> attributes) {
            this.attributes = attributes;
        }

        public Integer getSalesVolume() {
            return salesVolume;
        }

        public void setSalesVolume(Integer salesVolume) {
            this.salesVolume = salesVolume;
        }

        public String getProductUrl() {
            return productUrl;
        }

        public void setProductUrl(String productUrl) {
            this.productUrl = productUrl;
        }

        @Override
        public String toString() {
            return "ProductDetails{" +
                    "id=" + id +
                    ", name='" + name + '\'' +
                    ", categoryName='" + categoryName + '\'' +
                    ", price=" + price +
                    ", rating=" + rating +
                    ", stocks=" + stocks +
                    '}';
        }
    }

    public static class Attribute {
        private String name;
        private String value;

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public String getValue() {
            return value;
        }

        public void setValue(String value) {
            this.value = value;
        }

        @Override
        public String toString() {
            return "Attribute{" +
                    "name='" + name + '\'' +
                    ", value='" + value + '\'' +
                    '}';
        }
    }
}
