# Python 代码审查规范

## 概述

本文档定义了 AI 选品自动化系统项目的 Python 代码审查标准和规范。所有代码提交 **MUST** 遵循这些规则，以确保代码质量、可维护性和跨平台兼容性。

---

## 1. 项目结构规范

### 1.1 目录组织 **MUST** 遵循的结构

```
ai-product-selector3/
├── cli/                  # 命令行接口模块
├── common/               # 核心业务逻辑模块
│   ├── models/          # 数据传输对象和业务实体
│   ├── config/          # 配置管理
│   ├── utils/           # 工具类和辅助函数
│   ├── business/        # 业务逻辑实现
│   ├── scrapers/        # 页面交互和数据抓取
│   └── services/        # 服务层实现
├── task_manager/         # 任务管理框架
├── rpa/                  # 浏览器自动化模块
│   ├── browser/         # 浏览器核心实现
│   └── docs/            # 浏览器相关文档
├── tests/                # 测试套件
├── utils/                # 工具函数模块
├── packaging/            # 打包和发布模块
├── docs/                 # 项目文档
└── openspec/             # 项目规范和变更管理
```

### 1.2 文件组织原则

- **MUST** 按功能模块组织代码，避免巨型文件
- **MUST** 将相关功能放在同一模块内
- **SHOULD** 单个 Python 文件不超过 500 行
- **MUST** 避免循环依赖

---

## 2. 命名规范

### 2.1 文件和目录命名 **MUST** 使用 `snake_case`

```python
# ✅ 正确
main.py
logging_config.py
task_controller.py
user_data_manager.py

# ❌ 错误
Main.py
LoggingConfig.py
taskController.py
UserDataManager.py
```

### 2.2 类命名 **MUST** 使用 `PascalCase`

```python
# ✅ 正确
class TaskController:
    pass

class UserDataManager:
    pass

class GoodStoreSelectorConfig:
    pass

# ❌ 错误
class taskController:
    pass

class user_data_manager:
    pass
```

### 2.3 函数和变量命名 **MUST** 使用 `snake_case`

```python
# ✅ 正确
def create_parser():
    pass

def load_user_data(file_path):
    pass

ui_config = UIConfig()
system_config = GoodStoreSelectorConfig()

# ❌ 错误
def createParser():
    pass

def LoadUserData(filePath):
    pass

uiConfig = UIConfig()
```

### 2.4 常量命名 **MUST** 使用 `UPPER_CASE`

```python
# ✅ 正确
CREATE_VENV = False
PLATFORM_TAG = "linux-x64"
DEFAULT_TIMEOUT = 30
MAX_RETRY_COUNT = 3

# ❌ 错误
create_venv = False
platformTag = "linux-x64"
```

### 2.5 私有成员命名 **SHOULD** 使用前导下划线

```python
# ✅ 推荐
class UserManager:
    def __init__(self):
        self._internal_state = {}
        self.__private_data = None
    
    def _internal_method(self):
        pass

# ❌ 避免
class UserManager:
    def __init__(self):
        self.internal_state = {}  # 应该标记为私有
```

---

## 3. 代码风格规范

### 3.1 导入语句组织 **MUST** 遵循顺序

```python
# ✅ 正确的导入顺序
# 1. 标准库导入
import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict

# 2. 第三方库导入
import requests
import openpyxl
from playwright.sync_api import Browser

# 3. 本地模块导入
from cli.models import UIConfig
from common.logging_config import setup_logging
from task_manager.controllers import TaskController
```

### 3.2 导入语句规范

- **MUST** 使用绝对导入，避免相对导入
- **MUST** 每行只导入一个模块
- **SHOULD** 避免使用 `import *`
- **MUST** 按字母顺序排列同类导入

```python
# ✅ 正确
import json
import logging
import os

from cli.models import UIConfig
from common.config import SystemConfig

# ❌ 错误
import json, logging, os  # 多个导入在一行
from cli.models import *  # 通配符导入
from .models import UIConfig  # 相对导入
```

### 3.3 文档字符串 **MUST** 使用规范格式

