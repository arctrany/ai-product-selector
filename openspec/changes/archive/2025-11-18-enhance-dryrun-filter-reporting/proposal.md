# Change: 增强 --dryrun 模式的过滤报告功能

## Why
当前的 `--dryrun` 模式只是简单地记录入参并执行真实的抓取流程，但不保存结果到文件。这对于调试和优化过滤规则帮助有限，用户无法直观地看到：
1. 哪些店铺/商品被过滤掉了
2. 为什么被过滤（具体触发了哪个过滤条件）
3. 过滤规则的实际效果如何

用户需要一个"假"过滤模式，即：
- **不真正执行过滤**（所有店铺和商品都会被处理）
- **但输出详细的过滤判断结果**（每个店铺/商品是否会被过滤、原因是什么）
- **帮助用户调试和优化过滤规则**

## What Changes
- 在 `--dryrun` 模式下，过滤函数返回 `True`（不过滤），但记录详细的过滤判断信息
- 为店铺过滤和商品过滤分别实现过滤报告功能
- 输出结构化的过滤报告，包括：
  - 过滤判断结果（通过/不通过）
  - 触发的具体过滤条件
  - 相关的数据值和阈值对比
- 在日志中清晰标识 dryrun 模式的过滤报告

## Impact
- 影响的规范：
  - `cli/spec.md` - 增强 dryrun 模式的行为定义
  - `store-filtering/spec.md` - 修改过滤函数在 dryrun 模式下的行为
- 影响的代码：
  - `common/business/store_evaluator.py` - 店铺过滤函数
  - `common/business/profit_evaluator.py` - 商品过滤函数
  - `common/scrapers/seerfar_scraper.py` - 调用过滤函数的地方
  - `good_store_selector.py` - 主流程中的过滤逻辑
- 向后兼容：完全兼容，只是增强了 dryrun 模式的输出信息
