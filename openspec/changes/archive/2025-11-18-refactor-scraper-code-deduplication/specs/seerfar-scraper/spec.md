# Spec: Seerfar Scraper 重构

## MODIFIED Requirements

### Requirement: Eliminate Code Duplication

**描述**: SeerfarScraper 应该消除重复的代码逻辑，通过提取独立方法提高代码复用性。

**变更类型**: MODIFIED

**变更原因**: 
- 商品行去重逻辑在 `extract_products_async` 方法中重复出现两次
- page 对象验证逻辑在多个方法中重复
- 重复代码增加维护成本，容易引入不一致的bug

#### Scenario: 使用统一的去重方法

**Given**: SeerfarScraper 需要对商品行列表进行去重  
**When**: 调用 `_deduplicate_rows(rows)` 方法  
**Then**: 
- 基于 `data-index` 属性去重
- 如果元素没有 `data-index` 属性，也保留在结果中
- 返回去重后的商品行列表
- 保持原有顺序

**实现要点**:
```python
async def _deduplicate_rows(self, rows: list) -> list:
    """去重商品行，避免 CSS 和 XPath 选择器匹配到相同元素
    
    Args:
        rows: 商品行元素列表
        
    Returns:
        list: 去重后的商品行列表
    """
    seen_indices = set()
    unique_rows = []
    for row in rows:
        try:
            data_index = await row.get_attribute('data-index')
            if data_index and data_index not in seen_indices:
                seen_indices.add(data_index)
                unique_rows.append(row)
        except Exception:
            # 如果没有 data-index 属性，也加入列表
            unique_rows.append(row)
    return unique_rows
```

#### Scenario: 在商品列表提取中使用去重方法

**Given**: 在 `extract_products_async` 方法中获取商品行列表  
**When**: 需要对商品行去重时  
**Then**: 
- 第一次获取商品行后，调用 `product_rows = await self._deduplicate_rows(product_rows)`
- 循环中重新获取商品行后，调用 `unique_current_rows = await self._deduplicate_rows(current_rows)`
- 删除原有的内联去重逻辑（第394-407行和第416-428行）

#### Scenario: 使用统一的页面验证方法

**Given**: SeerfarScraper 需要验证 page 对象是否有效  
**When**: 调用 `_validate_page(page)` 方法  
**Then**: 
- 如果 page 为 None，记录错误日志并返回 False
- 如果 page 有效，返回 True
- 日志格式：`❌ page 对象为 None，浏览器可能未正确启动`

**实现要点**:
```python
def _validate_page(self, page) -> bool:
    """验证 page 对象是否有效
    
    Args:
        page: Playwright page 对象
        
    Returns:
        bool: page 是否有效
    """
    if page is None:
        self.logger.error("❌ page 对象为 None，浏览器可能未正确启动")
        return False
    return True
```

#### Scenario: 在多个方法中使用页面验证

**Given**: 在 `extract_products_async` 和 `_extract_product_from_row_async` 方法中需要验证 page  
**When**: 获取 page 对象后  
**Then**: 
- 使用 `if not self._validate_page(page): return []` 或 `return None`
- 删除原有的内联验证逻辑（第367-370行和第526-529行）

## ADDED Requirements

### Requirement: Shared Utility Methods

**描述**: 创建共享工具类 `ScraperUtils`，提供通用的数据提取和转换方法供多个抓取器使用。

**变更类型**: ADDED

**变更原因**: 
- `_extract_number_from_text` 方法是通用的数字提取逻辑
- 多个抓取器可能需要相同的功能
- 提取到共享类可以提高代码复用性和可维护性

#### Scenario: 创建 ScraperUtils 工具类

**Given**: 需要一个共享的工具类来存放通用方法  
**When**: 创建 `common/scrapers/scraper_utils.py` 文件  
**Then**: 
- 定义 `ScraperUtils` 类
- 实现 `extract_number_from_text` 静态方法
- 提供完整的文档字符串和类型注解

