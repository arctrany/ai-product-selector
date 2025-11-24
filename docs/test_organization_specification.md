# Python项目测试组织规范

## 1. 概述

本文档定义了项目的测试组织规范，包括测试目录结构、命名约定、版本控制、质量标准等方面的规范，确保测试代码与源代码保持一一对应的关系。

## 2. 测试框架和工具

- **测试框架**: pytest
- **代码覆盖率**: pytest-cov
- **Mock框架**: pytest-mock
- **断言库**: pytest内建断言

## 3. 测试目录结构规范

### 3.1 目录结构设计原则

测试目录结构必须与源代码目录结构保持一一对应关系，确保每个源代码模块都有对应的测试文件。

```
project/
├── cli/                          # CLI模块
│   ├── main.py
│   └── models.py
├── common/                       # 核心业务模块
│   ├── config/
│   │   └── base_config.py
│   ├── models/
│   │   └── business_models.py
│   ├── business/
│   │   └── pricing_calculator.py
│   └── scrapers/
│       └── ozon_scraper.py
├── rpa/                          # RPA自动化模块
│   └── browser_service.py
├── tests/                        # 测试根目录
│   ├── __init__.py
│   ├── conftest.py              # pytest配置文件
│   ├── fixtures/                # 测试数据夹具
│   │   └── test_data.json
│   ├── cli/                     # CLI模块测试 (与源码目录一一对应)
│   │   ├── test_main.py
│   │   └── test_models.py
│   ├── common/                  # 核心业务模块测试 (与源码目录一一对应)
│   │   ├── config/
│   │   │   └── test_base_config.py
│   │   ├── models/
│   │   │   └── test_business_models.py
│   │   ├── business/
│   │   │   └── test_pricing_calculator.py
│   │   └── scrapers/
│   │       └── test_ozon_scraper.py
│   ├── rpa/                     # RPA模块测试 (与源码目录一一对应)
│   │   └── test_browser_service.py
│   └── test_data/               # 测试数据文件
│       └── sample_data.xlsx
└── requirements.txt
```

### 3.2 目录结构强制要求

1. **一一对应原则**: 每个源代码文件必须有对应的测试文件，目录结构完全一致
2. **测试根目录**: 所有测试文件必须放在`tests/`目录下
3. **模块隔离**: 不同模块的测试文件必须放在对应的子目录中
4. **数据分离**: 测试数据必须放在`tests/test_data/`目录中

## 4. 测试文件命名规范

### 4.1 文件命名规则

- **单元测试文件**: `test_*.py` (前缀命名法)
- **集成测试文件**: `test_*_integration.py`
- **功能测试文件**: `test_*_functional.py`
- **性能测试文件**: `test_*_benchmark.py` 或 `test_*_performance.py`

### 4.2 类命名规则

- **测试类名**: `Test*` (单元测试)
- **集成测试类名**: `Test*Integration`
- **功能测试类名**: `Test*Functional`

### 4.3 方法命名规则

- **测试方法**: `test_*`
- **设置方法**: `setup_method` 或 `setup_class`
- **清理方法**: `teardown_method` 或 `teardown_class`

### 4.4 命名示例

```
# 源代码文件
common/business/pricing_calculator.py

# 对应测试文件
tests/common/business/test_pricing_calculator.py

# 测试类名
class TestPricingCalculator:

# 测试方法名
def test_calculate_green_price_success(self):
def test_calculate_green_price_invalid_input(self):
```

## 5. 测试组织规范

### 5.1 按测试类型组织

1. **单元测试 (Unit Tests)**
   - 测试单个函数或类的方法
   - 不依赖外部系统
   - 运行速度快
   - 命名: `test_*.py`

2. **集成测试 (Integration Tests)**
   - 测试多个模块间的交互
   - 可能依赖数据库、网络等外部系统
   - 运行速度中等
   - 命名: `test_*_integration.py`

3. **功能测试 (Functional Tests)**
   - 测试完整的业务功能
   - 模拟真实用户场景
   - 运行速度较慢
   - 命名: `test_*_functional.py`

4. **性能测试 (Performance Tests)**
   - 测试系统性能指标
   - 包括响应时间、吞吐量等
   - 定期运行
   - 命名: `test_*_benchmark.py` 或 `test_*_performance.py`

### 5.2 按模块组织

- 每个源代码模块对应一个测试文件
- 测试文件与源文件保持相同的目录结构
- 禁止创建与源代码结构不一致的测试文件

## 6. 版本控制规范

### 6.1 测试代码提交规范

- **提交原则**: 测试代码与功能代码一起提交
- **覆盖率要求**: 每个功能变更必须包含相应的测试
- **代码规范**: 测试代码遵循与生产代码相同的代码规范
- **提交信息**: 使用语义化提交信息 (test: add unit tests for pricing calculator)

### 6.2 禁止创建多版本测试文件

**严格禁止**创建以下类型的测试文件：
- ❌ `test_XXX_fixed.py` - 修复版本测试文件
- ❌ `test_XXX_v2.py` - 版本化测试文件
- ❌ `test_XXX_backup.py` - 备份测试文件
- ❌ `test_XXX_old.py` - 旧版本测试文件
- ❌ `test_XXX_new.py` - 新版本测试文件

