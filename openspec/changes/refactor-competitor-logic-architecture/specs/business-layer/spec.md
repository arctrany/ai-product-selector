# Spec: 业务层目录重组

## Summary

将业务逻辑模块从数据抓取层分离，创建独立的 `business/` 目录，并将 `filter_manager.py` 从 `common/scrapers/` 移动到项目根目录下的 `business/` 目录，明确业务逻辑和数据抓取的职责边界。

## Motivation

### 当前问题
- **职责混乱**: `filter_manager.py` 包含店铺和商品过滤的业务逻辑，但位于数据抓取层 `common/scrapers/`
- **架构不清**: 业务逻辑与数据抓取混在一起，违反分层架构原则
- **维护困难**: 业务逻辑分散在不同目录，难以统一管理和维护

### 预期收益
- **职责分离**: 明确业务逻辑和数据抓取的边界，符合分层架构原则
- **结构清晰**: 统一的业务逻辑目录，提高代码组织的逻辑性
- **维护性提升**: 业务逻辑集中管理，便于后续扩展和维护

## Detailed Design

### 目录结构重组

#### 现有结构
```
common/
├── scrapers/
│   ├── filter_manager.py      # ❌ 业务逻辑放在抓取层
│   ├── seerfar_scraper.py
│   ├── ozon_scraper.py
│   └── competitor_scraper.py
└── services/
    └── competitor_detection_service.py
```

#### 目标结构
```
# 项目根目录结构重组
business/                      # ✅ 新增业务层目录（项目根目录下）
├── __init__.py
├── filter_manager.py          # ✅ 从 common/scrapers/ 移动过来
├── profit_evaluator.py        # ✅ 利润评估业务逻辑
└── store_evaluator.py         # ✅ 店铺评估业务逻辑

common/
├── scrapers/                  # ✅ 纯数据抓取层
│   ├── seerfar_scraper.py
│   ├── ozon_scraper.py
│   └── competitor_scraper.py
└── services/                  # ✅ 服务层
    └── competitor_detection_service.py
```

### 模块迁移计划

#### filter_manager.py 迁移
```python
# 迁移前导入路径
from common.scrapers.filter_manager import FilterManager

# 迁移后导入路径  
from business.filter_manager import FilterManager
```

#### 业务模块设计
```python
# business/__init__.py
"""
业务层模块

职责：
- 店铺过滤和评估逻辑
- 商品过滤和评估逻辑  
- 利润计算和分析逻辑
- 业务规则和策略管理
"""

from .filter_manager import FilterManager
from .profit_evaluator import ProfitEvaluator
from .store_evaluator import StoreEvaluator

__all__ = [
    'FilterManager',
    'ProfitEvaluator', 
    'StoreEvaluator'
]
```

### 依赖关系重构

#### 更新导入引用
所有引用 `filter_manager` 的文件需要更新：

```python
# 需要更新的文件和路径
- competitor_detection_service.py
- good_store_selector.py  
- 相关测试文件
- 配置文件

# 更新方式
- from common.scrapers.filter_manager -> from business.filter_manager
```

#### 分层调用关系
```python
# 正确的分层调用关系
协调层 -> 服务层 -> 业务层 -> 抓取层

# 具体实现
good_store_selector.py (协调层)
    ↓
competitor_detection_service.py (服务层)
    ↓
business/filter_manager.py (业务层)
    ↓
common/scrapers/*.py (抓取层)
```

## Requirements

### ADDED

#### REQ-001: 业务目录创建
**Status**: ADDED  
**Description**: 在项目根目录下创建独立的 `business/` 目录
- 创建 `business/` 目录结构
- 添加 `__init__.py` 模块初始化文件
- 建立业务层模块导出接口

#### REQ-002: filter_manager 迁移
**Status**: ADDED  
**Description**: 将 `filter_manager.py` 从 `common/scrapers/` 移动到 `business/`
- 物理移动文件到新位置
- 保持文件内容和功能完全不变
- 确保文件权限和编码格式不变

