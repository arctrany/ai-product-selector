# 实施任务清单

## 1. 数据模型扩展
- [x] 1.1 在 `common/models.py` 的 `ProductInfo` 中添加 `product_id: Optional[str]` 字段
- [x] 1.2 在 scrape 返回结果中添加 `first_competitor_details: Optional[Dict]` 字段
- [x] 1.3 更新相关类型注解和文档字符串

## 2. OzonScraper 核心功能实现
- [x] 2.1 修改 `scrape()` 方法签名，添加递归控制参数
  - 添加 `_recursion_depth: int = 0` 参数
  - 添加 `_fetch_competitor_details: bool = True` 参数（内部使用，不暴露给外部调用）
- [x] 2.2 实现 `_click_first_competitor()` 辅助方法
  - 定位第一个跟卖店铺卡片（支持新旧选择器）
  - 查找并点击可点击链接
  - 验证页面跳转成功
  - 返回跳转后的新 URL
- [x] 2.3 在 `scrape()` 中添加递归调用逻辑
  - 判断递归条件：`include_competitors and has_better_price and _fetch_competitor_details and _recursion_depth == 0`
  - 调用 `_click_first_competitor()` 获取新 URL
  - 递归调用 `scrape(new_url, include_competitors=False, _fetch_competitor_details=False, _recursion_depth=1)`
  - 将结果存入 `first_competitor_details` 字段
- [x] 2.4 添加完善的错误处理
  - 捕获点击失败异常
  - 捕获跳转超时异常
  - 捕获递归抓取失败异常
  - 确保失败不影响主流程

## 3. Product ID 提取实现
- [x] 3.1 在 `scrape_product_prices()` 或 `scrape()` 中从 URL 提取 `product_id`
  - 使用正则表达式从 URL 中提取商品 ID
  - 处理不同格式的 URL（/product/xxx-12345/, /seller/xxx/product/12345/ 等）
- [x] 3.2 将 `product_id` 添加到返回结果中

## 4. 递归深度限制和安全保护
- [x] 4.1 在 `scrape()` 开头添加递归深度检查
  - `if _recursion_depth > 1: raise RecursionError("递归深度超限")`
- [x] 4.2 确保递归调用时正确传递 `_recursion_depth=1`
- [x] 4.3 确保递归调用时 `include_competitors=False`

## 5. 选择器兼容性
- [x] 5.1 在 `_click_first_competitor()` 中支持多套选择器
  - 新版选择器：`div.pdp_bk3`, `a.pdp_a5e`, `a.pdp_e2a`
  - 旧版选择器：`div.pdp_kb2`, `a.pdp_ae5`, `a.pdp_ea2`
  - 通用选择器：`a[href*='/seller/']`, `a[href*='/product/']`
- [x] 5.2 实现选择器降级策略（按优先级逐个尝试）

## 6. 测试用例开发
- [x] 6.1 单元测试：`test_click_first_competitor()` 方法
  - 测试成功点击和跳转
  - 测试元素不存在的情况
  - 测试跳转失败的情况
- [x] 6.2 单元测试：递归抓取逻辑
  - 测试 `has_better_price=True` 时触发递归
  - 测试 `has_better_price=False` 时不触发递归
  - 测试递归深度限制
- [x] 6.3 集成测试：完整的递归抓取流程
  - 使用 Mock 模拟测试
  - 验证数据结构正确性
  - 验证 `first_competitor_details` 字段完整性
- [x] 6.4 错误处理测试
  - 测试点击失败时的降级
  - 测试跳转超时时的降级
  - 测试递归抓取失败时的降级
- [x] 6.5 URL 解析测试
  - 测试标准格式 URL
  - 测试卖家格式 URL
  - 测试边界条件和无效 URL

## 7. 文档更新
- [x] 7.1 更新 `ozon_scraper.py` 的模块文档字符串
- [x] 7.2 更新 `scrape()` 方法的文档字符串，说明新参数和新字段
- [x] 7.3 更新 `_click_first_competitor()` 方法的文档字符串
- [x] 7.4 代码中的文档字符串随实现同步完成

## 8. 代码审查和优化
- [x] 8.1 运行 lint 检查并修复所有错误
  - `pylint common/scrapers/ozon_scraper.py`
  - `mypy common/scrapers/ozon_scraper.py`
- [x] 8.2 代码审查：检查递归逻辑的正确性
- [x] 8.3 代码审查：检查错误处理的完整性
- [x] 8.4 代码审查：检查性能影响和资源占用


## 依赖关系

```
任务依赖图：
1.1, 1.2, 1.3 → 2.1
2.1 → 2.2 → 2.3 → 2.4
2.1 → 3.1 → 3.2
2.1 → 4.1, 4.2, 4.3
2.2 → 5.1, 5.2
2.4 → 6.1, 6.2
2.3 → 6.3, 6.4, 6.5
所有功能完成 → 7.1, 7.2, 7.3, 7.4
所有功能完成 → 8.1, 8.2, 8.3, 8.4
所有审查通过 → 9.1, 9.2, 9.3, 9.4, 9.5
验证完成 → 10.1, 10.2, 10.3, 10.4, 10.5, 10.6
```

## 估时

- **核心功能实现**: 2-3 天
- **测试开发**: 1-2 天
- **文档和审查**: 0.5-1 天
- **集成验证**: 0.5-1 天
- **总计**: 4-7 天
