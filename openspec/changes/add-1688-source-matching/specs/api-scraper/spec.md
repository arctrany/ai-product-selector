## ADDED Requirements

### Requirement: 1688 API相似商品搜索
系统 SHALL 提供1688 API相似商品搜索功能，根据商品图片URL搜索1688平台上的相似商品。

#### Scenario: 成功调用1688 API
- **WHEN** 系统提供商品图片URL且配置了有效的1688访问令牌
- **THEN** 系统调用1688相似商品搜索API
- **AND** API请求包含必需参数：`imageUrl`、`access_token`、`_aop_signature`、`pageSize`、`currentPage`
- **AND** 系统按照1688签名规则生成 `_aop_signature`
- **AND** 从环境变量 `XP_ATK` 获取 `access_token`
- **AND** API成功返回相似商品列表（最多10个商品）

#### Scenario: API签名生成
- **WHEN** 系统需要调用1688 API
- **THEN** 系统按照1688签名规则生成 `_aop_signature`
- **AND** 签名规则参考：https://open.1688.com/doc/signature.htm
- **AND** 签名包含所有请求参数（按字典序排序）
- **AND** 签名使用正确的签名算法（HMAC-SHA1）

#### Scenario: API响应解析
- **WHEN** 1688 API成功返回响应
- **THEN** 系统解析JSON响应
- **AND** 提取商品列表数据
- **AND** 每个商品包含以下字段：offerId、subject、quantityBegin、unit、oldPrice、imageUrl、province、city、supplyAmount、categoryId
- **AND** 返回结构化的商品信息列表

#### Scenario: API分页处理
- **WHEN** 系统调用1688 API
- **THEN** 系统请求第一页数据（currentPage=1）
- **AND** 设置每页数量为10（pageSize=10）
- **AND** 只处理第一页结果，不进行分页遍历

#### Scenario: API重试机制
- **WHEN** 1688 API调用失败（网络错误、超时等）
- **THEN** 系统自动重试（最多2次）
- **AND** 重试间隔至少1秒（遵守API限流规则）
- **AND** 如果重试后仍失败，返回错误信息

#### Scenario: API超时控制
- **WHEN** 系统调用1688 API
- **THEN** 系统设置超时时间为20秒（可配置）
- **AND** 如果超过超时时间未响应，取消请求
- **AND** 记录超时错误到日志

#### Scenario: API限流遵守
- **WHEN** 系统需要调用1688 API
- **THEN** 系统遵守API限流规则（最多1秒一次）
- **AND** 在连续调用之间添加延迟
- **AND** 记录API调用时间，避免过快调用

#### Scenario: 访问令牌获取
- **WHEN** 系统需要调用1688 API
- **THEN** 系统从环境变量 `XP_ATK` 获取访问令牌
- **AND** 如果环境变量未设置，返回错误："错误: 未设置1688访问令牌，请设置环境变量 XP_ATK"
- **AND** 验证访问令牌格式（非空字符串）

#### Scenario: 错误响应处理
- **WHEN** 1688 API返回错误响应（认证失败、参数错误等）
- **THEN** 系统解析错误信息
- **AND** 记录错误详情到日志
- **AND** 返回结构化的错误信息
- **AND** 不进行重试（认证错误等不可重试的错误）

#### Scenario: 网络错误处理
- **WHEN** 1688 API调用发生网络错误（连接失败、DNS解析失败等）
- **THEN** 系统捕获网络异常
- **AND** 记录错误详情到日志
- **AND** 触发重试机制（如果是可重试的错误）
- **AND** 如果所有重试都失败，返回错误信息

#### Scenario: 响应数据验证
- **WHEN** 1688 API返回响应
- **THEN** 系统验证响应格式（JSON格式）
- **AND** 验证必需字段存在（offerId、subject、oldPrice等）
- **AND** 验证数据类型正确（oldPrice为数字，offerId为字符串等）
- **AND** 如果数据验证失败，记录警告并跳过该商品

#### Scenario: 空结果处理
- **WHEN** 1688 API返回空结果列表
- **THEN** 系统返回空列表
- **AND** 记录"未找到相似商品"到日志
- **AND** 不抛出异常，正常返回

#### Scenario: 日志记录
- **WHEN** 系统调用1688 API
- **THEN** 系统记录以下信息到日志：
  - API请求参数（隐藏敏感信息如access_token）
  - API响应状态码
  - 返回的商品数量
  - 处理耗时
  - 错误信息（如果有）

