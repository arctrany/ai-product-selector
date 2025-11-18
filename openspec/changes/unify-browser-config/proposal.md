# 统一浏览器配置管理

## Why - 为什么需要这个变更？

### 问题背景
当前系统存在两个独立的浏览器配置类：
1. **ScrapingConfig** (`common/config.py`) - 用于抓取器的浏览器配置
2. **BrowserConfig** (`rpa/browser/core/models/browser_config.py`) - 用于 RPA 模块的浏览器配置

### 存在的问题
1. **配置冗余**：两个类包含相同的浏览器配置字段（browser_type, headless, timeout 等）
2. **维护困难**：修改浏览器配置需要同时更新两个地方
3. **概念混淆**：开发者不清楚应该使用哪个配置类
4. **代码重复**：配置加载和验证逻辑重复实现
5. **扩展性差**：新增浏览器配置需要在多处修改

### 影响范围
- 所有使用 `config.scraping` 的抓取器代码
- 所有使用 `BrowserConfig` 的 RPA 代码
- 配置文件的结构和加载逻辑
- 相关的测试代码

## What Changes - 需要做什么变更？

### 简化方案（选项 C）
采用渐进式重构，降低风险：

1. **保留 ScrapingConfig 作为别名**
   - 在 `common/config.py` 中保留 ScrapingConfig 类
   - 将 ScrapingConfig 改为 BrowserConfig 的别名
   - 添加 @deprecated 装饰器标记为废弃

2. **统一配置读取逻辑**
   - 配置文件同时支持 `scraping` 和 `browser` 字段
   - 优先读取 `browser` 字段，向后兼容 `scraping` 字段
   - 使用 `scraping` 字段时输出警告日志

3. **文档和注释更新**
   - 更新配置文件示例，推荐使用 `browser` 字段
   - 添加迁移指南，说明如何从 `scraping` 迁移到 `browser`
   - 在代码注释中标注废弃信息

### 配置文件变更示例

**旧格式（仍然支持）：**
```json
{
  "scraping": {
    "browser_type": "edge",
    "headless": false,
    "page_load_timeout": 30
  }
}
```

**新格式（推荐）：**
```json
{
  "browser": {
    "browser_type": "edge",
    "headless": false,
    "timeout_seconds": 30,
    "required_login_domains": ["seerfar.cn", "www.maozierp.com"],
    "debug_port": 9222
  }
}
```

## Breaking Changes - 破坏性变更

### 无破坏性变更
本次采用简化方案，**不引入破坏性变更**：

1. ✅ **向后兼容**：保留 ScrapingConfig 类作为别名
2. ✅ **配置兼容**：同时支持 `scraping` 和 `browser` 字段
3. ✅ **代码兼容**：现有代码无需修改即可运行
4. ✅ **渐进迁移**：可以逐步迁移到新的配置方式

### 废弃警告
使用 `scraping` 配置时会输出警告日志：
```
⚠️ 警告：'scraping' 配置字段已废弃，请迁移到 'browser' 字段
```

## Implementation Plan - 实施计划

### 阶段 1：配置类重构（本次变更）
1. 在 `common/config.py` 中创建 BrowserConfig 类
2. 将 ScrapingConfig 改为 BrowserConfig 的别名
3. 添加 @deprecated 装饰器和警告日志
4. 更新配置加载逻辑，支持双字段读取

### 阶段 2：文档更新（本次变更）
1. 更新配置文件示例
2. 添加迁移指南
3. 更新代码注释

### 阶段 3：测试验证（本次变更）
1. 编写单元测试验证配置兼容性
2. 编写集成测试验证实际运行
3. 验证警告日志正确输出

### 阶段 4：逐步迁移（后续版本）
1. 逐步将代码中的 `config.scraping` 改为 `config.browser`
2. 更新所有配置文件使用新格式
3. 在未来版本中完全移除 ScrapingConfig 别名

## Success Criteria - 成功标准

1. ✅ 所有现有代码无需修改即可正常运行
2. ✅ 新旧配置格式都能正确加载
3. ✅ 使用旧配置时输出警告日志
4. ✅ 所有测试通过
5. ✅ 文档和示例已更新

## Risks and Mitigations - 风险和缓解措施

### 风险 1：配置加载逻辑复杂化
**缓解措施**：
- 使用清晰的字段优先级逻辑
- 添加详细的日志输出
- 编写充分的单元测试

### 风险 2：开发者混淆新旧配置
**缓解措施**：
- 提供清晰的迁移指南
- 在警告日志中提供具体的迁移建议
- 在代码注释中标注废弃信息

### 风险 3：第三方依赖使用旧配置
**缓解措施**：
- 长期保持向后兼容性
- 不强制要求立即迁移
- 提供足够的过渡期

## Timeline - 时间线

- **Week 1**: 完成配置类重构和测试
- **Week 2**: 更新文档和示例
- **Week 3**: 代码审查和合并
- **Future**: 逐步迁移现有代码

## Related Changes - 相关变更

- [refactor-browser-connect-only](../archive/2025-11-18-refactor-browser-connect-only/proposal.md) - 浏览器仅连接模式重构（已完成）
