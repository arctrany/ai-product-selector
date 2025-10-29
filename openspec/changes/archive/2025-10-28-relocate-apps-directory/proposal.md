## Why

当前项目的应用目录位于 `src_new/apps`，这种结构导致了以下问题：
1. **路径硬编码风险**：当前代码中存在硬编码路径 `'src_new/apps'`，违反了配置管理最佳实践
2. **模块导入复杂性**：应用的 `entry_point` 配置使用硬编码的模块路径前缀，增加了维护复杂性
3. **部署不便**：应用作为独立的业务逻辑单元，应该与核心引擎代码分离，便于独立部署和管理
4. **架构清晰度**：应用层逻辑与引擎核心代码混合，违反了分层架构原则
5. **函数注册问题**：当前 `AppManager` 在加载工作流时需要复杂的路径推导来正确导入和注册节点函数
6. **代码冗余问题**：存在多处重复的路径处理逻辑和配置读取代码
7. **规范违反**：硬编码字符串、魔法数字等不符合代码规范的实现

将 `apps` 目录移动到项目根目录并清理代码可以：
- 消除路径硬编码，提高配置灵活性
- 简化模块导入路径和函数注册逻辑
- 提高项目结构的清晰度和可维护性
- 便于应用的独立部署和版本管理
- 符合项目规范中关于目录结构的最佳实践
- **清理冗余实现**，减少重复代码和维护成本
- **规范化代码**，消除硬编码和不规范的实现

## What Changes

### 核心变更
- **BREAKING**: 将 `src_new/apps/` 目录移动到项目根目录 `apps/`
- **BREAKING**: 更新 `app.json` 中的 `entry_point` 配置格式，移除硬编码的模块路径前缀
- 消除所有路径硬编码，改用动态配置和环境变量
- 更新 `AppManager` 的模块路径解析逻辑，支持新的目录结构
- 修改配置管理系统，将默认应用目录从 `'src_new/apps'` 改为 `'apps'`
- 增强函数注册机制，确保新路径下的节点函数能正确加载和注册
- 更新所有相关的路径解析逻辑以支持新的应用目录位置
- 确保向后兼容性，支持环境变量覆盖应用目录位置

### 代码清理和规范化
- **清理冗余实现**：
  - **确认的重复代码**：`normalize_path` 函数在以下文件中重复实现：
    - `src_new/utils/windows_compat.py` (主实现)
    - `src_new/workflow_engine/apps/manager.py` (fallback实现，第17-20行)
    - `src_new/workflow_engine/api/app_routes.py` (fallback实现，第24-26行)
    - `bin/workflow_server.py` (fallback实现，第28-30行)
    - `bin/windows_compatibility_check.py` (重复实现，第355-364行)
  - 移除重复的配置读取代码，统一使用 `ConfigManager.get_apps_directory_path()`
  - 清理未使用的导入和变量
  - 合并相似的错误处理逻辑和日志记录模式
  - 统一路径解析逻辑，避免在 `AppManager` 和 `WorkflowEngineConfig` 中重复实现
- **消除硬编码**：
  - **关键问题**：`src_new/workflow_engine/core/config.py` 第56行存在硬编码路径 `'src_new/apps'`
  - **关键问题**：`WorkflowEngineConfig.get_apps_directory_path()` 和 `ConfigManager.get_apps_directory_path()` 重复实现相同逻辑
  - **具体硬编码示例**：`apps_dir = os.getenv('WORKFLOW_APPS_DIR', 'src_new/apps')` 需要改为 `'apps'`
  - **app.json配置硬编码**：当前 `entry_point` 使用硬编码前缀 `"apps.sample_app.flow1.imp.workflow_definition:create_flow1_workflow"`
  - 将所有硬编码路径替换为配置常量，定义 `DEFAULT_APPS_DIR = 'apps'`
  - 将魔法数字提取为命名常量
  - 将硬编码字符串提取为配置项或常量
- **规范化实现**：
  - 统一命名规范（变量名、函数名、类名）
  - 标准化错误处理和日志记录
  - 优化导入语句的组织和顺序
  - 添加必要的类型注解和文档字符串
  - 统一使用 `Path` 对象进行路径操作，避免字符串拼接
- **架构优化**：
  - 移除 `WorkflowEngineConfig` 和 `ConfigManager` 中重复的路径获取方法
  - 统一使用 `ConfigManager` 作为配置访问的单一入口
  - 简化 `AppManager` 中的动态路径解析逻辑（第36-38行的复杂路径构建）
  - 优化文件系统访问的缓存机制

### 向后兼容性保障
- 保留对旧路径的检测和警告机制
- 支持旧配置格式的自动转换
- 提供渐进式迁移工具和指南

## Impact

### 受影响的规范
- 项目架构、配置管理、应用管理
- 代码规范和最佳实践

### 受影响的代码文件
- **核心配置系统**:
  - `src_new/workflow_engine/core/config.py` - **关键**：第56行硬编码路径 `'src_new/apps'` 需要改为 `'apps'`
  - `src_new/workflow_engine/core/config.py` - **重复实现**：`WorkflowEngineConfig.get_apps_directory_path()` 与 `ConfigManager.get_apps_directory_path()` 重复
- **应用管理系统**:
  - `src_new/workflow_engine/apps/manager.py` - 应用管理器的路径解析逻辑和动态模块路径构建（第36-38行）
  - `src_new/apps/sample_app/app.json` - **具体配置**：`entry_point` 当前为 `"apps.sample_app.flow1.imp.workflow_definition:create_flow1_workflow"`，需要移除硬编码前缀
- **工具和实用程序**:
  - `src_new/utils/windows_compat.py` - 主要的路径处理工具函数实现
  - `src_new/workflow_engine/apps/manager.py` - **重复实现**：第17-20行的 `normalize_path` fallback实现
  - `src_new/workflow_engine/api/app_routes.py` - **重复实现**：第24-26行的 `normalize_path` fallback实现
  - `bin/workflow_server.py` - **重复实现**：第28-30行的 `normalize_path` fallback实现
  - `bin/windows_compatibility_check.py` - **完全重复**：第355-364行完整重复了 `normalize_path` 实现
  - `src_new/workflow_engine/sdk/env.py` - 配置文件搜索逻辑
- **启动脚本**:
  - `bin/workflow_server.py` - 服务器启动脚本的路径配置（第44-47行使用 `normalize_path`）
- **API路由系统**:
  - `src_new/workflow_engine/api/app_routes.py` - 35处 `normalize_path` 调用，需要统一路径处理
- **测试文件**:
  - 所有测试文件中的应用路径引用和配置

### 代码质量改进影响
- **消除重复代码**：多个文件中的路径处理逻辑将统一
- **提高可维护性**：硬编码路径集中管理，便于修改
- **增强一致性**：统一的配置访问模式和错误处理
- **改善性能**：减少重复的文件系统访问和路径计算

### 部署和开发影响
- **部署影响**: 需要更新部署脚本和配置以反映新的目录结构
- **开发影响**: 开发者需要更新本地环境配置和IDE设置
- **迁移影响**: 提供自动化迁移工具，减少手动操作
- **向后兼容**: 保持对旧路径的检测和警告，确保平滑过渡