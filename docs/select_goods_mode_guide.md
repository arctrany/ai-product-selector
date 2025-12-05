# 选品模式使用指南

## 功能概述

选品模式（select-goods）是一种直接从指定店铺列表中选择有利润商品的功能模式。与店铺筛选模式不同，选品模式跳过店铺过滤步骤，直接分析店铺中的商品并导出有利润的商品到Excel文件。

## 使用场景

- 当您已有确定的店铺列表，想直接选出这些店铺中的有利润商品
- 需要批量分析特定店铺的商品利润情况
- 不需要进行店铺销售额、订单量等筛选

## 使用方法

### 1. 准备输入文件

#### 店铺列表Excel文件
在Excel文件的第一列（A列）填入要分析的店铺ID，例如：
```
A列
店铺ID
123456
234567
345678
```

#### 利润计算器文件
使用系统提供的标准利润计算器Excel文件。

### 2. 创建配置文件

生成选品模式的配置模板：
```bash
python -m cli.main create-template --mode select-goods
```

编辑生成的 `user_data_template_select_goods.json` 文件：
```json
{
  "good_shop_file": "/path/to/店铺列表.xlsx",
  "item_collect_file": "/path/to/item_collect.xlsx",
  "margin_calculator": "/path/to/利润计算器.xlsx",
  "margin": 0.20,
  "item_shelf_days": 150,
  "follow_buy_cnt": 50,
  "max_monthly_sold": 1000,
  "monthly_sold_min": 100,
  "item_min_weight": 0,
  "item_max_weight": 2000,
  "g01_item_min_price": 10,
  "g01_item_max_price": 500
}
```

参数说明：
- `good_shop_file`: 店铺列表Excel文件路径
- `item_collect_file`: 商品收集配置文件（选品模式必需）
- `margin_calculator`: 利润计算器文件路径
- `margin`: 最低利润率要求（0.20 表示 20%）
- 其他参数：商品筛选条件

### 3. 运行选品任务

```bash
python -m cli.main start --data user_data_template_select_goods.json --select-goods
```

试运行模式（不写入文件）：
```bash
python -m cli.main start --data user_data_template_select_goods.json --select-goods --dryrun
```

### 4. 查看结果

程序运行完成后，会在店铺列表文件的同目录下生成 `products_output.xlsx` 文件，包含以下信息：

| 列名 | 说明 |
|------|------|
| 店铺ID | 商品所属店铺 |
| 商品ID | 商品唯一标识 |
| 商品名称 | 商品标题 |
| 商品图片 | 商品主图URL |
| 绿标价格 | 促销价格（卢布） |
| 黑标价格 | 原价（卢布） |
| 佣金率 | 平台佣金比例 |
| 重量(g) | 商品重量 |
| 长(cm) | 商品尺寸 |
| 宽(cm) | 商品尺寸 |
| 高(cm) | 商品尺寸 |
| 货源价格 | 采购成本（人民币） |
| 利润率 | 计算得出的利润率 |
| 预计利润 | 预计利润金额（人民币） |

## 与店铺筛选模式的区别

| 特性 | 选品模式 (select-goods) | 店铺筛选模式 (select-shops) |
|------|------------------------|---------------------------|
| 店铺过滤 | ❌ 不过滤 | ✅ 按销售额、订单量过滤 |
| 跟卖分析 | ❌ 跳过 | ✅ 分析跟卖商品 |
| 输出内容 | 商品列表 | 店铺状态（好店/非好店） |
| 适用场景 | 已确定店铺，直接选品 | 从大量店铺中筛选优质店铺 |

## 注意事项

1. **店铺ID格式**：确保Excel第一列的店铺ID为纯数字格式
2. **批量处理**：系统会自动批量处理商品，每批10个商品写入一次
3. **错误处理**：单个商品处理失败不会影响整批处理
4. **输出位置**：默认在输入Excel文件的同目录下生成结果文件
5. **性能考虑**：建议单次处理不超过100个店铺

## 常见问题

### Q: 为什么有些店铺没有输出商品？
A: 可能原因：
- 该店铺的商品都不满足利润率要求
- 商品数据抓取失败
- 商品不满足筛选条件（重量、价格等）

### Q: 如何调整利润率阈值？
A: 在配置文件中修改 `margin` 参数，例如 0.15 表示 15% 的利润率要求。

### Q: 可以同时运行多个选品任务吗？
A: 不建议同时运行多个任务，以避免浏览器资源冲突。请依次运行任务。

### Q: 如何查看详细的处理日志？
A: 使用以下命令查看日志：
```bash
python -m cli.main logs
```

导出日志到文件：
```bash
python -m cli.main logs --export txt --output logs.txt
```