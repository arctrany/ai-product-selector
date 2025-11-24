1. Populate your project context:
   "Please read openspec/project.md and help me fill it out
   with details about my project, tech stack, and conventions"

2. Create your first change proposal:
   "I want to add [YOUR FEATURE HERE]. Please create an
   OpenSpec change proposal for this feature"

3. Learn the OpenSpec workflow:
   "Please explain the OpenSpec workflow from openspec/AGENTS.md
   and how I should work with you on this project"# Python项目测试规范

## 1. 概述

本文档定义了项目的测试规范，包括测试文件组织、命名约定、目录结构、版本控制等方面的规范。

## 2. 测试框架和工具

- **测试框架**: pytest
- **代码覆盖率**: pytest-cov
- **Mock框架**: pytest-mock
- **断言库**: pytest内建断言

## 3. 测试目录结构

```
project/
├── src/
│   ├── module1/
│   └── module2/
├── tests/
│   ├── unit/                 # 单元测试
│   │   ├── test_module1.py
│   │   └── test_module2.py
│   ├── integration/          # 集成测试
│   │   ├── test_module1_integration.py
│   │   └── test_module2_integration.py
│   ├── functional/           # 功能测试
│   │   └── test_user_scenarios.py
│   ├── performance/          # 性能测试
│   │   └── test_benchmarks.py
│   ├── conftest.py           # pytest配置文件
│   └── fixtures/             # 测试夹具
│       └── test_data.json
└── requirements.txt
```

## 4. 测试文件命名规范

### 4.1 文件命名
- 单元测试文件: `test_*.py` 或 `*_test.py`
- 集成测试文件: `test_*_integration.py`
- 功能测试文件: `test_*_functional.py`
- 性能测试文件: `test_*_benchmark.py` 或 `test_*_performance.py`

### 4.2 类命名
- 测试类名: `Test*` (单元测试)
- 集成测试类名: `Test*Integration`
- 功能测试类名: `Test*Functional`

### 4.3 方法命名
- 测试方法: `test_*`
- 设置方法: `setup_method`
- 清理方法: `teardown_method`

## 5. 测试组织规范

### 5.1 按测试类型组织
1. **单元测试 (Unit Tests)**
   - 测试单个函数或类的方法
   - 不依赖外部系统
   - 运行速度快

2. **集成测试 (Integration Tests)**
   - 测试多个模块间的交互
   - 可能依赖数据库、网络等外部系统
   - 运行速度中等

3. **功能测试 (Functional Tests)**
   - 测试完整的业务功能
   - 模拟真实用户场景
   - 运行速度较慢

4. **性能测试 (Performance Tests)**
   - 测试系统性能指标
   - 包括响应时间、吞吐量等
   - 定期运行

### 5.2 按模块组织
- 每个源代码模块对应一个测试文件
- 测试文件与源文件保持相同的目录结构

## 6. 测试编写规范

### 6.1 测试结构
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

### 6.2 断言规范
- 使用明确的断言消息
- 优先使用pytest的内建断言
- 避免复杂的断言逻辑

### 6.3 Mock使用规范
- 使用pytest-mock插件
- 明确mock对象的行为
- 验证mock对象的调用

## 7. 测试数据管理

### 7.1 测试数据文件
- 存放在`tests/fixtures/`目录
- 使用JSON、YAML等格式存储
- 文件命名: `*.json`, `*_data.yaml`

### 7.2 测试数据策略
- 使用工厂模式创建测试数据
- 避免硬编码测试数据
- 使用参数化测试处理多种数据场景

## 8. 版本控制规范

### 8.1 测试代码提交
- 测试代码与功能代码一起提交
- 每个功能变更必须包含相应的测试
- 测试代码遵循与生产代码相同的代码规范

### 8.2 测试文件忽略
在`.gitignore`中添加:
```
# 测试生成文件
.tests/
.coverage
.pytest_cache/
```

## 9. 持续集成规范

### 9.1 测试执行
- 单元测试: 每次提交都运行
- 集成测试: 每日运行
- 性能测试: 定期运行

### 9.2 代码覆盖率
- 目标覆盖率: 80%以上
- 关键模块覆盖率: 90%以上
- 使用`pytest --cov`生成覆盖率报告

## 10. 测试文档规范

### 10.1 测试说明
- 每个测试类应有文档字符串说明测试目的
- 复杂测试应有详细注释说明测试逻辑

### 10.2 测试报告
- 使用pytest-html生成测试报告
- 定期审查测试结果和覆盖率

## 11. 实施指导

### 11.1 新增测试
1. 根据被测功能确定测试类型
2. 在对应目录创建测试文件
3. 编写测试用例覆盖所有场景
4. 运行测试确保通过
5. 检查代码覆盖率

### 11.2 测试维护
1. 功能变更时同步更新测试
2. 定期清理过时测试
3. 优化运行缓慢的测试
4. 重构重复测试代码

### 11.3 测试质量保证
1. 代码审查包含测试代码
2. 定期进行测试重构
3. 监控测试稳定性
4. 持续改进测试覆盖率