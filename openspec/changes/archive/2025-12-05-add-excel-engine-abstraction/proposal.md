# Change: Add Excel Engine Abstraction Layer

## Status: BLOCKED - NOT READY FOR MERGE (45% Complete)

**阻塞原因**:
1. XlwingsEngine 单元格映射完全错误
2. 安全测试 7/8 失败
3. 运费计算逻辑严重不完整

## Why
The current Excel profit calculator implementation directly embeds calculation logic in Python, missing the complex shipping cost tables and formula dependencies from the actual Excel file. We need a proper abstraction to support both xlwings-based Excel engine (100% accurate) and future pure Python implementations.

## What Changes
- Create new `excel_engine` module with abstract interface for calculation engines
- Implement xlwings-based engine for 100% Excel compatibility
- Support shipping cost lookup tables and formula dependencies
- Enable engine switching through configuration
- **BREAKING**: Move calculation logic from `common/business/excel_calculator.py` to new engine system
- **BREAKING**: Remove calculator file path from CLI parameters for security
- Add secure system configuration for calculator file locations
- Implement path validation and access control

## Impact
- Affected specs: [new capability: excel-engine]
- Affected code:
  - `common/business/excel_calculator.py` (refactored)
  - `common/business/profit_evaluator.py` (updated imports)
  - `cli/main.py` (remove file path parameters)
  - `cli/task_controller_adapter.py` (use config instead of path)
  - `good_store_selector.py` (use config instead of path)
  - New module: `common/excel_engine/`
  - New configuration: `common/config/engine_config.py`

## Implementation Status Summary

| 组件 | 完成度 | 状态 | 说明 |
|------|--------|------|------|
| 架构设计 | 80% | ✅ | Protocol 定义良好 |
| 安全配置 | 50% | ❌ | 7/8 测试失败，fallback 绕过安全 |
| XlwingsEngine | 30% | ❌ | **单元格映射完全错误** |
| PythonEngine | 60% | ⚠️ | 可运行但运费逻辑简化 |
| ExcelCompiler | 20% | ❌ | 生成代码不可用 |
| 测试覆盖 | 40% | ⚠️ | 安全测试大量失败 |

## Blocking Issues (必须修复才能合并)

### 🔴 Issue 1: XlwingsEngine 单元格映射完全错误
**位置**: `xlwings_engine.py:121-128`

当前错误映射:
```python
self.calc_sheet.range('H2').value = inputs.weight  # ❌ 应该是 A4
self.calc_sheet.range('H3').value = inputs.commission_rate  # ❌ 错误
```

实际 Excel 结构:
```
利润计算表:
  A4=重量(g), A5=长(cm), A6=宽(cm), A7=高(cm)
  A11=定价, B11=采购成本

UNI运费 Sheet (M列):
  M3=重量, M4=长, M5=宽, M6=高
  M7=销售价格(卢布), M8=送货方式(自提点/送货上门)
```

**修复时间**: 2 小时

### 🔴 Issue 2: 安全配置 Fallback 绕过
**位置**: `engine_factory.py:115-117`

```python
else:
    calculator_path = Path("docs/profits_calculator.xlsx")  # 绕过安全验证！
```

**修复时间**: 30 分钟

### 🔴 Issue 3: 运费计算逻辑严重不完整
当前只有 10 个固定费率，实际 Excel 有:
- 6 个物流渠道 (Extra Small, Budget, Small, Big, Premium Small, Premium Big)
- 复杂条件判断 (尺寸、重量、价格范围)
- 送货方式区分 (自提点 vs 送货上门)

**修复时间**: 1-2 天

## Next Steps Required
1. **BLOCKING**: 修复 XlwingsEngine 单元格映射 (2h)
2. **BLOCKING**: 移除安全 fallback (30min)
3. **HIGH**: 完善运费计算逻辑 (1-2d)
4. **MEDIUM**: 修复安全测试 (1h)
5. **LOW**: 实现 EngineConfig.from_file() (1h)