```python
# ✅ 正确
def load_user_data(data_path: str) -> UIConfig:
    """
    加载用户输入数据
    
    Args:
        data_path: 用户数据文件路径
        
    Returns:
        UIConfig: 用户配置对象
        
    Raises:
        FileNotFoundError: 当文件不存在时抛出
        JSONDecodeError: 当JSON格式错误时抛出
    """
    # 实现代码
```

### 3.4 注释规范

- **MUST** 使用中文注释（符合团队习惯）
- **SHOULD** 解释"为什么"而不是"是什么"
- **MUST** 避免过时或误导性注释
- **SHOULD** 在复杂逻辑前添加解释性注释

```python
# ✅ 正确
# 检查并警告废弃的字段，保持向后兼容
deprecated_fields = []
if 'item_created_days' in data_dict:
    deprecated_fields.append('item_created_days')

# 验证店铺过滤参数，确保业务逻辑正确性
if ui_config.min_store_sales_30days < 0:
    print(f"❌ 错误: min_store_sales_30days 必须为正数")
    
# ❌ 避免
# 创建列表
deprecated_fields = []
# 如果字段存在就添加
if 'item_created_days' in data_dict:
    deprecated_fields.append('item_created_days')
```

---

## 4. Clean Code 原则

### 4.1 函数设计原则

- **MUST** 单一职责：一个函数只做一件事
- **SHOULD** 函数长度不超过 50 行
- **MUST** 参数不超过 5 个，复杂参数使用数据类或字典
- **MUST** 有明确的返回类型

```python
# ✅ 正确：职责单一，参数清晰
def validate_store_filter_params(min_sales: float, min_orders: int) -> bool:
    """验证店铺过滤参数"""
    if min_sales < 0:
        return False
    if min_orders < 0:
        return False
    return True

# ❌ 错误：职责过多
def handle_everything(data, config, logger, state, manager):
    # 做了太多事情...
```

### 4.2 类设计原则

- **MUST** 类的职责要清晰明确
- **SHOULD** 避免过大的类（超过 300 行）
- **MUST** 正确使用继承和组合
- **MUST** 实现必要的魔法方法（`__str__`, `__repr__` 等）

### 4.3 错误处理 **MUST** 遵循的模式

```python
# ✅ 正确：具体的异常处理和错误消息
try:
    with open(data_path, 'r', encoding='utf-8') as f:
        data_dict = json.load(f)
except FileNotFoundError:
    print(f"❌ 用户数据文件不存在: {data_path}")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"❌ 用户数据JSON格式错误: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 加载用户数据失败: {e}")
    sys.exit(1)

# ❌ 错误：捕获所有异常但不处理
try:
    # 一些操作
    pass
except:
    pass  # 静默忽略所有错误
```

### 4.4 日志记录规范

- **MUST** 使用标准 `logging` 模块
- **MUST** 记录关键操作和错误信息
- **SHOULD** 使用适当的日志级别
- **MUST** 包含足够的上下文信息

```python
# ✅ 正确
import logging

logger = logging.getLogger(__name__)

def process_store_data(store_id: str):
    logger.info(f"开始处理店铺数据: {store_id}")
    try:
        # 处理逻辑
        result = some_operation()
        logger.info(f"店铺 {store_id} 处理完成，结果: {result}")
        return result
    except Exception as e:
        logger.error(f"处理店铺 {store_id} 时发生错误: {e}", exc_info=True)
        raise
```

---

## 5. 跨平台兼容性 **MUST** 遵循的规范

### 5.1 路径处理 **MUST** 使用 `pathlib`

```python
# ✅ 正确：使用 pathlib.Path
from pathlib import Path

def get_log_directory() -> Path:
    """获取日志目录路径"""
    return Path.home() / ".xuanping" / "data" / "logs"

def ensure_directory_exists(path: Path):
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)

# ❌ 错误：使用字符串拼接路径
import os

def get_log_directory():
    return os.path.join(os.path.expanduser("~"), ".xuanping", "data", "logs")
```

### 5.2 文件操作 **MUST** 考虑编码

```python
# ✅ 正确：明确指定编码
def load_json_file(file_path: Path) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_text_file(file_path: Path, content: str):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

# ❌ 错误：依赖系统默认编码
def load_json_file(file_path):
    with open(file_path, 'r') as f:  # 可能在不同系统有不同编码
        return json.load(f)
```

