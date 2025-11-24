# Change: Python项目测试组织规范重构

## Why
当前项目的测试文件组织缺乏系统性规范，存在测试目录结构与源代码不对应、重复测试文件（如test_XXX_fixed.py）等问题，导致测试维护困难和执行不稳定。需要建立规范化的测试组织体系。

## What Changes
- 建立测试目录结构与源代码目录一一对应的规范
- 禁止创建test_XXX_fixed.py等多版本测试文件
- 重组现有测试文件到对应的目录结构
- 删除重复和冗余的测试文件
- 制定跨平台兼容性测试标准
- 确保单元测试和端到端测试成功执行
- **BREAKING**: 测试文件目录结构将发生重大变更

## Impact
- Affected specs: 新增testing规范
- Affected code: 
  - tests/目录下所有58个测试文件需要重组
  - CLI模块测试 (cli/ → tests/cli/)
  - Common模块测试 (common/ → tests/common/)
  - Task Manager模块测试 (task_manager/ → tests/task_manager/)
  - Utils模块测试 (utils/ → tests/utils/)
  - RPA模块测试 (rpa/ → tests/rpa/)
  - 删除重复测试文件：test_selection_modes_real.py
