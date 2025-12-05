# 设计文档: GitHub Actions CI/CD跨平台构建系统

## Context

项目需要实现自动化的跨平台构建和发布流程，当前存在以下背景：
- 已有完整的本地构建脚本 (`packaging/` 目录)
- 已有PyInstaller配置 (`build.spec`, `build_optimized.spec`)
- 现有基础的GitHub Actions测试流程 (`python-package.yml`)
- 需要支持Windows、macOS、Linux三大平台的可执行文件分发

**约束条件**:
- 必须保持与现有本地构建脚本的兼容性
- 需要支持Playwright浏览器依赖的自动安装
- 构建产物必须包含完整的配置文件和使用说明
- 必须提供文件完整性校验机制

## Goals / Non-Goals

### Goals
- 实现完全自动化的跨平台构建流程
- 支持基于Git标签的自动Release发布
- 提供4个平台目标的并行构建 (Windows x64, macOS Intel, macOS ARM64, Linux x64)
- 生成标准化的构建产物和Release Notes
- 集成代码质量检查和构建验证
- 提供完整的使用文档和故障排除指南

### Non-Goals
- 不替换现有的本地构建脚本 (保持作为备选方案)
- 不改变现有的项目结构和依赖管理
- 不实现复杂的部署策略 (仅限于GitHub Release)
- 不支持自定义构建环境或容器化构建

## Decisions

### Decision 1: 使用GitHub Actions矩阵构建策略
**选择**: 使用 `strategy.matrix` 实现4个平台目标的并行构建 (Windows x64, macOS Intel, macOS ARM64, Linux x64)
**原因**: 
- 提供最佳的构建性能 (并行执行)
- GitHub Actions原生支持，稳定可靠
- 易于维护和扩展新平台
- 资源使用合理，符合GitHub Actions限制

**替代方案考虑**:
- 串行构建 → 拒绝，构建时间过长
- 自托管Runner → 拒绝，增加维护成本
- 第三方CI服务 → 拒绝，增加复杂性

### Decision 2: 保持双工作流设计
**选择**: 分离测试工作流 (`test.yml`) 和发布工作流 (`release.yml`)
**原因**:
- 职责分离，测试和发布有不同的触发条件
- 测试工作流支持PR和分支推送，发布工作流仅支持标签
- 便于独立维护和优化
- 符合CI/CD最佳实践

### Decision 3: 基于标签的自动发布策略
**选择**: 使用 `v*` 标签模式触发自动发布
**原因**:
- 符合语义化版本管理规范
- 避免意外触发发布流程
- 提供明确的发布控制点
- 支持预发布版本 (beta, alpha, rc)

**发布流程**:
```bash
git tag v1.0.0
git push origin v1.0.0  # 触发自动构建和发布
```

### Decision 4: 构建产物标准化
**选择**: 统一的命名和打包格式，支持4个平台目标
- Windows x64: `ai-product-selector-win-x64.zip`
- macOS Intel: `ai-product-selector-macos-x64.tar.gz`
- macOS ARM64: `ai-product-selector-macos-arm64.tar.gz`
- Linux x64: `ai-product-selector-linux-x64.tar.gz`

**包含内容**:
- 可执行文件
- 配置文件 (`config.json`, `example_config.json`)
- 使用说明 (`README.txt`)
- SHA256校验和文件

**GitHub Release**: 推送 `v*` 标签后自动创建 Release，上传所有平台的构建产物

### Decision 5: 版本信息动态生成
**选择**: 在CI环境中动态生成 `version.py` 文件
**原因**:
- 避免版本信息的硬编码和手动维护
- 确保构建信息的准确性 (构建号、时间戳)
- 支持多种版本信息查询方式
- 与现有代码结构兼容

## Risks / Trade-offs

### Risk 1: GitHub Actions配额限制
**风险**: 频繁构建可能超出GitHub Actions免费配额
**缓解措施**:
- 仅在标签推送时触发发布构建
- 优化构建时间，减少资源消耗
- 监控配额使用情况

### Risk 2: 跨平台构建环境差异
**风险**: 不同平台的构建环境可能导致构建结果不一致
**缓解措施**:
- 使用固定版本的GitHub Actions运行器
- 统一Python版本和依赖版本
- 添加构建验证步骤

### Risk 3: Playwright浏览器依赖安装失败
**风险**: 某些平台的浏览器依赖安装可能失败
**缓解措施**:
- 使用 `|| true` 允许部分失败
- 提供手动安装指导
- 在构建验证中测试浏览器功能

### Trade-off: 构建时间 vs 并行度
- **选择**: 4个平台目标并行构建 (Windows, macOS Intel, macOS ARM64, Linux)
- **权衡**: 增加资源使用但显著减少总构建时间
- **结果**: 总构建时间约15-20分钟，可接受

## Migration Plan

### Phase 1: 基础设施搭建 (已完成)
1. 创建GitHub Actions工作流文件
2. 配置构建矩阵和环境设置
3. 实现基础的构建和打包逻辑

### Phase 2: 测试和验证
1. 创建测试标签验证完整流程
2. 测试各平台构建产物的功能
3. 验证Release创建和资产上传

### Phase 3: 文档和推广
1. 完善使用文档和故障排除指南
2. 更新项目README和发布说明
3. 向团队介绍新的发布流程

### Rollback Plan
- 如果CI/CD流程出现问题，可立即回退到本地构建脚本
- 现有的 `build_scripts/` 目录脚本保持完整功能
- 提供详细的本地构建指导文档

## Open Questions

1. **构建缓存策略**: 是否需要实现更复杂的依赖缓存机制？
   - 当前使用GitHub Actions内置的pip缓存
   - 可考虑添加Playwright浏览器缓存

2. **多架构支持**: 是否需要支持更多架构 (如ARM Linux)？
   - 当前专注于主流平台
   - 可根据用户需求后续扩展

3. **构建通知**: 是否需要构建状态的外部通知机制？
   - GitHub自带通知已足够
   - 可考虑集成Slack或邮件通知

4. **安全扫描**: 是否需要集成安全漏洞扫描？
   - 当前依赖GitHub的安全建议
   - 可考虑添加依赖漏洞扫描步骤