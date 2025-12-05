# Change: 重构 RPA 浏览器自动化包

## Why

经过全面审查 `rpa/` 包的设计和代码质量，发现以下问题需要解决：

### 0. 代码质量问题（统计）
- **代码量**: 4 个核心文件共 4710 行，过于臃肿
- **print 语句**: 78 处 `print()` 调用（主要在 universal_paginator.py）
- **裸 except**: 多处 `except:` 或 `except Exception:` 未区分异常类型
- **函数过长**: 多个函数超过 50 行（如 `_go_to_next_page_numeric` 56 行）
- **重复代码**: 选择器查找逻辑在分页器中重复多次

### 1. 架构冲突和冗余
- **配置类重复**: `BrowserConfig`、`BrowserServiceConfig`、`PaginatorConfig`、`DOMAnalyzerConfig` 存在职责重叠
- **异常类过多**: 存在 20+ 个异常类，很多功能重复（如 `TimeoutError` vs `BrowserTimeoutError`，`ResourceError` vs `ResourceManagementError`）
- **向后兼容别名泛滥**: `DOMPageAnalyzer = SimplifiedDOMPageAnalyzer`、`ScenarioExecutionError = RunnerExecutionError` 等，增加维护成本

### 2. 设计不合理
- **过度抽象**: 接口层次过深（4层：IBrowserDriver → IPageAnalyzer → IContentExtractor/IElementMatcher/IPageValidator）
- **单例模式隐患**: `SimplifiedBrowserService` 使用类变量实现单例，但缺乏线程安全保护
- **print语句调试**: 生产代码中存在大量 `print()` 调试语句，应使用统一的日志系统
- **硬编码选择器**: 分页器中硬编码了大量 CSS 选择器，不易扩展

### 3. 性能隐患
- **同步/异步混用**: `IBrowserDriver` 接口同时定义同步和异步方法，但实现层缺乏清晰的边界
- **DOM分析器重复评估**: 每次提取元素都执行完整的 JavaScript 评估，缺乏缓存
- **浏览器检测器阻塞调用**: `BrowserDetector` 使用 `subprocess.run()` 同步阻塞，可能影响性能

### 4. 未使用的代码
- `PerformanceConfig`、`SecurityConfig` 数据类已定义但从未使用
- 多个接口方法（如 `check_accessibility`）实现但无调用者

## What Changes

### 新增能力
- **统一配置系统**: 以 `common.BrowserConfig` 为唯一配置源，RPA 层通过适配器转换
- **精简异常层次**: 减少异常类数量，采用异常码机制
- **日志标准化**: 移除所有 print 语句，统一使用 StructuredLogger
- **浏览器检测增强**: 扩展支持 Chrome 浏览器，新增插件检测功能

### 技术实现
1. 配置层重构：创建 `config_adapter.py` 适配器，从 `common.BrowserConfig` 转换为 RPA 内部配置
2. 异常层精简：保留 5 个核心异常 + 错误码
3. 接口层简化：移除冗余接口，采用组合而非继承
4. 清理向后兼容别名，提供迁移指南
5. 添加性能监控和资源使用追踪

## Impact

### 受影响的系统组件
- **rpa/browser/**: 核心重构区域
- **common/scrapers/**: 需要适配新的浏览器服务接口
- **tests/**: 需要更新测试以适应新结构

### 用户体验改进
- **开发者**: 更清晰的 API，减少学习成本
- **运维**: 更好的日志和错误追踪

### 技术债务
- 移除 6 个冗余配置类
- 合并 15+ 个重复异常类
- 删除约 500 行无用代码
- 建立清晰的同步/异步边界