**实现要点**:
```python
# common/scrapers/scraper_utils.py
import re
from typing import Optional

class ScraperUtils:
    """抓取器通用工具类"""
    
    @staticmethod
    def extract_number_from_text(text: str) -> Optional[float]:
        """从文本中提取数字
        
        Args:
            text: 包含数字的文本
            
        Returns:
            float: 提取的数字，如果提取失败返回None
        """
        if not text:
            return None

        # 移除常见的非数字字符
        cleaned_text = re.sub(r'[^\d.,\-+]', '', text.replace(',', '').replace(' ', ''))

        try:
            # 尝试转换为浮点数
            return float(cleaned_text)
        except (ValueError, TypeError):
            # 尝试提取第一个数字
            numbers = re.findall(r'-?\d+\.?\d*', text)
            if numbers:
                try:
                    return float(numbers[0])
                except (ValueError, TypeError):
                    pass
            return None
```

#### Scenario: 在 SeerfarScraper 中使用共享工具方法

**Given**: SeerfarScraper 需要从文本中提取数字  
**When**: 调用数字提取功能时  
**Then**: 
- 导入 `ScraperUtils`：`from .scraper_utils import ScraperUtils`
- 使用 `ScraperUtils.extract_number_from_text(text)` 替代 `self._extract_number_from_text(text)`
- 删除 `SeerfarScraper._extract_number_from_text` 方法定义

**实现要点**:
```python
# 在 seerfar_scraper.py 顶部添加导入
from .scraper_utils import ScraperUtils

# 在需要提取数字的地方使用
price = ScraperUtils.extract_number_from_text(price_text)
```

### Requirement: Consistent Error Handling

**描述**: SeerfarScraper 的错误处理应该一致且清晰。

**变更类型**: MODIFIED

**变更原因**: 
- 提高代码可维护性
- 统一错误处理模式

#### Scenario: 统一异常处理格式

**Given**: SeerfarScraper 在各个方法中处理异常  
**When**: 捕获异常时  
**Then**: 
- 使用统一的日志格式：`❌ {操作}失败: {error}`
- 日志级别为 ERROR
- 返回合适的默认值（空列表、None等）

**示例**:
```python
except Exception as e:
    self.logger.error(f"❌ 提取商品列表失败: {e}")
    return []
```

## 向后兼容性

- ✅ 所有公共方法签名保持不变
- ✅ 返回数据结构保持不变
- ✅ 外部调用方式不受影响
- ✅ 现有测试无需修改

## 性能影响

- ✅ 方法提取不影响性能
- ✅ 去重逻辑性能保持不变（O(n)复杂度）
- ✅ 页面验证开销可忽略

## 测试要求

### 单元测试
- 现有的 `test_selection_modes.py` 必须全部通过
- 现有的 `test_selection_modes_real.py` 必须全部通过

### 功能测试
- Seerfar 商品列表抓取功能正常
- 商品行去重功能正常
- OZON 详情页跳转和数据提取正常

### 回归测试
- 所有现有测试套件必须 100% 通过
- 无新的测试失败
- 日志输出正常，无重复日志

## 代码质量要求

### 方法复杂度
- 所有方法的圈复杂度 < 10
- `extract_products_async` 方法复杂度降低（从当前的 ~15 降至 < 10）

### 代码行数
- 预期减少 50-80 行代码
- 方法平均长度减少

### 文档完整性
- 所有新增方法必须有完整的文档字符串
- 文档字符串包含：功能描述、参数说明、返回值说明
- 复杂逻辑需要添加行内注释说明

## 实施注意事项

### 重构顺序
1. 先添加新方法（`_deduplicate_rows`, `_validate_page`）
2. 再更新调用点使用新方法
3. 最后删除废弃代码

### 测试策略
- 每完成一个步骤立即运行测试
- 确保每个步骤都不破坏现有功能
- 使用 Git 小步提交，便于回滚

### 风险控制
- 保持外部接口不变
- 不修改业务逻辑
- 只进行代码结构优化
