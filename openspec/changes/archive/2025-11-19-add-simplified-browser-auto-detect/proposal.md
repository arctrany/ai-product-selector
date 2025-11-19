# 在 SimplifiedBrowserService 中添加浏览器自动检测逻辑

## Why - 为什么需要这个变更？

### 问题背景

在 `support-auto-launch-browser` 变更中，我们成功实现了 `XuanpingBrowserService` 的浏览器自动检测和启动功能，但 **`SimplifiedBrowserService` 的实现不完整**。

### 当前问题

**SimplifiedBrowserService 缺少智能检测逻辑**：

查看 `rpa/browser/browser_service.py` 的 `initialize()` 方法：

```python
# 当前实现：被动接收配置
if connect_to_existing:
    # 连接到现有浏览器
    ...
else:
    # 启动新浏览器
    ...
```

**问题**：
1. ❌ `SimplifiedBrowserService` 不能自动判断是启动还是连接
2. ❌ 必须由上层（如 `XuanpingBrowserService`）来决定
3. ❌ 如果直接使用 `SimplifiedBrowserService`，无法实现自动切换
4. ❌ 与 `XuanpingBrowserService` 的实现不一致

### 对比分析

**XuanpingBrowserService（✅ 正确）**：
```python
def _create_browser_config(self) -> Dict[str, Any]:
    # 智能检测浏览器
    has_browser = self._check_existing_browser(debug_port)
    
    if has_browser:
        # 连接模式
        config['connect_to_existing'] = f"http://localhost:{debug_port}"
    else:
        # 启动模式
        config['connect_to_existing'] = False
```

**SimplifiedBrowserService（❌ 不完整）**：
```python
async def initialize(self) -> bool:
    # 被动接收配置，没有智能检测
    browser_config = self._prepare_browser_config()
    connect_to_existing = browser_config.get('connect_to_existing', None)
    
    if connect_to_existing:
        # 连接
    else:
        # 启动
```

### 用户影响

1. **直接使用 SimplifiedBrowserService 的用户**：
   - 无法享受自动检测和切换功能
   - 必须手动配置 `connect_to_existing`

2. **代码一致性问题**：
   - 两个服务的行为不一致
   - 增加维护成本

3. **违反设计原则**：
   - `SimplifiedBrowserService` 应该是独立可用的
   - 不应该依赖上层服务来实现核心功能

## What Changes - 需要做什么变更？

### 核心变更

在 `SimplifiedBrowserService` 中添加浏览器自动检测逻辑，使其行为与 `XuanpingBrowserService` 一致。

### 实施方案

#### 1. 添加 `_check_existing_browser()` 方法

**文件**: `rpa/browser/browser_service.py`

```python
def _check_existing_browser(self, debug_port: int) -> bool:
    """
    检查是否有现有浏览器在指定调试端口运行
    
    Args:
        debug_port: 调试端口号
        
    Returns:
        bool: 是否有现有浏览器
    """
    try:
        import socket
        import urllib.request
        import json
        
        # 检查端口是否被占用
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', debug_port))
        sock.close()
        
        if result != 0:
            return False
        
        # 验证 CDP 端点是否可用
        cdp_url = f"http://localhost:{debug_port}/json/version"
        try:
            req = urllib.request.Request(cdp_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read().decode('utf-8'))
                return 'webSocketDebuggerUrl' in data
        except Exception:
            return False
            
    except Exception as e:
        self.logger.debug(f"检查现有浏览器失败: {e}")
        return False
```

#### 2. 修改 `initialize()` 方法

**文件**: `rpa/browser/browser_service.py`

```python
async def initialize(self) -> bool:
    """初始化浏览器服务"""
    try:
        if self._initialized:
            return True
        
        self.logger.info("🔧 开始初始化浏览器服务")
        
        # 准备浏览器配置
        browser_config = self._prepare_browser_config()
        
        # 🔧 新增：智能检测浏览器
        debug_port = browser_config.get('debug_port', 9222)
        has_browser = self._check_existing_browser(debug_port)
        
        if has_browser:
            # 连接模式
            self.logger.info(f"🔗 检测到现有浏览器，将连接到端口 {debug_port}")
            browser_config['connect_to_existing'] = f"http://localhost:{debug_port}"
        else:
            # 启动模式
            self.logger.info(f"🚀 未检测到浏览器，将自动启动")
            browser_config['connect_to_existing'] = False
        
        # 后续逻辑保持不变
        connect_to_existing = browser_config.get('connect_to_existing', None)
        
        if connect_to_existing:
            # 连接到现有浏览器
            ...
        else:
            # 启动新浏览器
            ...
```

### 配置支持