#### REQ-003: 导入路径更新
**Status**: ADDED  
**Description**: 更新所有对 `filter_manager` 的导入引用
- 搜索并定位所有导入 `common.scrapers.filter_manager` 的文件
- 批量更新为 `business.filter_manager`
- 验证更新后的导入路径正确性

#### REQ-004: 业务模块扩展
**Status**: ADDED  
**Description**: 为未来业务逻辑预留扩展空间
- 设计 `profit_evaluator.py` 模块接口
- 设计 `store_evaluator.py` 模块接口  
- 建立业务模块的标准化结构

#### REQ-005: 向后兼容处理
**Status**: ADDED  
**Description**: 处理迁移过程中的向后兼容性
- 在 `common/scrapers/` 保留临时的兼容性引用
- 添加废弃警告提示
- 制定兼容性引用的移除时间表

## Testing Strategy

### 功能测试
- **导入测试**: 验证所有新的导入路径正常工作
- **功能验证**: 确保 `filter_manager` 迁移后功能完全一致
- **集成测试**: 验证整个业务流程在重组后正常运行

### 回归测试
- **现有测试**: 运行所有现有测试用例，确保无回归
- **导入测试**: 专门测试新旧导入路径的兼容性
- **跨平台测试**: 验证 Windows/Linux/macOS 路径兼容性

### 测试覆盖率目标
- 迁移后功能测试覆盖率 = 100%
- 导入路径测试覆盖率 = 100%  
- 整体回归测试通过率 = 100%

## Rollout Plan

### 阶段1: 目录结构准备 (1天)
- 创建 `business/` 目录
- 添加 `__init__.py` 和模块接口
- 准备扩展模块的基础结构

### 阶段2: 文件迁移 (1天)
- 将 `filter_manager.py` 移动到 `business/`
- 更新所有导入引用  
- 添加向后兼容性处理

### 阶段3: 测试验证 (1天)
- 全面功能测试和回归测试
- 跨平台兼容性验证
- 性能基准测试

### 阶段4: 清理优化 (1天)
- 移除临时兼容性代码
- 优化业务层模块结构
- 更新相关文档

### 风险缓解
- **分阶段迁移**: 降低风险，便于回滚
- **充分测试**: 每个阶段都有完整测试验证
- **向后兼容**: 保证迁移过程中系统稳定性

## Migration Guide

### 开发者迁移指南

#### 导入路径更新
```python
# 旧的导入方式（需要更新）
from common.scrapers.filter_manager import FilterManager

# 新的导入方式
from business.filter_manager import FilterManager
```

#### IDE 支持
- **批量替换**: 使用 IDE 的"查找替换"功能批量更新
- **重构工具**: 利用 IDE 的重构功能安全迁移
- **导入优化**: 使用 IDE 的导入优化功能清理无用导入

#### 测试文件更新
```python
# 测试文件中的导入也需要更新
# test_*.py 文件中的所有相关导入路径
```

### 自动化迁移脚本
```bash
#!/bin/bash
# migrate_business_layer.sh

# 1. 创建目录结构
mkdir -p business

# 2. 移动文件
mv common/scrapers/filter_manager.py business/

# 3. 创建 __init__.py
cat > business/__init__.py << 'EOF'
from .filter_manager import FilterManager
__all__ = ['FilterManager']
EOF

# 4. 批量更新导入路径
find . -name "*.py" -exec sed -i 's/from common\.scrapers\.filter_manager/from business.filter_manager/g' {} \;
find . -name "*.py" -exec sed -i 's/import common\.scrapers\.filter_manager/import business.filter_manager/g' {} \;
```

## Metrics

### 成功指标
- ✅ `business/` 目录成功创建
- ✅ `filter_manager.py` 成功迁移至新位置
- ✅ 所有导入引用更新完成
- ✅ 所有测试用例通过
- ✅ 零功能回归问题

### 监控指标
- 导入错误日志数量 = 0
- 业务功能异常数量 = 0  
- 模块加载时间变化 < 5%
- 代码重复率变化情况

### 质量验证
- 代码审查通过率 = 100%
- 自动化测试通过率 = 100%
- 手动测试验收通过率 = 100%
