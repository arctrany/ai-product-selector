## Why

当前 `apps/xuanping` 目录已存在基础结构（common、item_selector、shop_selector），但缺乏完整的工作流定义和 RPA 自动化能力。需要构建一个基于 workflow_engine 和浏览器 RPA 的完整小程序，实现店铺裂变流程和智能选品流程两个核心业务场景。

这个需求涉及复杂的跨系统集成：
- 需要整合现有的 Excel 利润计算器功能
- 需要利用 src_new/rpa/browser 的浏览器自动化能力
- 需要设计复杂的工作流状态管理和错误处理
- 需要实现 RPA 节点与 workflow_engine 的深度集成

## What Changes

- **新增完整的 xuanping 应用配置** - 创建 `apps/xuanping/app.json` 定义应用元数据和流程配置
- **实现店铺裂变工作流** - 基于浏览器 RPA 的自动化店铺发现和数据采集流程
- **实现智能选品工作流** - 结合利润计算器和 RPA 的商品分析和筛选流程
- **新增 RPA 工作流节点类型** - 扩展 workflow_engine 支持浏览器自动化节点
- **集成现有利润计算器** - 将 `apps/xuanping/common/excel_calculator.py` 集成到工作流中
- **实现工作流间数据传递** - 支持店铺裂变结果作为选品流程输入
- **新增错误处理和重试机制** - 针对 RPA 操作的特殊错误处理策略
- **创建专用的 Web 控制台界面** - 为 xuanping 应用定制的操作界面

## Impact

- **影响的规范**: 需要新增 `xuanping-app` 和 `rpa-workflow-integration` 两个新的能力规范
- **影响的代码**: 
  - `apps/xuanping/` - 完整的应用结构和工作流定义
  - `src_new/workflow_engine/nodes/` - 新增 RPA 节点类型
  - `src_new/workflow_engine/sdk/` - 扩展 SDK 支持 RPA 操作
  - `src_new/rpa/browser/` - 可能需要适配工作流集成
  - `src_new/workflow_engine/templates/` - 新增 xuanping 专用模板

**架构影响**: 这是一个跨系统的复杂集成，涉及工作流引擎、RPA 系统、Excel 处理、Web 界面等多个组件的协调工作。需要仔细设计接口和数据流，确保系统的可维护性和扩展性。