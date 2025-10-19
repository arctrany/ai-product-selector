# Console模块重构

## 重构目标
将 seefar_web.py 里和业务逻辑相关的代码分离出来，放到 web_console_api 里，确保系统逻辑不依赖 scenes。

## 重构成果

### ✅ 完成的API路由分离
- `/api/task/*` - 任务管理API
- `/api/browser/*` - 浏览器控制API  
- `/api/console/*` - 控制台状态API
- `/console` - 控制台页面（保留在场景模块）

### ✅ 架构优化
1. **完全解耦**: `web_console_api.py` 不再包含任何业务逻辑硬编码
2. **依赖注入**: 使用 `register_task_executor()` 注册执行器
3. **配置动态化**: 任务名称和参数由执行器决定，API层完全通用

### ✅ 文件结构
- `src/web/web_console_api.py` - 纯API接口模块
- `src/playweight/scenes/web/seerfar_web.py` - 场景相关路由

### ✅ 关键改进
- 移除硬编码的"智能选品自动化任务"
- 移除硬编码的 `total_items=10`
- 使用执行器的 `get_task_config()` 方法动态获取任务配置
- API层完全与具体业务解耦

## 使用方式
业务模块需要实现并注册执行器：
```python
from web.web_console_api import register_task_executor

class BusinessTaskExecutor:
    def get_task_config(self, form_data):
        return {'name': '业务任务', 'total_items': 10}
    
    async def execute_task(self, task_id, form_data, context):
        # 具体业务逻辑
        pass

register_task_executor(BusinessTaskExecutor())
```

## 架构原则
- ✅ 系统逻辑不依赖 scenes
- ✅ API接口与业务逻辑完全分离
- ✅ 支持插件化扩展
- ✅ 职责分离清晰