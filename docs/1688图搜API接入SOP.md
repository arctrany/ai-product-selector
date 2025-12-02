# 1688跨境相似商品搜索API接入SOP

> **API**: `alibaba.cross.similar.offer.search`  
> **技术栈**: Java 21 + Spring Boot 3.x + Maven  
> **部署环境**: 阿里云ECS (无域名)

---

## 一、前期准备

### 1.1 注册1688开放平台

1. 访问 https://open.1688.com 注册账号
2. 完成企业实名认证(绑定企业支付宝)
3. 等待审核(1-3个工作日)

### 1.2 创建应用

1. 登录后进入"控制台" → "应用管理" → "创建应用"
2. 填写应用信息:
   - 应用名称: 跨境商品图搜服务
   - 应用类型: 自用型应用
   - 应用描述: 用于跨境电商货源匹配
3. 提交审核,获得 **App Key** 和 **App Secret**

### 1.3 申请API权限

1. 在应用详情页点击"API权限管理"
2. 申请接口: `com.alibaba.linkplus:alibaba.cross.similar.offer.search`
3. 填写业务场景: 跨境电商货源匹配和选品
4. 等待审核(1-3个工作日)

---

## 二、ECS环境配置

### 2.1 登录ECS并安装Java

```bash
ssh root@your-ecs-ip

# 安装Java 17
yum install -y java-21-openjdk java-21-openjdk-devel
java -version
```

### 2.2 安装Maven

```bash
cd /opt
wget https://dlcdn.apache.org/maven/maven-3/3.9.6/binaries/apache-maven-3.9.6-bin.tar.gz
tar -xzf apache-maven-3.9.6-bin.tar.gz
ln -s /opt/apache-maven-3.9.6 /opt/maven

echo 'export MAVEN_HOME=/opt/maven' >> /etc/profile
echo 'export PATH=$MAVEN_HOME/bin:$PATH' >> /etc/profile
source /etc/profile

mvn -version
```

### 2.3 安装Redis(可选)

**选项1: 使用Redis缓存Token(推荐)**
```bash
yum install -y redis
systemctl start redis
systemctl enable redis
redis-cli ping  # 应返回PONG
```

**选项2: 最小化部署(不使用Redis)**
- 使用内存缓存Token
- 适合单机部署、低并发场景
- 重启服务后Token需重新获取

---

## 三、Java代理服务开发

### 3.1 项目结构

```
image-search-proxy/
├── pom.xml
├── src/main/
│   ├── java/com/company/imagesearch/
│   │   ├── ImageSearchApplication.java
│   │   ├── controller/ImageSearchController.java
│   │   ├── service/
│   │   │   ├── TokenManager.java
│   │   │   ├── ImageUploadService.java
│   │   │   └── CrossBorderSearchService.java
│   │   └── util/SignatureUtil.java
│   └── resources/application.yml
└── target/image-search-proxy-1.0.0.jar
```

### 3.2 pom.xml

```xml
<project>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
    </parent>

    <groupId>com.company</groupId>
    <artifactId>image-search-proxy</artifactId>
    <version>1.0.0</version>

    <properties>
        <java.version>17</java.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <!-- Redis可选: 最小化部署可注释掉 -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-redis</artifactId>
            <optional>true</optional>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
        </dependency>
        <dependency>
            <groupId>com.aliyun.oss</groupId>
            <artifactId>aliyun-sdk-oss</artifactId>
            <version>3.17.1</version>
        </dependency>
        <dependency>
            <groupId>cn.hutool</groupId>
            <artifactId>hutool-all</artifactId>
            <version>5.8.23</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

### 3.3 application.yml

```yaml
server:
  port: 8080

spring:
  # Redis配置(最小化部署可删除)
  # redis:
  #   host: localhost
  #   port: 6379
  #   password: ${REDIS_PASSWORD:}

alibaba:
  app-key: ${ALIBABA_APP_KEY}
  app-secret: ${ALIBABA_APP_SECRET}
  token-url: https://gw.open.1688.com/openapi/http/1/system.oauth2/getToken
  search-url: https://gw.open.1688.com/openapi/param2/1/com.alibaba.linkplus/alibaba.cross.similar.offer.search

aliyun:
  oss:
    endpoint: ${OSS_ENDPOINT}
    access-key-id: ${OSS_ACCESS_KEY_ID}
    access-key-secret: ${OSS_ACCESS_KEY_SECRET}
    bucket-name: ${OSS_BUCKET_NAME}
    url-prefix: ${OSS_URL_PREFIX}
```

### 3.4 签名工具类

**SignatureUtil.java:**
```java
package com.company.imagesearch.util;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.util.Map;
import java.util.TreeMap;

public class SignatureUtil {

