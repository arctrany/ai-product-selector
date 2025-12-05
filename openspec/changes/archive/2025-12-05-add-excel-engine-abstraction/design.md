# Excel Engine Abstraction Design

## Context
The profit calculation system needs to accurately replicate Excel's complex shipping cost calculations, which include:
- Multi-dimensional lookup tables (weight, dimensions, price ranges)
- Dynamic formula dependencies across multiple sheets
- Conditional logic for shipping channel selection

Current Python implementation only covers ~70% of Excel functionality, missing critical shipping cost calculations that affect profit accuracy.

Additionally, the current CLI exposes calculator file paths as parameters, creating a security vulnerability where sensitive file locations could be exposed to clients.

## Goals / Non-Goals
- Goals:
  - 100% accurate profit calculations matching Excel
  - Support for complex shipping lookup tables (1000+ rows)
  - Ability to switch between calculation engines
  - Cross-platform compatibility (with graceful degradation)
  - Performance optimization through engine selection
  - Pre-compiled Python engine for production use
  - Secure calculator file access without CLI exposure

- Non-Goals:
  - Real-time Excel synchronization
  - Supporting all Excel functions (only those needed for profit calculation)
  - Building a general-purpose Excel engine
  - Runtime Excel parsing in production

## Decisions

### Decision: Abstract Engine Interface
Create `CalculationEngine` protocol that all implementations must follow:
```python
class CalculationEngine(Protocol):
    def calculate_profit(self, inputs: ProfitCalculatorInput) -> ProfitCalculatorResult
    def calculate_shipping(self, weight: float, dimensions: Tuple[float, float, float], price: float) -> float
    def validate_connection(self) -> bool
```

**Alternatives considered:**
- Direct xlwings integration: Less flexible, platform-dependent
- Only formulas library: May not support all Excel functions
- Manual formula parsing: Too complex and error-prone

### Decision: Engine Implementations
1. **XlwingsEngine**: Uses actual Excel for 100% accuracy (Windows/macOS only, requires Excel installation)
2. **PythonEngine**: Pre-compiled implementation for performance and Linux compatibility
3. **FormulasEngine**: Future option for cross-platform Excel compatibility

**Rationale**: Allows optimal engine selection based on environment and requirements

**Platform Support**:
- xlwings: Windows ✅, macOS ✅, Linux ❌
- Python engine: Windows ✅, macOS ✅, Linux ✅
- formulas engine: Windows ✅, macOS ✅, Linux ✅

### Decision: Python Engine Pre-compilation Approach
The Python engine will use a pre-compilation approach to achieve 100% accuracy while maintaining high performance:

```python
# Development time: Extract and compile Excel logic
python -m common.excel_engine.compiler \
    --input profits_calculator.xlsx \
    --output compiled_rules.py

# Generated file structure
compiled_rules.py:
    - ShippingRules: Complete shipping rate table (1000+ entries)
    - CalculationFormulas: All Excel formulas converted to Python
    - DependencyGraph: Formula dependencies for correct calculation order
```

**Pre-compilation Process**:
1. **Extract Phase**: Read all Excel sheets, formulas, and lookup tables
2. **Analyze Phase**: Build dependency graph of formula references
3. **Generate Phase**: Create Python code that replicates Excel logic exactly
4. **Validate Phase**: Compare outputs with Excel to ensure 100% accuracy

**Advantages**:
- No runtime Excel parsing overhead
- Version control for compiled rules
- Easy to audit and debug
- Platform independent execution
- CI/CD can validate against Excel source

**Workflow**:
- Developers run compiler when Excel file changes
- Compiled rules are committed to repository
- Runtime uses pre-compiled rules for calculations
- Validation tests ensure Excel/Python parity

### Decision: Configuration-based Engine Selection
```python
engine_config = {
    "default": "auto",  # auto|xlwings|python|formulas
    "fallback_order": ["xlwings", "formulas", "python"],
    "cache_enabled": True,
    "validation_mode": False  # Compare results across engines
}
```

## Architecture

```
common/
├── excel_engine/
│   ├── __init__.py
│   ├── base.py          # Abstract interfaces
│   ├── xlwings_engine.py
│   ├── python_engine.py
│   ├── engine_factory.py
│   └── models.py        # Shared data models
├── config/
│   ├── engine_config.py # Engine configuration
│   └── paths.py         # Secure path configuration
├── business/
│   └── excel_calculator.py  # Refactored to use engines
```

### Security Architecture
```python
# config/paths.py
class SecurePathConfig:
    """Secure path configuration with validation"""
    
    ALLOWED_DIRS = ['/app/data/calculators/']
    
    @staticmethod
    def get_calculator_path(identifier: str) -> Path:
        """Get calculator path by secure identifier"""
        # Map identifiers to actual paths
        # Validate against allowed directories
        # Prevent path traversal attacks
```

## Risks / Trade-offs
- **Risk**: xlwings requires Excel installation → Mitigation: Automatic fallback to Python engine
- **Risk**: Performance degradation with xlwings → Mitigation: Caching layer and batch operations
- **Risk**: Engine results divergence → Mitigation: Validation mode to compare results
- **Risk**: File path exposure security vulnerability → Mitigation: System configuration with access control
- **Trade-off**: Complexity vs accuracy → Accept complexity for business-critical calculations
- **Trade-off**: CLI convenience vs security → Prioritize security by removing direct file path access

