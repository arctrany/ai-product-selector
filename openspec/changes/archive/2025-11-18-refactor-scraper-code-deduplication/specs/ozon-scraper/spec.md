# Spec: OZON Scraper 重构

## MODIFIED Requirements

### Requirement: Code Quality and Maintainability

**描述**: OzonScraper 应该具有高质量、易维护的代码结构，避免重复逻辑，提供清晰的辅助方法。

**变更类型**: MODIFIED

**变更原因**: 
- 当前代码缺少辅助方法，导致验证和错误处理逻辑分散
- 价格验证逻辑在多处重复
- 错误处理格式不统一

#### Scenario: 价格验证使用统一方法

**Given**: OzonScraper 需要验证提取的价格是否有效  
**When**: 调用 `_validate_price(price, price_type)` 方法  
**Then**: 
- 如果价格为 None 或 <= 0，返回 False 并记录调试日志
- 如果价格有效，返回 True
- 日志格式统一：`⚠️ {price_type}价格无效: {price}`

**实现要点**:
```python
def _validate_price(self, price: Optional[float], price_type: str) -> bool:
    """验证价格是否有效"""
    if price is None or price <= 0:
        self.logger.debug(f"⚠️ {price_type}价格无效: {price}")
        return False
    return True
```

#### Scenario: 错误处理使用统一方法

**Given**: OzonScraper 在提取数据时发生异常  
**When**: 调用 `_handle_extraction_error(error, context)` 方法  
**Then**: 
- 记录错误日志，格式：`❌ {context}失败: {error}`
- 日志级别为 ERROR
- 可选：记录到错误追踪系统

**实现要点**:
```python
def _handle_extraction_error(self, error: Exception, context: str) -> None:
    """统一处理提取错误"""
    self.logger.error(f"❌ {context}失败: {error}")
```

#### Scenario: 价格提取逻辑使用辅助方法

**Given**: 在 `_extract_basic_prices` 方法中提取绿标和黑标价格  
**When**: 提取到价格后需要验证  
**Then**: 
- 使用 `_validate_price(green_price, "绿标")` 验证绿标价格
- 使用 `_validate_price(black_price, "黑标")` 验证黑标价格
- 只有验证通过的价格才添加到返回数据中

**实现要点**:
```python
# 在 _extract_basic_prices 中
if green_price is not None and self._validate_price(green_price, "绿标"):
    prices['green_price'] = green_price

if black_price is not None and self._validate_price(black_price, "黑标"):
    prices['black_price'] = black_price
```

### Requirement: Clean Code - No Dead Code

**描述**: OzonScraper 不应包含注释掉的废弃代码，保持代码库整洁。

**变更类型**: MODIFIED

**变更原因**: 
- 注释代码影响可读性
- 版本控制系统已经保存历史代码
- 废弃代码容易造成混淆

#### Scenario: 删除所有注释废弃代码

**Given**: OzonScraper 中存在注释掉的实验性代码  
**When**: 进行代码清理  
**Then**: 
- 删除所有被注释掉但不再使用的代码块
- 保留必要的解释性注释
- 通过 Git 历史可以找回删除的代码

### Requirement: Consistent Logging Format

**描述**: OzonScraper 的日志输出应该使用统一的格式和级别。

**变更类型**: MODIFIED

**变更原因**: 
- 当前日志格式不统一，影响日志分析
- 日志级别使用不一致

#### Scenario: 统一日志格式

**Given**: OzonScraper 需要记录各种操作日志  
**When**: 记录日志时  
**Then**: 
- 成功操作使用 `✅` 前缀，级别为 INFO
- 警告信息使用 `⚠️` 前缀，级别为 WARNING
- 错误信息使用 `❌` 前缀，级别为 ERROR
- 调试信息使用 `🔍` 前缀，级别为 DEBUG

**示例**:
```python
self.logger.info(f"✅ 绿标价格: {green_price}₽")
self.logger.warning(f"⚠️ 未找到黑标价格")
self.logger.error(f"❌ 提取价格数据失败: {e}")
self.logger.debug(f"🔍 使用选择器 '{selector}' 找到 {len(elements)} 个元素")
```

## 向后兼容性

- ✅ 所有公共方法签名保持不变
- ✅ 返回数据结构保持不变
- ✅ 外部调用方式不受影响
- ✅ 现有测试无需修改

## 性能影响

- ✅ 方法提取不影响性能（内联优化）
- ✅ 辅助方法调用开销可忽略（< 1%）
- ✅ 无新的性能瓶颈引入

## 测试要求

### 单元测试
- 现有的 `test_ozon_scraper_method.py` 必须全部通过
- 现有的 `test_ozon_competitor_scenarios_fixed.py` 必须全部通过

### 集成测试
- `test_erp_ozon_integration.py` 必须通过
- 端到端场景测试必须通过

### 回归测试
- 所有现有测试套件必须 100% 通过
- 无新的测试失败

## 文档要求

- 所有新增方法必须有完整的文档字符串
- 文档字符串包含：功能描述、参数说明、返回值说明
- 复杂逻辑需要添加行内注释说明