    public static String generateSignature(Map<String, String> params, 
                                          String apiPath, 
                                          String appSecret) {
        try {
            TreeMap<String, String> sortedParams = new TreeMap<>(params);

            StringBuilder signStr = new StringBuilder(apiPath);
            for (Map.Entry<String, String> entry : sortedParams.entrySet()) {
                signStr.append(entry.getKey()).append(entry.getValue());
            }

            Mac mac = Mac.getInstance("HmacSHA1");
            SecretKeySpec secretKeySpec = new SecretKeySpec(
                appSecret.getBytes("UTF-8"), "HmacSHA1"
            );
            mac.init(secretKeySpec);
            byte[] hash = mac.doFinal(signStr.toString().getBytes("UTF-8"));

            StringBuilder hexString = new StringBuilder();
            for (byte b : hash) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) hexString.append('0');
                hexString.append(hex);
            }

            return hexString.toString().toUpperCase();

        } catch (Exception e) {
            throw new RuntimeException("签名生成失败: " + e.getMessage());
        }
    }
}
```

### 3.5 Token管理服务

**TokenManager.java (最小化版本 - 内存缓存):**
```java
package com.company.imagesearch.service;

import cn.hutool.http.HttpUtil;
import cn.hutool.json.JSONUtil;
import org.springframework.stereotype.Service;
import java.util.HashMap;
import java.util.Map;

@Service
public class TokenManager {

    private String cachedToken;
    private long expireTime;

    public synchronized String getAccessToken(String appKey, String appSecret, String tokenUrl) {
        // 1. 检查内存缓存
        if (cachedToken != null && System.currentTimeMillis() < expireTime) {
            return cachedToken;
        }

        // 2. 重新获取Token
        Map<String, Object> params = new HashMap<>();
        params.put("grant_type", "client_credentials");
        params.put("client_id", appKey);
        params.put("client_secret", appSecret);

        String response = HttpUtil.post(tokenUrl, params);
        Map<String, Object> result = JSONUtil.toBean(response, Map.class);

        cachedToken = (String) result.get("access_token");
        int expiresIn = (int) result.getOrDefault("expires_in", 7200);
        expireTime = System.currentTimeMillis() + (expiresIn - 200) * 1000L;

        return cachedToken;
    }
}
```

**注意:** 如需Redis版本,只需添加 `StringRedisTemplate` 依赖即可

### 3.6 图片上传服务

**ImageUploadService.java:**
```java
package com.company.imagesearch.service;

import com.aliyun.oss.OSS;
import com.aliyun.oss.model.PutObjectRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.*;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ImageUploadService {

    private final OSS ossClient;

    @Value("${aliyun.oss.bucket-name}")
    private String bucketName;

    @Value("${aliyun.oss.url-prefix}")
    private String urlPrefix;

    public String uploadImage(MultipartFile file) throws IOException {
        InputStream processed = preprocessImage(file.getInputStream());

        String objectName = "products/" + System.currentTimeMillis() + 
                           "/" + UUID.randomUUID() + ".jpg";

        ossClient.putObject(new PutObjectRequest(bucketName, objectName, processed));

        return urlPrefix + "/" + objectName;
    }

    private InputStream preprocessImage(InputStream input) throws IOException {
        BufferedImage img = ImageIO.read(input);

        int maxSize = 800;
        if (img.getWidth() > maxSize || img.getHeight() > maxSize) {
            double scale = Math.min((double) maxSize / img.getWidth(), 
                                   (double) maxSize / img.getHeight());
            int newW = (int) (img.getWidth() * scale);
            int newH = (int) (img.getHeight() * scale);

            BufferedImage resized = new BufferedImage(newW, newH, BufferedImage.TYPE_INT_RGB);
            Graphics2D g = resized.createGraphics();
            g.drawImage(img, 0, 0, newW, newH, null);
            g.dispose();
            img = resized;
        }

        ByteArrayOutputStream out = new ByteArrayOutputStream();
        ImageIO.write(img, "jpg", out);
        return new ByteArrayInputStream(out.toByteArray());
    }
}
```

### 3.7 跨境搜索服务

**CrossBorderSearchService.java:**
```java
package com.company.imagesearch.service;

import cn.hutool.http.HttpUtil;
import cn.hutool.json.JSONUtil;
import com.company.imagesearch.util.SignatureUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.*;

@Service
@RequiredArgsConstructor
public class CrossBorderSearchService {

    private final TokenManager tokenManager;