**正确做法**:
- ✅ 直接修改原有测试文件
- ✅ 使用Git版本控制管理历史变更
- ✅ 重大重构前创建feature分支
- ✅ 使用Git stash临时保存代码

### 6.3 测试文件忽略规则

在`.gitignore`中添加:
```
# 测试生成文件
.tests/
.coverage
.pytest_cache/
__pycache__/
*.pyc
```

## 7. 测试编写规范

### 7.1 测试结构规范

```python
class TestModuleName:
    """模块功能测试"""
    
    def setup_method(self):
        """测试前准备"""
        # 初始化测试数据和对象
        pass
    
    def teardown_method(self):
        """测试后清理"""
        # 清理测试数据和对象
        pass
    
    def test_feature_success_case(self):
        """测试功能成功场景"""
        # Arrange - 准备测试数据
        # Act - 执行被测功能
        # Assert - 验证结果
        pass
    
    def test_feature_error_case(self):
        """测试功能错误场景"""
        # Arrange - 准备测试数据
        # Act & Assert - 执行并验证异常
        pass
```

### 7.2 断言规范

- 使用明确的断言消息
- 优先使用pytest的内建断言
- 避免复杂的断言逻辑

### 7.3 Mock使用规范

- 使用pytest-mock插件
- 明确mock对象的行为
- 验证mock对象的调用

## 8. 测试数据管理

### 8.1 测试数据文件

- 存放在`tests/test_data/`目录
- 使用JSON、YAML等格式存储
- 文件命名: `*.json`, `*_data.yaml`

### 8.2 测试数据策略

- 使用工厂模式创建测试数据
- 避免硬编码测试数据
- 使用参数化测试处理多种数据场景

## 9. 测试覆盖率要求和质量标准

### 9.1 覆盖率目标

- **总体覆盖率**: ≥ 80%
- **核心业务模块覆盖率**: ≥ 90%
- **关键路径覆盖率**: = 100%
  - 利润计算模块
  - 价格计算模块
  - 店铺评估模块

### 9.2 质量标准

1. **测试完整性**
   - 每个公共方法至少有一个测试用例
   - 覆盖正常路径、异常路径、边界条件
   - 包含成功场景和失败场景

2. **测试独立性**
   - 测试之间不能相互依赖
   - 每个测试应能独立运行
   - 使用setup/teardown确保环境清洁

3. **测试可读性**
   - 测试名称应清晰描述测试内容
   - 包含适当的注释说明测试目的
   - 遵循统一的代码风格

### 9.3 持续集成规范

- **单元测试**: 每次提交都运行
- **集成测试**: 每日运行
- **性能测试**: 定期运行
- **覆盖率检查**: 使用`pytest --cov`生成覆盖率报告

## 10. 实施指导

### 10.1 新增测试流程

1. 根据被测功能确定测试类型
2. 在对应目录创建测试文件（遵循一一对应原则）
3. 编写测试用例覆盖所有场景
4. 运行测试确保通过
5. 检查代码覆盖率是否达标

### 10.2 测试维护流程

1. 功能变更时同步更新测试
2. 定期清理过时测试
3. 优化运行缓慢的测试
4. 重构重复测试代码

### 10.3 测试质量保证

1. 代码审查包含测试代码
2. 定期进行测试重构
3. 监控测试稳定性
4. 持续改进测试覆盖率

## 11. 违规处理

### 11.1 违规行为定义

以下行为被视为违反测试组织规范：
1. 创建`test_XXX_fixed.py`等多版本测试文件
2. 测试目录结构与源代码结构不一致
3. 测试文件命名不符合规范
4. 测试覆盖率未达到最低要求
5. 提交包含无效或过时的测试文件

### 11.2 处理措施

1. **首次违规**: 警告并要求立即整改
2. **重复违规**: 暂停代码提交权限直至完成培训
3. **严重违规**: 需要技术负责人审批后方可提交

## 12. 附录

### 12.1 常用测试命令

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/common/business/test_pricing_calculator.py

# 运行测试并生成覆盖率报告
pytest --cov=common --cov=rpa --cov-report=html

# 运行测试并显示覆盖率
pytest --cov=common --cov=rpa --cov-report=term-missing
```

### 12.2 测试文件模板

```python
"""
{模块名}测试套件

测试{模块功能描述}
"""

import pytest
from unittest.mock import Mock, patch

# 导入被测模块
from common.business.pricing_calculator import PricingCalculator

class TestPricingCalculator:
    """PricingCalculator功能测试"""
    
    def setup_method(self):
        """测试初始化"""
        self.calculator = PricingCalculator()
    
    def test_calculate_green_price_success(self):
        """测试成功计算绿标价格"""
        # Arrange
        black_price = 1000.0
        expected_green_price = 950.0  # 95折
        
        # Act
        result = self.calculator.calculate_green_price(black_price)
        
        # Assert
        assert result == expected_green_price
    
    def test_calculate_green_price_invalid_input(self):
        """测试无效输入计算绿标价格"""
        # Arrange
        invalid_price = -100.0
        
        # Act & Assert
        with pytest.raises(ValueError):
            self.calculator.calculate_green_price(invalid_price)
```