### Discovered Implementation Issues (2025-12-05 Review)

#### 🔴 BLOCKING: XlwingsEngine 单元格映射完全错误

**当前代码** (`xlwings_engine.py:121-128`):
```python
# ❌ 错误的映射
self.calc_sheet.range('H2').value = inputs.weight
self.calc_sheet.range('H3').value = inputs.commission_rate
```

**实际 Excel 结构** (通过 openpyxl 分析确认):
```
利润计算表 Sheet:
├── A4: 重量(g) ← weight
├── A5: 长(cm) ← length
├── A6: 宽(cm) ← width
├── A7: 高(cm) ← height
├── A11: 定价 ← list_price ✅ 正确
├── B11: 采购成本 ← purchase_price ✅ 正确
├── C11: =SUM(UNI运费!K8,K15,K22,K29,K36,K43) ← 运费(自动计算)
├── D11: 3 ← 贴单费
├── E11: =A11*C9 ← 平台佣金
├── F11: =A11*0.04 ← 杂费
└── G11: =A11-B11-C11-D11-E11-F11 ← 利润

UNI运费 Sheet (M列 - 运费计算输入):
├── M3: 重量(g)
├── M4: 长(cm)
├── M5: 宽(cm)
├── M6: 高(cm)
├── M7: 销售价格(卢布)
└── M8: 送货方式 ("自提点" 或 "送货上门") ← 关键参数缺失！
```

**正确的映射应该是**:
```python
# 利润计算表
self.calc_sheet.range('A4').value = inputs.weight
self.calc_sheet.range('A5').value = inputs.length
self.calc_sheet.range('A6').value = inputs.width
self.calc_sheet.range('A7').value = inputs.height
self.calc_sheet.range('A11').value = inputs.list_price
self.calc_sheet.range('B11').value = inputs.purchase_price

# UNI运费 Sheet
uni_sheet = self.workbook.sheets["UNI运费"]
uni_sheet.range('M3').value = inputs.weight
uni_sheet.range('M4').value = inputs.length
uni_sheet.range('M5').value = inputs.width
uni_sheet.range('M6').value = inputs.height
uni_sheet.range('M7').value = inputs.list_price  # 卢布价格
uni_sheet.range('M8').value = inputs.delivery_type  # "自提点" 或 "送货上门"
```

#### 🔴 BLOCKING: 运费计算逻辑严重不完整

**当前 compiled_rules.py**:
```python
# 只有 10 个固定费率档位
self.shipping_rates = [
    (0, 50, 5.0, 6.0),
    (50, 100, 6.0, 7.0),
    # ... 共 10 条
]
```

**实际 Excel 运费逻辑** (UNI运费 Sheet K列):
```
6 个物流渠道:
├── K8:  UNI Extra Small (1g-500g)
├── K15: UNI Budget (501g-25kg, 低客单)
├── K22: UNI Small (1g-2kg)
├── K29: UNI Big (2.001kg-25kg)
├── K36: UNI Premium Small (1g-5kg, 高客单)
└── K43: UNI Premium Big (5.001kg-25kg, 高客单)

每个渠道的公式:
=IF(AND(
    MAX($M$4:$M$6)<=V8,      # 最大尺寸限制
    SUM($M$4:$M$6)<=U8,      # 三边之和限制
    $M$7<=W8, $M$7>=X8,      # 价格范围 (卢布)
    $M$3>=S8, $M$3<=T8       # 重量范围 (g)
  ),
  IF($M$8="自提点",
     Y8 + $M$3*Z8,           # 自提点: 首重+续重
     AA8 + $M$3*AB8          # 送货上门: 首重+续重
  ),
  ""  # 不符合条件返回空
)

最终运费 = SUM(K8, K15, K22, K29, K36, K43)
```

**缺失的逻辑**:
- [ ] 6 个渠道的条件参数 (S-AB 列)
- [ ] 尺寸条件判断 (MAX, SUM)
- [ ] 价格范围条件 (卢布)
- [ ] 送货方式区分
- [ ] 渠道选择和汇总

#### 🔴 BLOCKING: 安全配置 Fallback 绕过

**位置**: `engine_factory.py:115-117`
```python
if config:
    calculator_path = config.get_calculator_path()
else:
    calculator_path = Path("docs/profits_calculator.xlsx")  # ❌ 绕过安全！
```

**安全测试失败**: `test_security_path_config.py` 7/8 测试失败

#### HIGH: ExcelCompiler Output Non-functional
- Generated code contains syntax errors
- No execution framework for Excel functions
- Formula conversion incomplete

#### MEDIUM: Configuration Issues
- `EngineConfig.from_file()` method missing
- YAML configuration disconnected from implementation
- Three separate config sources not integrated

## Migration Plan
1. Create engine abstraction without changing external API
2. Move existing logic to PythonEngine
3. Implement XlwingsEngine with full Excel support
4. Add configuration to select engines
5. Gradual rollout with validation mode enabled
6. Monitor performance and accuracy metrics

**Rollback**: Configuration flag to force Python engine

## Open Questions
- Should we support parallel engine execution for validation?
- How to handle Excel file updates in production?
- Optimal caching strategy for xlwings engine?