    public Map<String, Object> searchByImage(String imageUrl,
                                             String appKey,
                                             String appSecret,
                                             String tokenUrl,
                                             String searchUrl) {
        String token = tokenManager.getAccessToken(appKey, appSecret, tokenUrl);

        String apiPath = String.format(
            "param2/1/com.alibaba.linkplus/alibaba.cross.similar.offer.search/%s",
            appKey
        );

        Map<String, String> params = new HashMap<>();
        params.put("access_token", token);
        params.put("imageUrl", imageUrl);

        String signature = SignatureUtil.generateSignature(params, apiPath, appSecret);
        params.put("_aop_signature", signature);

        try {
            String response = HttpUtil.post(searchUrl, params);
            Map<String, Object> result = JSONUtil.toBean(response, Map.class);

            if ((Boolean) result.getOrDefault("success", false)) {
                Map<String, Object> data = (Map<String, Object>) result.get("result");
                List<Map<String, Object>> offers = (List<Map<String, Object>>) data.get("offerList");

                Map<String, Object> successMap = new HashMap<>();
                successMap.put("success", true);
                successMap.put("total", offers.size());
                successMap.put("offers", offers);
                return successMap;
            } else {
                Map<String, Object> errorMap = new HashMap<>();
                errorMap.put("success", false);
                errorMap.put("error", result.get("error_response"));
                return errorMap;
            }

        } catch (Exception e) {
            Map<String, Object> errorMap = new HashMap<>();
            errorMap.put("success", false);
            errorMap.put("errorMessage", e.getMessage());
            return errorMap;
        }
    }
}
```

### 3.8 REST Controller

**ImageSearchController.java:**
```java
package com.company.imagesearch.controller;

import com.company.imagesearch.service.*;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.util.*;

@RestController
@RequestMapping("/api/v1/search")
@RequiredArgsConstructor
public class ImageSearchController {

    private final ImageUploadService imageUploadService;
    private final CrossBorderSearchService searchService;

    @Value("${alibaba.app-key}")
    private String appKey;

    @Value("${alibaba.app-secret}")
    private String appSecret;

    @Value("${alibaba.token-url}")
    private String tokenUrl;

    @Value("${alibaba.search-url}")
    private String searchUrl;

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "UP");
    }

    @PostMapping("/upload-and-search")
    public ResponseEntity<Map<String, Object>> uploadAndSearch(
            @RequestParam("image") MultipartFile file) {
        try {
            String imageUrl = imageUploadService.uploadImage(file);
            Map<String, Object> result = searchService.searchByImage(
                imageUrl, appKey, appSecret, tokenUrl, searchUrl
            );
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.ok(Map.of(
                "success", false,
                "errorMessage", e.getMessage()
            ));
        }
    }

    @PostMapping("/by-url")
    public ResponseEntity<Map<String, Object>> searchByUrl(
            @RequestBody Map<String, String> request) {
        
        String imageUrl = request.get("imageUrl");
        if (imageUrl == null) {
            return ResponseEntity.badRequest().body(Map.of(
                "success", false,
                "errorMessage", "imageUrl不能为空"
            ));
        }

        Map<String, Object> result = searchService.searchByImage(
            imageUrl, appKey, appSecret, tokenUrl, searchUrl
        );

        return ResponseEntity.ok(result);
    }
}
```

### 3.9 启动类

**ImageSearchApplication.java:**
```java
package com.company.imagesearch;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class ImageSearchApplication {
    public static void main(String[] args) {
        SpringApplication.run(ImageSearchApplication.class, args);
    }
}
```

---

## 四、打包与部署

### 4.1 本地打包

```bash
mvn clean package -DskipTests
# 生成: target/image-search-proxy-1.0.0.jar
```

### 4.2 上传到ECS

```bash
scp target/image-search-proxy-1.0.0.jar root@your-ecs-ip:/opt/app/
```

### 4.3 配置环境变量

```bash
mkdir -p /opt/app
vim /opt/app/env.sh
```

**最小化部署 env.sh:**
```bash
#!/bin/bash
export ALIBABA_APP_KEY="your_app_key"
export ALIBABA_APP_SECRET="your_app_secret"
export OSS_ENDPOINT="oss-cn-hangzhou.aliyuncs.com"
export OSS_ACCESS_KEY_ID="your_oss_key"
export OSS_ACCESS_KEY_SECRET="your_oss_secret"
export OSS_BUCKET_NAME="your-bucket"
export OSS_URL_PREFIX="https://your-bucket.oss-cn-hangzhou.aliyuncs.com"
```

```bash
chmod +x /opt/app/env.sh
```

**说明:** 如使用Redis,添加 `export REDIS_PASSWORD="your_password"`

### 4.4 创建Systemd服务

```bash
vim /etc/systemd/system/image-search.service
```

```ini
[Unit]
Description=1688 Image Search Proxy
After=network.target redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/app
EnvironmentFile=/opt/app/env.sh
ExecStart=/usr/bin/java -Xms256m -Xmx512m -jar /opt/app/image-search-proxy-1.0.0.jar
Restart=always

[Install]
WantedBy=multi-user.target
```

**启动服务:**
```bash
systemctl daemon-reload
systemctl start image-search
systemctl enable image-search
systemctl status image-search
```

### 4.5 配置防火墙

```bash
# 开放8080端口
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --reload