### 5.3 命令执行 **MUST** 考虑平台差异

```python
# ✅ 正确：跨平台命令执行
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list, cwd: Path = None) -> subprocess.CompletedProcess:
    """跨平台命令执行"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败: {' '.join(cmd)}, 错误: {e}")
        raise

# 平台特定的可执行文件处理
def get_executable_name(base_name: str) -> str:
    """获取跨平台的可执行文件名"""
    if sys.platform.startswith('win'):
        return f"{base_name}.exe"
    return base_name
```

### 5.4 环境变量和配置 **MUST** 提供默认值

```python
# ✅ 正确：提供跨平台默认配置
import os
from pathlib import Path

def get_config_directory() -> Path:
    """获取配置目录，跨平台兼容"""
    if os.name == 'nt':  # Windows
        config_dir = Path(os.environ.get('APPDATA', Path.home())) / 'ai-product-selector'
    else:  # Unix-like systems
        config_dir = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'ai-product-selector'
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir
```

---

## 6. 性能和资源管理

### 6.1 资源管理 **MUST** 使用上下文管理器

```python
# ✅ 正确：使用 with 语句
def process_excel_file(file_path: Path) -> dict:
    with open(file_path, 'rb') as f:
        workbook = openpyxl.load_workbook(f)
        # 处理文件
        return extract_data(workbook)

# ✅ 正确：自定义上下文管理器
class DatabaseConnection:
    def __enter__(self):
        self.conn = create_connection()
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
```

### 6.2 避免内存泄漏

- **MUST** 及时关闭文件句柄和网络连接
- **SHOULD** 避免创建不必要的大对象
- **MUST** 在长时间运行的循环中释放资源

```python
# ✅ 正确：及时释放资源
def process_large_dataset(data_source):
    for batch in data_source.get_batches():
        try:
            result = process_batch(batch)
            yield result
        finally:
            # 确保批次数据被清理
            del batch
```

---

## 7. 类型注解 **MUST** 的使用规范

### 7.1 函数签名 **MUST** 包含类型注解

```python
# ✅ 正确
from typing import Optional, List, Dict, Union
from pathlib import Path

def load_user_data(data_path: str) -> UIConfig:
    pass

def process_stores(store_ids: List[str], config: Optional[Dict] = None) -> List[Dict]:
    pass

def get_file_size(path: Path) -> Optional[int]:
    if path.exists():
        return path.stat().st_size
    return None

# ❌ 错误：缺少类型注解
def load_user_data(data_path):  # 缺少参数和返回值类型
    pass
```

### 7.2 复杂类型 **SHOULD** 使用 Type Alias

```python
# ✅ 正确：定义类型别名
from typing import Dict, List, Union

StoreData = Dict[str, Union[str, int, float]]
ProductList = List[StoreData]
ConfigDict = Dict[str, Union[str, int, bool]]

def process_products(products: ProductList) -> ConfigDict:
    pass
```

---

## 8. 测试规范

### 8.1 测试文件组织 **MUST** 遵循结构

```
tests/
├── unit/                 # 单元测试
│   ├── test_cli/
│   ├── test_common/
│   └── test_task_manager/
├── integration/          # 集成测试
└── fixtures/             # 测试数据和装置
```

### 8.2 测试命名 **MUST** 使用描述性名称

```python
# ✅ 正确
def test_load_user_data_with_valid_json_returns_ui_config():
    pass

def test_load_user_data_with_missing_file_raises_file_not_found_error():
    pass

def test_validate_store_filter_params_with_negative_sales_returns_false():
    pass

# ❌ 错误
def test_load_data():
    pass

def test_error():
    pass
```

### 8.3 测试标记 **MUST** 正确使用

```python
import pytest

@pytest.mark.unit
def test_basic_functionality():
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_full_workflow():
    pass

@pytest.mark.browser
def test_playwright_functionality():
    pass
```

---

## 9. 依赖管理和版本控制

### 9.1 依赖管理 **MUST** 遵循规范

- **MUST** 在 `requirements.txt` 中固定版本号
- **SHOULD** 定期更新依赖包
- **MUST** 避免引入不必要的依赖

