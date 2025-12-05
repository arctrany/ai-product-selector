# Change: 基于GitHub的CI/CD跨平台构建系统

## Why

项目需要实现自动化的跨平台构建和发布流程，以支持Windows、macOS、Linux三大平台的可执行文件分发。当前虽然已有本地构建脚本，但缺乏统一的CI/CD自动化流程和规范化的构建管理。

通过GitHub Actions实现自动化构建可以：
1. 确保构建环境的一致性和可重复性
2. 支持多平台并行构建，提高构建效率
3. 自动化Release创建和资产分发
4. 提供构建产物的校验和验证机制

## What Changes

### 新增能力
- **GitHub Actions工作流**: 跨平台构建和Release发布自动化
- **构建矩阵配置**: 支持4个平台目标 (Windows x64, macOS Intel, macOS ARM64, Linux x64)
- **自动Release管理**: 基于Git标签自动创建GitHub Release
- **构建产物管理**: 自动生成压缩包、校验和文件和Release Notes
- **测试集成**: 构建前的代码质量检查和构建验证

### 技术实现
- 创建 `.github/workflows/release.yml` 实现跨平台构建工作流
- 创建 `.github/workflows/test.yml` 实现代码测试和构建验证
- 优化 `build.spec` 配置以适配CI环境
- 提供完整的使用文档和故障排除指南

## Impact

### 受影响的系统组件
- **新增规范**: `github-actions-cicd` (GitHub Actions CI/CD构建系统)
- **现有构建脚本**: 保持兼容，作为本地构建的备选方案
- **项目发布流程**: 从手动构建转向自动化Release流程

### 用户体验改进
- **开发者**: 推送标签即可触发自动构建和发布
- **最终用户**: 可从GitHub Releases直接下载各平台的可执行文件
- **维护者**: 统一的构建环境减少"在我机器上能运行"的问题

### 技术债务
- 现有的本地构建脚本 (`packaging/build-*.sh`, `packaging/build.py`) 将保持兼容
- 逐步迁移到以GitHub Actions为主的构建流程
- 提供清晰的迁移路径和文档指导