# 或直接关闭防火墙(仅测试环境)
systemctl stop firewalld
systemctl disable firewalld
```

---

## 五、测试验证

### 5.1 健康检查

```bash
curl http://your-ecs-ip:8080/api/v1/search/health
# 返回: {"status":"UP"}
```

### 5.2 使用图片URL搜索

```bash
curl -X POST http://your-ecs-ip:8080/api/v1/search/by-url \
  -H "Content-Type: application/json" \
  -d '{"imageUrl": "https://your-cdn.com/product.jpg"}'
```

### 5.3 上传图片并搜索

```bash
curl -X POST http://your-ecs-ip:8080/api/v1/search/upload-and-search \
  -F "image=@/path/to/image.jpg"
```

### 5.4 返回数据格式

```json
{
  "success": true,
  "total": 5,
  "offers": [
    {
      "offerId": "439143824",
      "subject": "手机壳多色可选防摔",
      "price": 12.5,
      "oldPrice": 628.0,
      "quantityBegin": 3,
      "unit": "个、件",
      "imageUrl": "https://xxx.jpg",
      "province": "浙江",
      "city": "杭州市",
      "supplyAmount": 2000,
      "categoryId": "xx",
      "detailUrl": "https://detail.1688.com/offer/439143824.html"
    }
  ]
}
```

---

## 六、常见问题

### Q1: 签名生成失败?
**A:** 
1. 确认使用HMAC-SHA1算法(不是MD5)
2. API路径格式: `param2/1/com.alibaba.linkplus/alibaba.cross.similar.offer.search/{APP_KEY}`
3. 参数按ASCII码升序排列
4. 签名结果转大写

### Q2: imageUrl必须是什么格式?
**A:** 
- 必须是可公开访问的HTTP/HTTPS URL
- 不支持base64编码
- 推荐使用阿里云OSS存储

### Q3: 搜索结果为空?
**A:** 
1. 检查imageUrl是否可访问
2. 确认图片质量清晰
3. 该商品可能不在跨境专供库中

### Q4: Token获取失败?
**A:** 
1. 检查App Key和App Secret
2. 确认应用已审核通过
3. 检查网络连接

### Q5: 服务无法启动?
**A:** 
```bash
# 查看日志
journalctl -u image-search -n 50

# 检查端口占用
lsof -i:8080

# 手动启动测试
java -jar /opt/app/image-search-proxy-1.0.0.jar
```

---

## 七、运维管理

### 7.1 查看日志

```bash
# 实时日志
journalctl -u image-search -f

# 最近100行
journalctl -u image-search -n 100

# 搜索错误
journalctl -u image-search | grep ERROR
```

### 7.2 重启服务

```bash
systemctl restart image-search
systemctl status image-search
```

### 7.3 更新部署

```bash
# 停止服务
systemctl stop image-search

# 备份旧版本
mv /opt/app/image-search-proxy-1.0.0.jar /opt/app/backup/

# 上传新版本
scp target/image-search-proxy-1.0.0.jar root@your-ecs-ip:/opt/app/

# 启动服务
systemctl start image-search
```

---

## 八、安全配置

### 8.1 密钥保护

- 不要将App Secret提交到Git
- 使用环境变量存储敏感信息
- 定期轮换OSS访问密钥

### 8.2 API鉴权(可选)

在Controller中添加:
```java
@PostMapping("/by-url")
public ResponseEntity<Map<String, Object>> searchByUrl(
        @RequestHeader("X-API-Key") String apiKey,
        @RequestBody Map<String, String> request) {
    
    if (!"your_internal_api_key".equals(apiKey)) {
        return ResponseEntity.status(401).body(Map.of(
            "success", false,
            "errorMessage", "未授权"
        ));
    }
    
    // 正常处理...
}
```

---

## 附录

### A. 完整环境变量清单

```bash
ALIBABA_APP_KEY=your_app_key
ALIBABA_APP_SECRET=your_app_secret
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_ACCESS_KEY_ID=your_oss_key
OSS_ACCESS_KEY_SECRET=your_oss_secret
OSS_BUCKET_NAME=your-bucket
OSS_URL_PREFIX=https://your-bucket.oss-cn-hangzhou.aliyuncs.com
REDIS_PASSWORD=your_redis_password
```

### B. 依赖版本

- Java: 17
- Spring Boot: 3.2.0
- Aliyun OSS SDK: 3.17.1
- Hutool: 5.8.23
- Redis: 最新稳定版

### C. 参考文档

- API文档: https://open.1688.com/api/apidocdetail.htm?id=com.alibaba.linkplus:alibaba.cross.similar.offer.search-1
- 签名文档: https://open.1688.com/doc/signature.htm
- 开放平台: https://open.1688.com