# 应用目录重定位测试计划

## 测试策略概述

根据 `project.md` 的测试要求，本测试计划覆盖应用目录从 `src_new/apps` 迁移到项目根目录 `apps/` 的所有变动范围，确保系统功能完整性和稳定性。

## 测试分类与覆盖范围

### 1. 单元测试 (Unit Tests)

#### 1.1 配置管理测试
**测试文件**: `tests/test_config_apps_relocation.py`
**覆盖组件**:
- `WorkflowEngineConfig.get_apps_directory_path()`
- `ConfigManager.get_apps_directory_path()`
- 环境变量 `WORKFLOW_APPS_DIR` 处理逻辑

**测试场景**:
- 默认应用目录路径解析（从 `src_new/apps` 到 `apps`）
- 环境变量覆盖功能验证
- 相对路径和绝对路径处理
- 跨平台路径兼容性（Windows/macOS/Linux）
- 配置加载器的路径展开功能

#### 1.2 应用管理器测试
**测试文件**: `tests/test_app_manager_relocation.py`
**覆盖组件**:
- `AppManager.__init__()` 路径初始化
- `AppManager._determine_root_module_path()`
- `AppManager.load_workflow_definition()`
- 模块导入路径构建逻辑

**测试场景**:
- 应用目录自动发现和加载
- 动态模块路径解析
- `app.json` 配置格式兼容性（新旧格式）
- 工作流定义加载和模块导入
- 节点模块自动发现机制
- 错误处理和降级策略

#### 1.3 函数注册机制测试
**测试文件**: `tests/test_function_registry_relocation.py`
**覆盖组件**:
- `@register_function` 装饰器
- 函数注册表管理
- 模块导入和函数解析

**测试场景**:
- 新路径下函数注册正常工作
- 函数引用解析准确性
- 装饰器执行时机验证
- 函数调用链完整性
- 注册表状态一致性

### 2. 集成测试 (Integration Tests)

#### 2.1 工作流引擎集成测试
**测试文件**: `tests/test_workflow_engine_apps_integration.py`
**覆盖范围**:
- 完整的工作流加载和执行流程
- 应用管理器与工作流引擎协作
- 数据库存储和检索功能

**测试场景**:
- 端到端工作流执行（从应用加载到任务完成）
- 工作流状态持久化和恢复
- 多应用并发加载和执行
- 检查点机制在新路径下的正常工作
- WebSocket 实时通信功能

#### 2.2 服务器启动集成测试
**测试文件**: `tests/test_server_startup_apps_relocation.py`
**覆盖范围**:
- 服务器初始化流程
- 应用引导和注册过程
- 依赖注入容器配置

**测试场景**:
- 服务器正常启动和应用加载
- 应用路径配置正确传递
- 路由注册和API端点可用性
- 静态资源和模板加载
- 健康检查端点响应

### 3. API测试 (API Tests)

#### 3.1 应用管理API测试
**测试文件**: `tests/test_app_routes_relocation.py`
**覆盖端点**:
- `GET /apps` - 应用列表
- `GET /apps/{app_id}` - 应用详情
- `GET /apps/{app_id}/flows/{flow_id}` - 工作流详情
- `POST /apps/{app_id}/flows/{flow_id}/start` - 启动工作流

**测试场景**:
- 应用列表正确返回
- 应用元数据完整性
- 工作流配置访问
- 文件路径解析准确性
- 错误处理和状态码

#### 3.2 控制台API测试
**测试文件**: `tests/test_console_routes_relocation.py`
**覆盖端点**:
- `GET /` - 控制台主页
- `GET /console/stats` - 统计信息
- `GET /console/health` - 健康检查

**测试场景**:
- 控制台页面正常渲染
- 应用统计数据准确性
- 模板路径解析正确
- 静态资源加载正常

### 4. 浏览器测试 (Browser Tests)

#### 4.1 控制台界面测试
**测试文件**: `tests/test_console_ui_apps_relocation.py`
**测试工具**: Chrome DevTools MCP
**覆盖功能**:
- 应用列表显示
- 工作流控制台界面
- 实时状态更新

**测试场景**:
- 页面加载和渲染正确
- 应用卡片信息显示
- 工作流执行界面功能
- WebSocket 连接和消息传递
- 响应式布局适配

### 5. 跨平台兼容性测试

#### 5.1 路径处理测试
**测试文件**: `tests/test_cross_platform_paths.py`
**覆盖平台**: Windows, macOS, Linux
**测试场景**:
- 路径分隔符处理
- 文件系统权限
- 环境变量展开
- 相对路径解析
- Unicode 路径支持

#### 5.2 环境配置测试
**测试文件**: `tests/test_environment_config_relocation.py`
**测试场景**:
- 不同操作系统的默认路径
- 环境变量优先级
- 配置文件加载顺序
- 路径规范化处理

### 6. 向后兼容性测试

#### 6.1 迁移兼容性测试
**测试文件**: `tests/test_migration_compatibility.py`
**测试场景**:
- 旧路径检测和警告
- 配置格式兼容性
- 渐进式迁移支持
- 回滚机制验证

