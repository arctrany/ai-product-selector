# Implementation Tasks

## 1. 分析 DOM 结构
- [x] 1.1 分析 seefar_table.html 的表格结构
- [x] 1.2 确定类目字段的 XPath/CSS 选择器
- [x] 1.3 确定上架时间字段的 XPath/CSS 选择器
- [x] 1.4 确定销量字段的 XPath/CSS 选择器

## 2. 实现数据提取方法
- [x] 2.1 实现 `_extract_category()` 方法提取类目信息
- [x] 2.2 实现 `_extract_listing_date()` 方法提取上架时间
- [x] 2.3 实现 `_extract_sales_volume()` 方法提取销量
- [x] 2.4 确保所有方法在无法提取时返回 `None` 而非默认值

## 3. 集成到主流程
- [x] 3.1 在 `_extract_product_from_row_async()` 中调用新方法
- [x] 3.2 将提取的数据添加到 `product_data` 字典
- [x] 3.3 添加适当的日志记录

## 4. 代码质量保证
- [x] 4.1 遵循项目编码规范（避免硬编码、跨平台兼容）
- [x] 4.2 添加异常处理和错误日志
- [x] 4.3 确保代码风格一致
- [x] 4.4 运行 lint 检查

## 5. 实现前置过滤功能
- [x] 5.1 修改 `_extract_products_list_async()` 启用循环遍历
- [x] 5.2 在循环中先提取基础字段（类目、上架时间、销量）
- [x] 5.3 应用 filter_func 进行前置过滤判断
- [x] 5.4 仅对通过过滤的商品继续处理 OZON 详情页
- [x] 5.5 添加过滤日志记录（记录跳过原因）
- [x] 5.6 运行 lint 检查确保代码质量

## 6. 数据模型对齐和修复
- [x] 6.1 修复 `usr_input.json` 字段名拼写错误（item_min_weigt -> item_min_weight）
- [x] 6.2 在 `UIConfig` 中添加类目黑名单字段（category_blacklist）
- [x] 6.3 更新 `cli/main.py` 的 `load_user_data()` 函数以支持新字段
- [x] 6.4 验证数据传递流程完整性

## 7. 实现重量提取
- [x] 7.1 分析 seefar_table.html 确定重量字段位置（倒数第二列）
- [x] 7.2 实现 `_extract_weight()` 方法提取重量信息
- [x] 7.3 在 `_extract_products_list_async()` 中集成重量提取
- [x] 7.4 添加重量提取的异常处理和日志

## 8. 实现完整的过滤函数
- [x] 8.1 创建 `create_product_filter()` 函数，接收 UIConfig 参数
- [x] 8.2 实现类目黑名单过滤逻辑
- [x] 8.3 实现上架时间阈值过滤逻辑
- [x] 8.4 实现销量范围过滤逻辑
- [x] 8.5 实现重量范围过滤逻辑
- [x] 8.6 实现 G01 商品价格范围过滤逻辑（如适用）
- [x] 8.7 确保所有过滤条件组合正确（AND 逻辑）

## 9. 集成和测试
- [x] 9.1 在 `scrape_store_products()` 中集成完整的 filter_func
- [x] 9.2 确保 filter_func 从 UIConfig 正确获取配置
- [x] 9.3 运行 lint 检查所有修改的文件
- [x] 9.4 创建单元测试验证过滤功能
- [x] 9.5 运行测试确保功能正确
