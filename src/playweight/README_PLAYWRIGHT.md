# Playwright 环境配置说明

## ✅ 已完成的工作

### 1. **Playwright 安装成功**
```bash
# 已安装的版本
Playwright: 1.55.0
Python包: playwright, greenlet, pyee
```

### 2. **浏览器驱动已安装**
- ✅ Chromium 140.0.7339.16
- ✅ Firefox 141.0
- ✅ Webkit 26.0
- ✅ FFMPEG
- ✅ Chromium Headless Shell

安装位置：`C:\Users\wuhao\AppData\Local\ms-playwright\`

### 3. **项目结构已更新**

#### **新增目录和文件**

```
ai-product-selector/
├── src/
│   └── playweight/                    # Playwright 爬虫实现（主要代码）
│       ├── __init__.py
│       ├── automation_scenario.py     # 自动化场景
│       ├── browser_service.py         # 浏览器服务
│       ├── dom_analyzer.py            # DOM 分析器
│       ├── integrated_crawler.py      # 集成爬虫
│       ├── logger_config.py           # 日志配置
│       ├── paginator.py               # 分页器
│       ├── user_interface.py          # 用户界面
│       ├── requirements.txt           # 依赖包
│       └── screenshots/               # 截图目录
│
├── tests/                             # 测试文件
│   ├── __init__.py
│   ├── browser_test.py               # 浏览器测试
│   ├── method_test.py                # 方法测试
│   ├── playwright_cdp_test.py        # CDP 测试
│   ├── playwright_cdp_default_user_test.py
│   ├── playwright_cdp_improved_test.py
│   ├── playwright_persistent_context_test.py
│   ├── seefar_test.py                # Seefar 测试
│   └── simple_test.py                # 简单测试
│
└── specs/                             # 规范文档
    ├── playwright/
    │   └── browser.md                # Playwright Browser API 文档
    │
    └── yingdao_sdk/                  # 影刀 SDK 文档
        ├── package.md
        ├── xbot.app.dialog.md
        ├── xbot.browser.md
        ├── xbot.browser.new.md
        ├── xbot.logging.new.md
        ├── xbot.web.md
        ├── xbot.web.new.md
        ├── xbot.web.Element.md
        └── xbot.web.Element.new.md
```

#### **已移除的文件**
- ❌ `src/playwright/` (本地临时创建的教程文件，已删除)
- ❌ `src/bin/speckit_manager/` (已移除)
- ❌ `src/yd/explore_browser.py` (已移动到 tests/)
- ❌ `src/yd/__pycache__/` (已清理)

## 🚀 快速开始

### 1. 安装依赖
```bash
# 安装 Playwright 相关依赖
cd src/playweight
pip install -r requirements.txt

# 如果浏览器驱动未安装，运行：
playwright install
```

### 2. 启动 Codegen (代码生成器)
```bash
# 空白页面
playwright codegen

# 访问 Seefar
playwright codegen https://seerfar.cn/admin/store-detail.html?storeId=99927&platform=OZON

# 访问百度
playwright codegen https://www.baidu.com
```

### 3. 运行测试
```bash
# 运行 Seefar 测试
python tests/seefar_test.py

# 运行浏览器测试
python tests/browser_test.py

# 运行 Playwright CDP 测试
python tests/playwright_cdp_test.py
```

### 4. 使用集成爬虫
```bash
cd src/playweight
python integrated_crawler.py
```

## 📚 主要功能模块

### 1. **browser_service.py** - 浏览器服务
提供统一的浏览器管理接口：
- 浏览器启动和关闭
- 页面导航
- 元素查找和操作
- 截图功能

### 2. **dom_analyzer.py** - DOM 分析器
分析网页 DOM 结构：
- 元素定位策略
- XPath 生成
- 页面结构分析

### 3. **integrated_crawler.py** - 集成爬虫
完整的爬虫实现：
- 数据抓取
- 分页处理
- 错误处理
- 结果存储

### 4. **automation_scenario.py** - 自动化场景
预定义的自动化场景：
- 登录流程
- 数据采集流程
- 批量操作流程

### 5. **user_interface.py** - 用户界面
提供交互式界面：
- 参数配置
- 进度显示
- 结果查看

## 🔧 Codegen 使用技巧

### 基本命令
```bash
# 生成 Python 代码
playwright codegen --target python https://example.com

