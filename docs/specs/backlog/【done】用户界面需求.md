# 需求
每个scene下拥有自己的表单输入，
实现一个页面，代替[scene_interface.py](..%2Fsrc%2Fplayweight%2Fscenes%2Fscene_interface.py)的实现
这个表单里的内容：

```json

{
  "dialogTitle": null,
  "height": 0,
  "width": 0,
  "timeout": 0,
  "autoCloseButton": "确定",
  "use_wait_timeout": false,
  "canRememberContent": false,
  "settings": {
    "editors": [
      {
        "type": "File",
        "label": "好店模版文件",
        "VariableName": "good_shop_file",
        "kind": 0,
        "filter": "Excel文件|*.xls;*.xlsx",
        "value": null,
        "nullText": "请选择路径",
        "id": "78b1c0db-ba08-42ac-a1ca-5cc08ebf2a0a"
      },
      {
        "type": "File",
        "label": "采品文件",
        "VariableName": "item_collect_file",
        "kind": 0,
        "filter": "Excel文件|*.xls;*.xlsx",
        "value": null,
        "nullText": "请选择商品",
        "id": "942d257e-dfa0-4a7a-a288-fc71ff1e8ebc"
      },
      {
        "type": "File",
        "label": "计算器文件",
        "VariableName": "margin_calculator",
        "kind": 0,
        "filter": "Excel文件|*.xls;*.xlsx",
        "value": null,
        "nullText": "请选择路径",
        "id": "b4e7f737-5f50-44d9-8818-108c835bd03c"
      },
      {
        "type": "Number",
        "label": "利润率大于等于",
        "VariableName": "margin",
        "value": 0.1,
        "maxValue": null,
        "minValue": null,
        "useFloat": true,
        "id": "c4cd95ce-0d3a-4180-991e-db85ca954e01"
      },
      {
        "type": "Number",
        "label": "商品创建天数小于等于",
        "VariableName": "item_created_days",
        "value": 150,
        "maxValue": null,
        "minValue": null,
        "useFloat": false,
        "id": "b67f4761-ffae-4685-9dad-c10546534e72"
      },
      {
        "type": "Number",
        "label": "跟卖数量小于",
        "VariableName": "follow_buy_cnt",
        "value": 37,
        "maxValue": null,
        "minValue": null,
        "useFloat": true,
        "id": "66ab9a00-643e-4101-9d8a-836c57553742"
      },
      {
        "type": "Number",
        "label": "月销量大于等于",
        "VariableName": "max_monthly_sold",
        "value": 0,
        "maxValue": null,
        "minValue": null,
        "useFloat": false,
        "id": "3baba30f-9158-4df4-a21b-e0a5b969c139"
      },
      {
        "type": "Number",
        "label": "月销量小于等于",
        "VariableName": "monthly_sold_min",
        "value": 100,
        "maxValue": null,
        "minValue": null,
        "useFloat": false,
        "id": "7edad03b-65ec-4d35-b074-bb4896af89c8"
      },
      {
        "type": "Number",
        "label": "商品最小重量（g）",
        "VariableName": "item_min_weigt",
        "value": 0,
        "maxValue": null,
        "minValue": null,
        "useFloat": false,
        "id": "1dfd29e5-2ee7-41af-88b3-28bed5438b43"
      },
      {
        "type": "Number",
        "label": "商品最大数量（g）",
        "VariableName": "item_max_weight",
        "value": 1000,
        "maxValue": null,
        "minValue": null,
        "useFloat": false,
        "id": "f86d2e3d-9d8f-4546-9d32-12816fe14c11"
      },
      {
        "type": "Number",
        "label": "G01商品最小售价（₽）",
        "VariableName": "g01_item_min_price",
        "value": 0,
        "maxValue": null,
        "minValue": null,
        "useFloat": false,
        "id": "52f9ccf8-d054-464f-ab78-868354969dc7"
      },
      {
        "type": "Number",
        "label": "G01商品最大售价（₽）",
        "VariableName": "g01_item_max_price",
        "value": 1000,
        "maxValue": null,
        "minValue": null,
        "useFloat": false,
        "id": "cd7bcd90-9570-4392-b199-684d82cf35fb"
      }
    ],
    "buttons": [
      {
        "type": "Button",
        "label": "确定",
        "theme": "white",
        "hotKey": "Return",
        "id": "92c4e7ff-a302-4949-861f-f3c848b0ba97"
      },
      {
        "type": "Button",
        "label": "取消",
        "theme": "white",
        "hotKey": "Escape",
        "id": "25d8b975-1b18-4d1c-a656-93c4eb8de9fe"
      }
    ]
  }
}

```
1. 用户在「任意」浏览器里输入 http://127.0.0.1:7788/app=${id}， 浏览器会根据id路由器打开一个scene的页面，现在id可以为空，显示默认的表单
2. 设计表单页面、标题是「智能选品」
3. 请捕获上述关键的属性实现表单，页面在确认、取消按钮旁边，增加一个checkbox，表明是否需要记住用户选择。
4. 用户在提交表单后,forward一个控制台页面输出，控制台里包括控制按钮，启动、停止、暂停。展示时间消耗。
5. 系统读取表单内容。例如将good_shop_file 赋指给 scene里的程序，然后执行店铺、商品的自动化程序。并将内容实时输出到控制台页面。

# 实现要求
1. 把seefar_main 和 user_interface 重写，支持web服务,接受表单。 
2. 控制台的页面、以及控制逻辑来自底层系统框架，不要写在scenes里，放到引擎里。
3. 用python最广泛验证的技术实现。

