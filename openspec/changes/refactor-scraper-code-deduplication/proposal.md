# Proposal: 重构抓取器代码去重

## 概述

**变更ID**: `refactor-scraper-code-deduplication`  
**类型**: 重构 (Refactoring)  
**优先级**: 中  
**影响范围**: `ozon-scraper`, `seerfar-scraper`

## 问题陈述

当前 `OzonScraper` 和 `SeerfarScraper` 存在以下代码质量问题：

### 1. SeerfarScraper 的冗余问题
- **重复的去重逻辑**：商品行去重代码在 `extract_products_async` 方法中出现两次（第394-407行和第416-428行）
- **废弃的注释代码**：第624-653行存在大量被注释掉但未删除的代码
- **重复的空值检查**：`page` 对象的空值检查在多个方法中重复出现
- **重复的日志输出**：相同的日志信息在不同位置重复记录

### 2. OzonScraper 的维护性问题
- **方法职责不清**：价格提取逻辑分散在多个方法中，难以追踪
- **缺少辅助方法**：常用的验证和转换逻辑未提取为独立方法
- **注释代码残留**：存在被注释但未删除的实验性代码

### 3. 跨抓取器的共性问题
- **缺少共享工具类**：页面验证、元素去重等通用逻辑未抽象
- **错误处理不一致**：不同抓取器的错误处理方式不统一
- **日志格式不统一**：日志级别和格式在不同模块中不一致

## 目标

1. **消除代码重复**：提取重复逻辑为独立方法，提高代码复用性
2. **清理废弃代码**：删除所有注释掉的废弃代码，保持代码库整洁
3. **提高可维护性**：通过方法提取和职责分离，使代码更易理解和修改
4. **统一编码规范**：建立一致的错误处理和日志记录模式

## 非目标

- 不改变抓取器的外部接口和行为
- 不引入新的功能特性
- 不修改业务逻辑和数据处理流程
- 不涉及性能优化（除非是重构的自然结果）

## 解决方案

### 阶段1：SeerfarScraper 重构

#### 1.1 提取去重逻辑
```python
async def _deduplicate_rows(self, rows: list) -> list:
    """去重商品行，避免 CSS 和 XPath 选择器匹配到相同元素"""
    seen_indices = set()
    unique_rows = []
    for row in rows:
        try:
            data_index = await row.get_attribute('data-index')
            if data_index and data_index not in seen_indices:
                seen_indices.add(data_index)
                unique_rows.append(row)
        except Exception:
            unique_rows.append(row)
    return unique_rows
```

#### 1.2 提取页面验证逻辑
```python
def _validate_page(self, page) -> bool:
    """验证 page 对象是否有效"""
    if page is None:
        self.logger.error("❌ page 对象为 None，浏览器可能未正确启动")
        return False
    return True
```

#### 1.3 删除废弃代码
- 删除第624-653行的注释代码块
- 删除重复的 OzonScraper 调用逻辑

### 阶段2：OzonScraper 重构

#### 2.1 提取价格验证逻辑
```python
def _validate_price(self, price: Optional[float], price_type: str) -> bool:
    """验证价格是否有效"""
    if price is None or price <= 0:
        self.logger.debug(f"⚠️ {price_type}价格无效: {price}")
        return False
    return True
```

#### 2.2 统一错误处理模式
```python
def _handle_extraction_error(self, error: Exception, context: str) -> None:
    """统一处理提取错误"""
    self.logger.error(f"❌ {context}失败: {error}")
    # 可选：记录到错误追踪系统
```

### 阶段3：创建共享工具类（可选）

如果发现多个抓取器有共同需求，可以创建：
```python
# common/scrapers/scraper_utils.py
class ScraperUtils:
    """抓取器通用工具类"""
    
    @staticmethod
    async def deduplicate_elements(elements: list, attr: str = 'data-index') -> list:
        """通用元素去重逻辑"""
        pass
    
    @staticmethod
    def validate_page(page, logger) -> bool:
        """通用页面验证逻辑"""
        pass
```

## 实施计划

### 里程碑1：SeerfarScraper 重构（1-2天）
- [ ] 提取 `_deduplicate_rows` 方法
- [ ] 提取 `_validate_page` 方法
- [ ] 删除所有废弃注释代码
- [ ] 更新所有调用点使用新方法
- [ ] 运行现有测试确保无回归

### 里程碑2：OzonScraper 重构（1-2天）
- [ ] 提取 `_validate_price` 方法
- [ ] 提取 `_handle_extraction_error` 方法
- [ ] 统一日志格式和级别
- [ ] 清理注释代码
- [ ] 运行现有测试确保无回归

### 里程碑3：文档和验证（0.5天）
- [ ] 更新代码注释和文档字符串
- [ ] 添加方法级别的单元测试（如需要）
- [ ] 代码审查和质量检查

## 风险和缓解

### 风险1：重构引入新bug
**缓解措施**：
- 每次重构后立即运行完整测试套件
- 使用小步提交，便于回滚
- 重点测试边界条件和异常情况

### 风险2：影响现有功能
**缓解措施**：
- 保持外部接口不变
- 使用类型注解确保参数正确性
- 添加集成测试验证端到端流程

### 风险3：代码审查延迟
**缓解措施**：
- 提供清晰的变更说明和对比
- 分阶段提交，每个阶段独立可审查
- 提前与团队沟通重构计划

## 成功标准

1. **代码质量**：
   - 消除所有重复代码（通过代码审查确认）
   - 删除所有注释废弃代码
   - 方法复杂度降低（圈复杂度 < 10）

2. **测试覆盖**：
   - 所有现有测试通过
   - 新提取的方法有单元测试覆盖（如适用）

3. **可维护性**：
   - 代码行数减少 10-15%
   - 方法平均长度减少
   - 代码可读性提升（通过团队反馈）

4. **性能**：
   - 重构不引入性能退化
   - 关键路径执行时间保持不变（±5%）

## 替代方案

### 方案A：完全重写抓取器
**优点**：可以从零开始设计更好的架构  
**缺点**：风险高、工作量大、可能引入新问题  
**结论**：不推荐，当前代码整体架构合理

### 方案B：仅删除注释代码
**优点**：风险最小、工作量最小  
**缺点**：不解决重复代码问题，可维护性提升有限  
**结论**：不充分，无法达到重构目标

### 方案C：引入代码生成工具
**优点**：可以自动化部分重构工作  
**缺点**：需要学习新工具、可能过度工程化  
**结论**：当前规模不需要，手动重构更合适

## 依赖和前置条件

- 现有测试套件完整且可运行
- 代码库使用版本控制（Git）
- 团队成员熟悉 Python 异步编程
- 有代码审查流程

## 后续工作

重构完成后，可以考虑：
1. 建立代码质量检查工具（如 pylint, flake8）
2. 添加代码复杂度监控
3. 制定抓取器开发规范文档
4. 定期进行代码质量审查

## 参考资料

- [Python 重构最佳实践](https://refactoring.guru/refactoring/python)
- [Clean Code 原则](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)
- 项目现有代码规范：`openspec/project.md`