确保 `browser_config` 包含 `debug_port` 配置：

```python
def _prepare_browser_config(self) -> Dict[str, Any]:
    """准备浏览器配置"""
    browser_config = self.config.browser_config.to_dict()
    
    # 确保传递调试端口
    if hasattr(self.config.browser_config, 'debug_port'):
        browser_config['debug_port'] = self.config.browser_config.debug_port
    else:
        browser_config['debug_port'] = 9222  # 默认端口
    
    return browser_config
```

## Breaking Changes - 破坏性变更

### 无破坏性变更

本次变更是**功能增强**，不引入破坏性变更：

1. ✅ **向后兼容**：仍然支持手动配置 `connect_to_existing`
2. ✅ **新增功能**：增加自动检测浏览器的能力
3. ✅ **配置兼容**：使用现有的 browser 配置
4. ✅ **行为改进**：从"被动接收配置"改为"主动智能检测"

### 行为变更

- **旧行为**：必须由上层服务配置 `connect_to_existing`
- **新行为**：自动检测浏览器状态并设置 `connect_to_existing`

## Implementation Plan - 实施计划

### 阶段 1：添加检测方法 (P0)

**文件**: `rpa/browser/browser_service.py`

1. 添加 `_check_existing_browser()` 方法
2. 实现端口检查逻辑
3. 实现 CDP 端点验证

**预计时间**: 30 分钟

### 阶段 2：修改 initialize() 方法 (P0)

**文件**: `rpa/browser/browser_service.py`

1. 在 `initialize()` 中调用 `_check_existing_browser()`
2. 根据检测结果设置 `connect_to_existing`
3. 添加日志输出

**预计时间**: 30 分钟

### 阶段 3：测试验证 (P0)

1. **功能测试**
   - [ ] 浏览器未运行 → 自动启动
   - [ ] 浏览器已运行 → 自动连接
   - [ ] 手动配置优先级高于自动检测

2. **兼容性测试**
   - [ ] 与 XuanpingBrowserService 行为一致
   - [ ] 直接使用 SimplifiedBrowserService 正常工作

**预计时间**: 1 小时

### 阶段 4：文档和清理 (P1)

1. 更新注释
2. 清理无用代码
3. 提交代码

**预计时间**: 30 分钟

**总预计时间**: 2.5 小时

## Success Criteria - 成功标准

### 核心功能

1. ✅ SimplifiedBrowserService 能够自动检测浏览器
2. ✅ 检测到浏览器时自动连接
3. ✅ 未检测到浏览器时自动启动
4. ✅ 与 XuanpingBrowserService 行为一致
5. ✅ 手动配置优先级高于自动检测
6. ✅ 所有现有功能正常工作
7. ✅ 无 lint 错误

### 测试覆盖

1. ✅ 自动检测逻辑正确
2. ✅ 端口检查准确
3. ✅ CDP 端点验证有效
4. ✅ 日志输出清晰

## Risks and Mitigations - 风险和缓解措施

### 风险 1：检测逻辑失败

**影响**: 中  
**概率**: 低（复用 XuanpingBrowserService 的成熟实现）  
**缓解措施**:
- 直接复用 XuanpingBrowserService 的 `_check_existing_browser()` 方法
- 充分的测试验证

### 风险 2：与现有配置冲突

**影响**: 低  
**概率**: 低  
**缓解措施**:
- 手动配置优先级高于自动检测
- 保持向后兼容

## Timeline - 时间线

- **Hour 0-0.5**: 添加 `_check_existing_browser()` 方法
- **Hour 0.5-1**: 修改 `initialize()` 方法
- **Hour 1-2**: 测试和验证
- **Hour 2-2.5**: 文档、清理和提交

**总预计时间**: 2.5 小时

## Related Changes - 相关变更

- [support-auto-launch-browser](../archive/2025-11-19-support-auto-launch-browser/proposal.md) - 浏览器自动启动支持（已完成，但 SimplifiedBrowserService 实现不完整）

## Key Insight - 关键洞察

### 设计原则

**SimplifiedBrowserService 应该是独立可用的**

- `SimplifiedBrowserService` 是基础服务层
- 不应该依赖上层服务（如 `XuanpingBrowserService`）来实现核心功能
- 应该具备完整的自动检测和切换能力

### 代码复用

**直接复用 XuanpingBrowserService 的实现**

- `_check_existing_browser()` 方法已经过验证
- 不需要重新实现，直接复用即可
- 确保两个服务的行为完全一致

### 实现策略

**最小化修改，最大化复用**

- 只添加必要的检测逻辑
- 保持现有代码结构不变
- 代码修改量 < 100 行