#### 6.2 配置格式测试
**测试文件**: `tests/test_app_config_format_compatibility.py`
**测试场景**:
- 新旧 `app.json` 格式支持
- `entry_point` 路径格式转换
- 配置验证和错误处理
- 默认值填充机制

## 测试数据和资源

### 测试应用结构
```
tests/resources/apps_relocation/
├── test_apps/                    # 测试用应用目录
│   ├── sample_app/              # 示例应用
│   │   ├── app.json            # 新格式配置
│   │   └── flow1/
│   │       └── imp/
│   │           ├── workflow_definition.py
│   │           └── nodes.py
│   └── legacy_app/             # 兼容性测试应用
│       ├── app.json            # 旧格式配置
│       └── flow1/
├── configs/                     # 测试配置文件
│   ├── test_config_new.yaml
│   ├── test_config_legacy.yaml
│   └── env_configs/
└── expected_outputs/            # 预期输出数据
    ├── app_lists/
    ├── workflow_metadata/
    └── api_responses/
```

### 环境变量测试矩阵
```python
TEST_ENV_MATRIX = [
    {"WORKFLOW_APPS_DIR": "apps"},                    # 新默认路径
    {"WORKFLOW_APPS_DIR": "src_new/apps"},           # 旧路径兼容
    {"WORKFLOW_APPS_DIR": "/absolute/path/to/apps"}, # 绝对路径
    {"WORKFLOW_APPS_DIR": "./relative/apps"},        # 相对路径
    {},                                              # 无环境变量（使用默认值）
]
```

## 测试执行策略

### 测试阶段划分

#### 阶段1: 核心组件单元测试
- 配置管理器测试
- 应用管理器测试
- 函数注册机制测试
- **通过标准**: 所有单元测试通过，代码覆盖率 ≥ 90%

#### 阶段2: 集成测试
- 工作流引擎集成测试
- 服务器启动测试
- **通过标准**: 端到端流程正常，无集成错误

#### 阶段3: API和界面测试
- API端点测试
- 浏览器界面测试
- **通过标准**: 所有API响应正确，界面功能完整

#### 阶段4: 兼容性和性能测试
- 跨平台兼容性测试
- 向后兼容性测试
- 性能基准测试
- **通过标准**: 所有平台正常运行，性能无回退

### 自动化测试流程

#### CI/CD 集成
```bash
# 测试命令序列
pytest tests/test_*_relocation.py -v --cov=src_new/workflow_engine
pytest tests/test_cross_platform_paths.py --platform-matrix
pytest tests/test_migration_compatibility.py --legacy-support
```

#### 测试环境配置
```yaml
test_environments:
  - name: "new_structure"
    apps_dir: "apps"
    config_format: "new"
  
  - name: "legacy_compatibility"
    apps_dir: "src_new/apps"
    config_format: "legacy"
  
  - name: "custom_path"
    apps_dir: "/tmp/test_apps"
    config_format: "new"
```

## 性能基准测试

### 关键性能指标
- **应用加载时间**: ≤ 100ms (单个应用)
- **工作流启动时间**: ≤ 200ms
- **API响应时间**: ≤ 50ms (95th percentile)
- **内存使用**: 无显著增长
- **并发处理**: 支持 ≥ 10 个并发工作流

### 性能测试场景
```python
PERFORMANCE_TEST_SCENARIOS = [
    {
        "name": "single_app_load",
        "apps_count": 1,
        "flows_per_app": 5,
        "expected_time_ms": 100
    },
    {
        "name": "multiple_apps_load",
        "apps_count": 10,
        "flows_per_app": 3,
        "expected_time_ms": 500
    },
    {
        "name": "concurrent_workflows",
        "concurrent_count": 10,
        "workflow_duration_s": 30,
        "expected_success_rate": 0.95
    }
]
```

## 测试通过标准

### 必须满足的条件
1. **功能完整性**: 所有现有功能在新路径下正常工作
2. **向后兼容性**: 支持旧配置格式和路径结构
3. **性能稳定性**: 性能指标无显著回退
4. **跨平台兼容**: Windows/macOS/Linux 全平台支持
5. **错误处理**: 异常情况下的优雅降级
6. **代码覆盖率**: 核心变更代码覆盖率 ≥ 90%

### 验收测试检查清单
- [ ] 所有单元测试通过 (100%)
- [ ] 集成测试通过 (100%)
- [ ] API测试通过 (100%)
- [ ] 浏览器测试通过 (100%)
- [ ] 跨平台测试通过 (Windows/macOS/Linux)
- [ ] 向后兼容性测试通过
- [ ] 性能基准测试通过
- [ ] 代码覆盖率达标 (≥90%)
- [ ] 无内存泄漏或资源泄露
- [ ] 文档和示例更新完成

## 风险缓解措施

### 高风险场景处理
1. **模块导入失败**: 提供详细错误日志和降级机制
2. **路径解析错误**: 多重路径检测和自动修复
3. **配置格式不兼容**: 自动格式转换和验证
4. **性能回退**: 性能监控和优化建议
5. **跨平台问题**: 平台特定的测试和修复

### 回滚计划
- 保留旧路径检测逻辑
- 提供配置回滚工具
- 维护兼容性层至少一个版本周期
- 详细的迁移指南和故障排除文档