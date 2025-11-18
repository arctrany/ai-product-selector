# Tasks: 重构抓取器代码去重

## 阶段1：SeerfarScraper 重构

### 1.1 提取重复逻辑为独立方法
- [ ] 在 `SeerfarScraper` 中添加 `_deduplicate_rows` 方法
  - 输入：商品行列表
  - 输出：去重后的商品行列表
  - 逻辑：基于 `data-index` 属性去重
- [ ] 在 `SeerfarScraper` 中添加 `_validate_page` 方法
  - 输入：page 对象
  - 输出：布尔值表示是否有效
  - 逻辑：检查 page 是否为 None

### 1.2 更新调用点使用新方法
- [ ] 在 `extract_products_async` 方法中替换第一处去重逻辑（第394-407行）
  - 使用 `self._deduplicate_rows(product_rows)` 替换
- [ ] 在 `extract_products_async` 方法中替换第二处去重逻辑（第416-428行）
  - 使用 `self._deduplicate_rows(current_rows)` 替换
- [ ] 在 `extract_products_async` 方法中使用 `_validate_page` 替换空值检查（第367-370行）
- [ ] 在 `_extract_product_from_row_async` 方法中使用 `_validate_page` 替换空值检查（第526-529行）

### 1.3 删除废弃代码
- [ ] 删除 `_extract_product_from_row_async` 方法中的注释代码块（第624-653行）
  - 包括注释掉的 OzonScraper 调用逻辑
  - 包括 try-finally 块中的注释代码
- [ ] 删除重复的日志输出语句

### 1.4 测试和验证
- [ ] 运行 `tests/test_selection_modes.py` 确保无回归
- [ ] 运行 `tests/test_selection_modes_real.py` 确保真实场景正常
- [ ] 检查日志输出是否正常，无重复日志

## 阶段2：OzonScraper 重构

### 2.1 提取辅助方法
- [ ] 在 `OzonScraper` 中添加 `_validate_price` 方法
  - 输入：价格值、价格类型名称
  - 输出：布尔值表示价格是否有效
  - 逻辑：检查价格是否为 None 或 <= 0
- [ ] 在 `OzonScraper` 中添加 `_handle_extraction_error` 方法
  - 输入：异常对象、上下文描述
  - 输出：无（记录日志）
  - 逻辑：统一的错误日志格式

### 2.2 更新价格提取逻辑
- [ ] 在 `_extract_basic_prices` 方法中使用 `_validate_price` 验证绿标价格
- [ ] 在 `_extract_basic_prices` 方法中使用 `_validate_price` 验证黑标价格
- [ ] 在 `_extract_competitor_price_value` 方法中使用 `_validate_price` 验证跟卖价格

### 2.3 统一错误处理
- [ ] 在 `_extract_price_data_core` 方法中使用 `_handle_extraction_error`
- [ ] 在 `_extract_basic_prices` 方法中使用 `_handle_extraction_error`
- [ ] 在 `_extract_competitor_price_value` 方法中使用 `_handle_extraction_error`
- [ ] 在 `_extract_product_image_core` 方法中使用 `_handle_extraction_error`

### 2.4 清理和优化
- [ ] 删除所有注释掉的实验性代码
- [ ] 统一日志格式（使用 emoji 前缀：✅ 成功、⚠️ 警告、❌ 错误）
- [ ] 确保所有方法都有完整的文档字符串

### 2.5 测试和验证
- [ ] 运行 `tests/test_ozon_scraper_method.py` 确保价格提取正常
- [ ] 运行 `tests/test_ozon_competitor_scenarios_fixed.py` 确保跟卖检测正常
- [ ] 运行 `tests/test_erp_ozon_integration.py` 确保集成测试通过

## 阶段3：代码质量和文档

### 3.1 代码审查
- [ ] 检查所有新增方法的类型注解是否完整
- [ ] 检查所有新增方法的文档字符串是否清晰
- [ ] 确认没有引入新的代码重复

### 3.2 测试覆盖
- [ ] 为 `_deduplicate_rows` 方法添加单元测试（如需要）
- [ ] 为 `_validate_page` 方法添加单元测试（如需要）
- [ ] 为 `_validate_price` 方法添加单元测试（如需要）

### 3.3 文档更新
- [ ] 更新相关代码注释，说明重构的原因
- [ ] 在提交信息中详细说明重构内容
- [ ] 更新 CHANGELOG（如有）

## 验证清单

### 功能验证
- [ ] 所有现有测试通过（100%）
- [ ] 手动测试关键场景：
  - [ ] Seerfar 商品列表抓取
  - [ ] OZON 价格提取
  - [ ] 跟卖店铺检测
  - [ ] ERP 信息抓取

### 代码质量验证
- [ ] 代码行数减少（预期减少 50-100 行）
- [ ] 方法平均长度减少
- [ ] 圈复杂度降低（所有方法 < 10）
- [ ] 无 pylint/flake8 警告

### 性能验证
- [ ] 关键路径执行时间无明显变化（±5%）
- [ ] 内存使用无明显增加
- [ ] 无新的性能瓶颈

## 依赖关系

```
阶段1 (SeerfarScraper)
  ├─ 1.1 提取方法
  ├─ 1.2 更新调用点 (依赖 1.1)
  ├─ 1.3 删除废弃代码 (依赖 1.2)
  └─ 1.4 测试验证 (依赖 1.3)

阶段2 (OzonScraper)
  ├─ 2.1 提取方法
  ├─ 2.2 更新价格逻辑 (依赖 2.1)
  ├─ 2.3 统一错误处理 (依赖 2.1)
  ├─ 2.4 清理优化 (依赖 2.2, 2.3)
  └─ 2.5 测试验证 (依赖 2.4)

阶段3 (质量和文档)
  ├─ 3.1 代码审查 (依赖阶段1, 阶段2)
  ├─ 3.2 测试覆盖 (依赖阶段1, 阶段2)
  └─ 3.3 文档更新 (依赖 3.1, 3.2)
```

## 预估工作量

- **阶段1**: 4-6 小时
- **阶段2**: 4-6 小时  
- **阶段3**: 2-3 小时
- **总计**: 10-15 小时（约 1.5-2 个工作日）

## 风险缓解

- **每完成一个阶段立即提交**，便于回滚
- **优先运行测试**，发现问题立即修复
- **保持小步迭代**，避免一次性修改过多
- **代码审查**，确保重构质量
