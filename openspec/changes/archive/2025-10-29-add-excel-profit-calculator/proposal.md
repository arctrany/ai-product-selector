## Why

需要实现一个基于Excel的商品利润计算器，用于自动化计算电商产品的利润率和相关财务指标。当前系统缺乏标准化的利润计算组件，导致在商品选品流程中无法准确评估产品的盈利能力。

## What Changes

- 在 `apps/xuanping/common/excel_calculator.py` 中实现完整的Excel利润计算器逻辑，支持通过Excel文件调用计算组件进行利润计算
- 接受输入参数：绿标价格、黑标价格、佣金率、重量 ，输出计算结果：利润率、利润金额
- 提供标准化的计算接口和结果格式
- 通过Excel计算器文件初始化组件实例，支持单个实例处理多次计算请求


## Impact

- Affected specs: profit-calculator (new capability)
- Affected code: apps/xuanping/common/excel_calculator.py
- 为选品系统提供标准化的利润计算能力