# 生成代码并保存到文件
playwright codegen --target python -o script.py https://example.com

# 使用特定浏览器
playwright codegen --browser chromium https://example.com
playwright codegen --browser firefox https://example.com
playwright codegen --browser webkit https://example.com

# 设置窗口大小
playwright codegen --viewport-size=1920,1080 https://example.com

# 模拟移动设备
playwright codegen --device="iPhone 12" https://example.com
playwright codegen --device="iPad Pro" https://example.com
```

### 调试技巧
```python
# 在代码中添加暂停点
page.pause()  # 会打开 Playwright Inspector

# 慢速执行，便于观察
browser = p.chromium.launch(
    headless=False,
    slow_mo=1000  # 每个操作延迟 1000ms
)
```

## 📖 学习资源

### 官方文档
- [Playwright Python 文档](https://playwright.dev/python/)
- [API 参考](https://playwright.dev/python/docs/api/class-playwright)
- [选择器文档](https://playwright.dev/python/docs/selectors)

### 项目内文档
- `specs/playwright/browser.md` - Browser API 详细文档
- `specs/yingdao_sdk/` - 影刀 SDK 文档（对比参考）

### 示例代码
- `tests/` - 各种测试示例
- `src/playweight/` - 实际应用代码

## 🆚 Playwright vs 影刀RPA

| 特性 | Playwright | 影刀RPA |
|------|-----------|---------|
| **跨平台** | ✅ Windows/Mac/Linux | ❌ 仅 Windows |
| **浏览器支持** | Chromium, Firefox, Webkit | Chrome |
| **代码生成** | ✅ Codegen | ❌ 需手动编写 |
| **开源** | ✅ 完全开源 | ❌ 商业软件 |
| **学习资源** | 🔥 丰富 | 📚 有限 |
| **调试工具** | ✅ Inspector, Trace Viewer | ⚠️ 基础 |
| **API 稳定性** | ✅ 稳定，文档完善 | ⚠️ 文档不全 |
| **社区支持** | 🌟 活跃 | 💬 一般 |

## 💡 最佳实践

### 1. 元素定位优先级
```python
# ✅ 优先使用语义化定位
page.get_by_text("销售额")
page.get_by_role("button", name="搜索")

# ⚠️ 其次使用稳定的属性
page.locator("#id")
page.locator("[data-testid='element']")

# ❌ 避免过度依赖 CSS 类名
page.locator(".css-1234567")  # 类名可能随时变化
```

### 2. 等待策略
```python
# ✅ 使用内置等待
page.locator("#element").click()  # 自动等待元素可点击

# ✅ 等待网络空闲
page.wait_for_load_state("networkidle")

# ❌ 避免固定延迟
import time
time.sleep(5)  # 不推荐
```

### 3. 错误处理
```python
try:
    element = page.locator("#element")
    element.click(timeout=5000)  # 5秒超时
except TimeoutError:
    print("元素未找到或不可点击")
except Exception as e:
    print(f"发生错误: {str(e)}")
```

## 🎯 下一步

1. ✅ **Playwright 已安装完成**
2. ✅ **浏览器驱动已安装**
3. ✅ **项目结构已更新**
4. 📝 **学习使用 Codegen 生成代码**
5. 🧪 **运行测试文件熟悉 API**
6. 🚀 **开始开发实际爬虫**

## 🆘 常见问题

### Q1: 如何启动 Codegen？
```bash
playwright codegen https://example.com
```

### Q2: 如何处理"找不到元素"错误？
1. 使用 Codegen 验证选择器
2. 添加适当的等待
3. 检查元素是否在 iframe 中

### Q3: 如何截图？
```python
page.screenshot(path="screenshot.png")
```

### Q4: 如何在无头模式运行？
```python
browser = p.chromium.launch(headless=True)
```

## 📞 获取帮助

- 查看 `specs/playwright/browser.md` 了解 API 详情
- 运行 `tests/` 中的示例代码学习用法
- 访问 Playwright 官方文档

---

**安装完成时间**: 2025-10-17  
**Playwright 版本**: 1.55.0  
**Python 版本**: 3.11  
**操作系统**: Windows 10

