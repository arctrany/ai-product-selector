# 测试重组计划

## 目标
重新组织现有的测试文件结构，使其符合新的测试组织规范。

## 重组步骤

### 第一阶段：分析现有测试文件
1. 分析根目录下的所有测试文件
2. 确定每个测试文件对应的源代码模块
3. 分类测试文件类型（单元测试、集成测试、端到端测试）

### 第二阶段：创建目标目录结构
1. 确保所有必要的测试目录都已创建
2. 创建缺失的目录结构

### 第三阶段：迁移测试文件
1. 将测试文件移动到对应的目录
2. 重命名不符合规范的测试文件
3. 更新测试文件中的导入路径

### 第四阶段：验证
1. 确保所有测试仍能正常运行
2. 更新测试配置文件
3. 文档化变更

## 详细迁移映射

### CLI相关测试
- `test_cli_main.py` → `tests/cli/test_main.py`
- `test_cli_flags.py` → `tests/cli/test_flags.py`
- `test_cli_xp_cli.py` → `tests/cli/test_xp_cli.py`

### Common模块测试
- `test_models_enums.py` → `tests/common/models/test_enums.py`
- `test_config_user.py` → `tests/common/config/test_user.py`
- `test_wait_utils.py` → `tests/common/utils/test_wait_utils.py`

### 集成测试
- `test_integration_end_to_end.py` → `tests/integration/test_end_to_end.py`
- `test_scraping_integration.py` → `tests/integration/test_scraping.py`

### 端到端测试
- 端到端测试将放置在 `tests/e2e/` 目录中
