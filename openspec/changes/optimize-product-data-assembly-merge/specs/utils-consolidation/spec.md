# 工具函数模块整合规格说明

## REMOVED Requirements

### Requirement: 删除冗余的工具函数模块
系统 MUST 删除以下冗余的工具函数模块文件：
- `common/models/utils.py`
- `common/utils/model_utils.py`

#### Scenario: 冗余文件清理验证
**Given** 项目代码库  
**When** 检查工具函数模块  
**Then** 不应该存在 `common/models/utils.py` 文件  
**And** 不应该存在 `common/utils/model_utils.py` 文件

## MODIFIED Requirements

### Requirement: 增强scraping_utils.py为统一工具函数库
`common/utils/scraping_utils.py` MUST 成为统一的工具函数库，包含所有模型相关的工具函数。

#### Scenario: 工具函数完整性验证
**Given** `common/utils/scraping_utils.py` 模块  
**When** 检查可用函数  
**Then** 必须包含以下函数：
- `validate_store_id(store_id: str) -> bool`
- `validate_price(price: Optional[float]) -> bool`  
- `validate_weight(weight: Optional[float]) -> bool`
- `clean_price_string(price_str: str, selectors_config=None) -> Optional[float]`
- `format_currency(amount: float, currency: str = '¥') -> str`
- `calculate_profit_rate(profit: float, cost: float) -> float`

#### Scenario: 函数功能一致性验证
**Given** 合并后的工具函数  
**When** 调用 `validate_store_id("123")`  
**Then** 应该返回 `True` 对于有效的店铺ID  
**And** 应该返回 `False` 对于空字符串或None

**Given** 合并后的工具函数  
**When** 调用 `validate_price(100.0)`  
**Then** 应该返回 `True` 对于正数价格  
**And** 应该返回 `False` 对于负数价格

**Given** 合并后的工具函数  
**When** 调用 `clean_price_string("100 ₽")`  
**Then** 应该返回 `100.0`  
**And** 应该正确处理俄语货币符号和格式

### Requirement: 维持向后兼容性导入路径
`common/models/__init__.py` MUST 提供向后兼容的导入路径，确保现有代码无需修改。

#### Scenario: 向后兼容性导入验证
**Given** 现有代码使用 `from common.models import validate_store_id`  
**When** 执行导入语句  
**Then** 应该成功导入函数而不报错  
**And** 函数功能应该与原来完全一致

#### Scenario: 统一导入路径验证  
**Given** 新的统一导入路径  
**When** 使用 `from common.utils.scraping_utils import validate_store_id`  
**Then** 应该成功导入相同的函数  
**And** 函数行为应该与兼容性导入完全一致

## ADDED Requirements

### Requirement: 导入路径重定向机制
`common/models/__init__.py` MUST 实现导入路径重定向，将工具函数导入指向统一的 `scraping_utils` 模块。

#### Scenario: 导入重定向实现
**Given** `common/models/__init__.py` 文件  
**When** 检查工具函数的导入语句  
**Then** 应该包含类似以下的重定向导入：
```python
from ..utils.scraping_utils import (
    validate_store_id,
    validate_price,
    validate_weight,
    clean_price_string,
    format_currency,
    calculate_profit_rate
)
```

### Requirement: 函数合并完整性验证
合并过程 MUST 确保所有函数的完整功能都被保留，特别是复杂的 `clean_price_string` 函数。

#### Scenario: clean_price_string功能保留验证
**Given** 合并后的 `clean_price_string` 函数  
**When** 处理复杂的俄语价格格式 "от 1 000 ₽"  
**Then** 应该正确提取数值 `1000.0`  
**And** 应该正确处理配置化的货币符号  
**And** 应该正确处理特殊空格字符和千位分隔符

#### Scenario: 所有验证函数功能保留
**Given** 合并后的验证函数  
**When** 测试边界条件和异常情况  
**Then** `validate_weight(0)` 应该返回 `False`  
**And** `validate_price(None)` 应该返回 `True`  
**And** `format_currency(123.456)` 应该返回格式化的货币字符串

### Requirement: 测试覆盖率维持
合并后的工具函数 MUST 维持原有的测试覆盖率，确保所有功能都有相应的测试。

#### Scenario: 测试用例迁移验证
**Given** 原有的工具函数测试用例  
**When** 更新测试导入路径指向合并后的模块  
**Then** 所有测试用例应该继续通过  
**And** 测试覆盖率不应该下降  
**And** 应该添加针对合并过程的额外测试用例