```txt
# ✅ 正确：固定版本
playwright>=1.40.0
openpyxl>=3.1.0
requests>=2.31.0

# ❌ 错误：未固定版本
playwright
openpyxl
requests
```

### 9.2 兼容性要求

- **MUST** 支持 Python 3.8+
- **MUST** 兼容 Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **SHOULD** 避免使用过于新的语言特性

---

## 10. 安全性规范

### 10.1 输入验证 **MUST** 进行

```python
# ✅ 正确：输入验证
def validate_file_path(path: str) -> bool:
    """验证文件路径的安全性"""
    path_obj = Path(path).resolve()
    
    # 检查路径遍历攻击
    if '..' in str(path_obj):
        return False
    
    # 检查是否在允许的目录内
    allowed_dirs = [Path.cwd(), Path.home()]
    if not any(path_obj.is_relative_to(allowed_dir) for allowed_dir in allowed_dirs):
        return False
    
    return True
```

### 10.2 敏感信息处理

- **MUST** 避免在代码中硬编码密码或密钥
- **MUST** 在日志中屏蔽敏感信息
- **SHOULD** 使用环境变量存储配置

```python
# ✅ 正确：使用环境变量
import os

API_KEY = os.environ.get('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY 环境变量未设置")

# ❌ 错误：硬编码敏感信息
API_KEY = "sk-1234567890abcdef"  # 不要这样做
```

---

## 11. 代码审查检查点

### 11.1 **MUST** 检查的项目

- [ ] 代码遵循命名规范
- [ ] 所有函数都有类型注解
- [ ] 导入语句按规范组织
- [ ] 错误处理完整且具体
- [ ] 使用 pathlib 处理路径
- [ ] 文件操作指定编码
- [ ] 资源管理使用上下文管理器
- [ ] 测试覆盖率 >= 80%
- [ ] 无安全漏洞
- [ ] 跨平台兼容性

### 11.2 **SHOULD** 检查的项目

- [ ] 代码注释清晰有用
- [ ] 函数长度合理（<50行）
- [ ] 类的职责单一
- [ ] 性能优化合理
- [ ] 日志记录完整

### 11.3 **MAY** 考虑的改进

- [ ] 代码风格一致性
- [ ] 更好的抽象设计
- [ ] 性能优化机会
- [ ] 用户体验改进

---

## 12. 工具和自动化

### 12.1 **MUST** 使用的工具

- **pytest**: 测试框架
- **black**: 代码格式化（如果团队采用）
- **flake8**: 代码检查
- **mypy**: 类型检查

### 12.2 **SHOULD** 使用的工具

- **pre-commit**: 提交前检查
- **coverage**: 测试覆盖率
- **bandit**: 安全检查

---

## 13. 违规处理

### 13.1 严重违规（**MUST** 规则）

- **MUST** 在合并前修复
- 影响系统稳定性或安全性
- 破坏跨平台兼容性

### 13.2 一般违规（**SHOULD** 规则）

- 可在后续迭代中改进
- 不影响功能但影响可维护性
- 需要添加 TODO 注释说明改进计划

### 13.3 建议改进（**MAY** 规则）

- 可选择性采纳
- 主要关注代码优雅性
- 需要权衡改进成本和收益

---

## 附录：常见问题和示例

### A.1 路径处理示例

```python
# ✅ 跨平台路径处理
from pathlib import Path

def get_user_data_path() -> Path:
    """获取用户数据路径"""
    return Path.home() / '.ai-product-selector' / 'data'

def ensure_config_exists(config_path: Path):
    """确保配置文件存在"""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if not config_path.exists():
        config_path.write_text('{}', encoding='utf-8')
```

### A.2 异步代码规范

```python
# ✅ 正确的异步代码
import asyncio
from typing import List

async def fetch_store_data(store_id: str) -> dict:
    """异步获取店铺数据"""
    # 实现异步逻辑
    pass

async def process_multiple_stores(store_ids: List[str]) -> List[dict]:
    """并发处理多个店铺"""
    tasks = [fetch_store_data(store_id) for store_id in store_ids]
    return await asyncio.gather(*tasks)
```

---

*本规范将根据项目发展和团队反馈持续更新。最后更新：2025-11-26*