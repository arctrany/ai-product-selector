## 1. 架构设计和准备工作
- [ ] 1.1 设计完全同步的业务层架构
- [ ] 1.2 定义同步超时处理策略
- [ ] 1.3 规划异步方法到同步方法的映射关系
- [ ] 1.4 制定测试策略和验证方案

## 2. BaseScraper核心重构
- [ ] 2.1 移除 `run_async()` 方法及其所有调用
- [ ] 2.2 重构 `scrape_page_data()` 方法为完全同步
- [ ] 2.3 重构 `close()` 方法移除异步调用
- [ ] 2.4 更新所有同步包装方法的超时处理
- [ ] 2.5 增强错误处理和重试机制

## 3. SeerfarScraper重构（试点）
- [ ] 3.1 重构 `_extract_sales_data_async` -> `_extract_sales_data`
- [ ] 3.2 重构 `_extract_products_list_async` -> `_extract_products_list`
- [ ] 3.3 重构 `_extract_product_from_row_async` -> `_extract_product_from_row`
- [ ] 3.4 重构所有其他异步方法为同步方法
- [ ] 3.5 移除 async/await 关键字
- [ ] 3.6 优化同步调用链的超时处理

## 4. 其他Scraper类重构
- [ ] 4.1 重构 OzonScraper 异步方法
- [ ] 4.2 重构 CompetitorScraper 异步方法  
- [ ] 4.3 重构 ErpPluginScraper 异步方法
- [ ] 4.4 移除所有业务类中的 async/await

## 5. 同步超时优化
- [ ] 5.1 为不同类型操作设定合理超时时间
- [ ] 5.2 实现超时配置的动态调整机制
- [ ] 5.3 增强同步操作的错误恢复能力
- [ ] 5.4 添加操作进度监控和日志

## 6. 测试更新和验证
- [ ] 6.1 更新 BaseScraper 相关测试用例
- [ ] 6.2 更新 SeerfarScraper 测试用例
- [ ] 6.3 添加同步超时机制测试
- [ ] 6.4 验证功能完整性和性能表现
- [ ] 6.5 执行回归测试确保无功能损失
- [ ] 6.6 执行集成测试验证端到端功能

## 7. 集成测试验证
- [ ] 7.1 执行 dryrun 模式集成测试
- [ ] 7.2 验证选品流程完整性
- [ ] 7.3 确认 SeerfarScraper 销售数据抓取正常
- [ ] 7.4 验证整体系统稳定性

## 8. 清理和文档更新
- [ ] 8.1 移除所有未使用的异步相关代码
- [ ] 8.2 更新相关文档和注释
- [ ] 8.3 清理测试文件中的异步测试代码
- [ ] 8.4 验证代码 lint 检查通过

## 依赖关系
- 任务 2.x 必须在其他 scraper 重构前完成
- 任务 3.x 作为试点，验证重构方案可行性
- 任务 6.x 在每个阶段完成后都需要执行验证

## 关键里程碑
- **里程碑 1**: BaseScraper 核心重构完成
- **里程碑 2**: SeerfarScraper 试点重构成功
- **里程碑 3**: 所有业务 Scraper 重构完成
- **里程碑 4**: 单元测试验证通过
- **里程碑 5**: 集成测试验证通过

## 集成测试命令
重构完成后必须通过以下集成测试验证功能：
```bash
./xp start --dryrun --select-shops --data /Users/haowu/IdeaProjects/ai-product-selector3/tests/test_data/test_user_data.json
```

**验证要点**：
- dryrun 模式正常启动
- 商铺选择流程无异常
- SeerfarScraper 能成功抓取销售额数据
- 整个流程端到端运行完成
- 无异步相关错误或超时问题
