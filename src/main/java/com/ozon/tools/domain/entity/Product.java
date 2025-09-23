package com.ozon.tools.domain.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Set;

/**
 * Product entity representing OZON marketplace products
 * 
 * @author AI Assistant
 */
@Entity
@Table(name = "products", indexes = {
    @Index(name = "idx_product_ozon_id", columnList = "ozonId"),
    @Index(name = "idx_product_category", columnList = "categoryId"),
    @Index(name = "idx_product_updated", columnList = "lastUpdated")
})
public class Product {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "ozon_id", unique = true, nullable = false)
    @NotNull
    private Long ozonId;

    @Column(name = "name", nullable = false, length = 500)
    @NotBlank
    @Size(max = 500)
    private String name;

    @Column(name = "description", columnDefinition = "TEXT")
    private String description;

    @Column(name = "category_id")
    private Long categoryId;

    @Column(name = "category_name", length = 200)
    @Size(max = 200)
    private String categoryName;

    @Column(name = "price", precision = 10, scale = 2)
    @DecimalMin(value = "0.0", inclusive = false)
    private BigDecimal price;

    @Column(name = "old_price", precision = 10, scale = 2)
    @DecimalMin(value = "0.0", inclusive = false)
    private BigDecimal oldPrice;

    @Column(name = "currency", length = 3)
    @Size(max = 3)
    private String currency = "RUB";

    @Column(name = "rating", precision = 3, scale = 2)
    @DecimalMin(value = "0.0")
    @DecimalMax(value = "5.0")
    private BigDecimal rating;

    @Column(name = "reviews_count")
    @Min(0)
    private Integer reviewsCount = 0;

    @Column(name = "sales_volume")
    @Min(0)
    private Integer salesVolume = 0;

    @Column(name = "stock_quantity")
    @Min(0)
    private Integer stockQuantity = 0;

    @Column(name = "brand", length = 100)
    @Size(max = 100)
    private String brand;

    @Column(name = "seller_id")
    private Long sellerId;

    @Column(name = "seller_name", length = 200)
    @Size(max = 200)
    private String sellerName;

    @Column(name = "image_url", length = 1000)
    @Size(max = 1000)
    private String imageUrl;

    @Column(name = "product_url", length = 1000)
    @Size(max = 1000)
    private String productUrl;

    @Enumerated(EnumType.STRING)
    @Column(name = "status")
    private ProductStatus status = ProductStatus.ACTIVE;

    @Column(name = "is_premium")
    private Boolean isPremium = false;

    @Column(name = "has_discount")
    private Boolean hasDiscount = false;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "last_updated", nullable = false)
    private LocalDateTime lastUpdated;

    @OneToMany(mappedBy = "product", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private Set<ProductAnalysis> analyses;

    @OneToMany(mappedBy = "product", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private Set<PriceHistory> priceHistory;

    // Constructors
    public Product() {}

    public Product(Long ozonId, String name) {
        this.ozonId = ozonId;
        this.name = name;
    }

    // Getters and Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getOzonId() {
        return ozonId;
    }

    public void setOzonId(Long ozonId) {
        this.ozonId = ozonId;
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

    public String getCurrency() {
        return currency;
    }

    public void setCurrency(String currency) {
        this.currency = currency;
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

    public Integer getSalesVolume() {
        return salesVolume;
    }

    public void setSalesVolume(Integer salesVolume) {
        this.salesVolume = salesVolume;
    }

    public Integer getStockQuantity() {
        return stockQuantity;
    }

    public void setStockQuantity(Integer stockQuantity) {
        this.stockQuantity = stockQuantity;
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

    public String getImageUrl() {
        return imageUrl;
    }

    public void setImageUrl(String imageUrl) {
        this.imageUrl = imageUrl;
    }

    public String getProductUrl() {
        return productUrl;
    }

    public void setProductUrl(String productUrl) {
        this.productUrl = productUrl;
    }

    public ProductStatus getStatus() {
        return status;
    }

    public void setStatus(ProductStatus status) {
        this.status = status;
    }

    public Boolean getIsPremium() {
        return isPremium;
    }

    public void setIsPremium(Boolean isPremium) {
        this.isPremium = isPremium;
    }

    public Boolean getHasDiscount() {
        return hasDiscount;
    }

    public void setHasDiscount(Boolean hasDiscount) {
        this.hasDiscount = hasDiscount;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getLastUpdated() {
        return lastUpdated;
    }

    public void setLastUpdated(LocalDateTime lastUpdated) {
        this.lastUpdated = lastUpdated;
    }

    public Set<ProductAnalysis> getAnalyses() {
        return analyses;
    }

    public void setAnalyses(Set<ProductAnalysis> analyses) {
        this.analyses = analyses;
    }

    public Set<PriceHistory> getPriceHistory() {
        return priceHistory;
    }

    public void setPriceHistory(Set<PriceHistory> priceHistory) {
        this.priceHistory = priceHistory;
    }

    // Business methods
    public BigDecimal getDiscountPercentage() {
        if (oldPrice != null && price != null && oldPrice.compareTo(BigDecimal.ZERO) > 0) {
            return oldPrice.subtract(price)
                    .divide(oldPrice, 4, BigDecimal.ROUND_HALF_UP)
                    .multiply(BigDecimal.valueOf(100));
        }
        return BigDecimal.ZERO;
    }

    public boolean isOnSale() {
        return hasDiscount != null && hasDiscount && 
               oldPrice != null && 
               price != null && 
               oldPrice.compareTo(price) > 0;
    }

    @Override
    public String toString() {
        return "Product{" +
                "id=" + id +
                ", ozonId=" + ozonId +
                ", name='" + name + '\'' +
                ", categoryName='" + categoryName + '\'' +
                ", price=" + price +
                ", rating=" + rating +
                ", reviewsCount=" + reviewsCount +
                ", status=" + status +
                '}';
    }

    /**
     * Product status enumeration
     */
    public enum ProductStatus {
        ACTIVE,
        INACTIVE,
        OUT_OF_STOCK,
        DISCONTINUED,
        PENDING_REVIEW
    }
}
