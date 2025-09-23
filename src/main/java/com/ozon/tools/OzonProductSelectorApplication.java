package com.ozon.tools;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * OZON Product Selector Application
 * 
 * AI-powered product selection tool for OZON marketplace using Spring AI Alibaba
 * 
 * @author AI Assistant
 * @version 1.0.0
 */
@SpringBootApplication
@EnableCaching
@EnableAsync
@EnableScheduling
public class OzonProductSelectorApplication {

    public static void main(String[] args) {
        SpringApplication.run(OzonProductSelectorApplication.class, args);
    }
}
