# 模型和配置架构统一 - 迁移指南

## 📋 概述

本指南帮助开发者从旧的混合架构迁移到新的统一模块化架构。重构主要解决了CLI/Task/Common模块间的冲突和冗余问题，实现了清晰的分层依赖和职责分离。

## 🎯 迁移目标

- **消除循环依赖**: 建立清晰的CLI → Common → RPA分层架构
- **模块化设计**: 将配置和模型按功能组织到独立目录
- **向后兼容**: 保持现有导入路径正常工作
- **代码质量**: 清理重复代码，统一实现标准

## 📁 目录结构变更

### Before (旧架构)
```
common/
├── models.py          # 混合了所有模型
├── config.py          # 混合了所有配置
├── logging_config.py  # 日志配置
└── utils/
    └── ...

cli/
├── models.py          # CLI专用模型
└── ...
```

### After (新架构)
```
common/
├── models/            # 🆕 数据模型目录
│   ├── __init__.py    # 向后兼容导出
│   ├── enums.py       # 系统枚举
│   ├── business_models.py      # 业务模型
│   ├── scraping_models.py      # 抓取模型
│   ├── excel_models.py         # Excel处理模型
│   └── exceptions.py           # 异常定义
├── config/            # 🆕 配置管理目录
│   ├── __init__.py    # 向后兼容导出
│   ├── base_config.py          # 基础配置
│   ├── system_config.py        # 系统技术配置
│   ├── business_config.py      # 业务配置
│   ├── ozon_selectors_config.py    # OZON选择器
│   ├── seerfar_selectors.py        # Seerfar选择器
│   └── erp_selectors_config.py     # ERP选择器
├── utils/
│   └── model_utils.py # 🆕 模型相关工具
├── logging_config.py  # 🆕 兼容性日志模块
└── ...

cli/
├── models.py          # CLI专用模型 (保持不变)
└── ...
```

## 🔄 导入路径迁移

### 数据模型

#### ✅ 推荐用法 (新路径)
```python
# 使用新的模块化导入
from common.models.business_models import StoreInfo, ProductInfo, PriceCalculationResult
from common.models.scraping_models import ScrapingResult, CompetitorDetectionResult
from common.models.enums import ScrapingStatus, FilterType
from common.models.exceptions import ScrapingException, ValidationException
```

#### 🔄 向后兼容 (旧路径仍可用)
```python
# 这些导入仍然可以正常工作
from common.models import StoreInfo, ProductInfo, ScrapingResult
from common.models import ScrapingStatus, FilterType
```

### 配置管理

#### ✅ 推荐用法 (新路径)
```python
# 使用新的配置层次结构
from common.config.base_config import GoodStoreSelectorConfig, BaseScrapingConfig
from common.config.system_config import LoggingConfig, PerformanceConfig
from common.config.business_config import FilterConfig, PriceConfig
from common.config.ozon_selectors_config import OzonSelectorsConfig
```

#### 🔄 向后兼容 (旧路径仍可用)
```python
# 这些导入仍然可以正常工作
from common.config import GoodStoreSelectorConfig
from common.config import OzonSelectorsConfig
```

### 工具函数

#### ✅ 推荐用法 (新工具)
```python
# 使用新的模型工具
from common.utils.model_utils import validate_store_id, validate_price
from common.utils.model_utils import format_currency, calculate_profit_rate

# 使用增强的抓取工具
from common.utils.scraping_utils import clean_price_string
```

### 日志系统

#### ✅ 推荐用法 (兼容性接口)
```python
# 兼容性日志接口，自动重定向到RPA日志系统
from common.logging_config import xuanping_logger, setup_logging, get_logger

# 使用方式保持不变
logger = get_logger("my_module")
logger.info("这是一条日志消息")
```

## ⚠️ 废弃警告

以下文件已被安全删除，请使用新的模块化导入：

### 🚫 已删除的文件
- ~~`common/models.py`~~ → 使用 `common/models/` 目录
- ~~`common/config.py`~~ → 使用 `common/config/` 目录  
- ~~原 `common/logging_config.py`~~ → 使用新的兼容性版本

### 📋 检查清单

在迁移过程中，请检查以下几点：

#### ✅ 导入语句更新
- [ ] 将模型导入迁移到 `common.models.*`
- [ ] 将配置导入迁移到 `common.config.*`
- [ ] 更新工具函数导入路径

#### ✅ 代码质量
- [ ] 移除重复的导入语句
- [ ] 使用新的工具函数替代重复代码
- [ ] 验证类型注解正确性

#### ✅ 测试验证
- [ ] 运行单元测试确保功能正常
- [ ] 验证配置加载正确
- [ ] 检查日志输出正常

## 🔧 常见问题解决

### Q1: 导入错误 "No module named 'common.models'"
**A:** 确保使用正确的导入路径，或使用向后兼容的接口：
```python
# 正确方式
from common.models.business_models import StoreInfo

# 或使用兼容接口  
from common.models import StoreInfo
```

### Q2: 配置文件找不到
**A:** 检查配置文件路径是否正确：
```python
# 推荐使用新的配置结构
from common.config.base_config import GoodStoreSelectorConfig
```

### Q3: 日志功能异常
**A:** 使用新的兼容性日志接口：
```python
from common.logging_config import get_logger
logger = get_logger("your_module")
```

### Q4: 类型检查错误
**A:** 更新类型注解，使用新的模型定义：
```python
from common.models.business_models import StoreInfo
from common.models.scraping_models import ScrapingResult

def process_store(store: StoreInfo) -> ScrapingResult:
    # ...
```

## 📈 性能优化建议

1. **使用具体导入**: 避免导入整个模块，只导入需要的类
2. **利用缓存**: 新的配置管理支持缓存机制
3. **减少重复代码**: 使用工具函数替代重复实现

## 🚀 迁移步骤

### 第一步：更新导入语句
```bash
# 全局搜索替换 (建议使用IDE的重构功能)
common.models → common.models.business_models
common.config → common.config.base_config
```

### 第二步：验证功能
```bash
# 运行测试
pytest tests/

# 检查代码质量
python -m pylint common/ cli/
```

### 第三步：清理代码
```bash
# 移除未使用的导入
python -m autoflake --remove-all-unused-imports --recursive .
```

## 📞 支持

如果在迁移过程中遇到问题：

1. **查看日志**: 新的日志系统提供详细的错误信息
2. **运行测试**: 使用测试套件验证功能
3. **查看文档**: 参考 `openspec/project.md` 获取详细架构信息

---

**🎯 迁移完成标志**: 所有导入正常工作，测试通过，无lint错误
