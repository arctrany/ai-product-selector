# 轻量级工作流引擎 - Prefect 集成项目

本项目在 `src_new` 目录下集成了 **Prefect** 工作流引擎,满足以下核心需求:
- ✅ 跨平台支持(Windows/Mac/Linux)
- ✅ 轻量级,资源占用少
- ✅ 灵活的 API 控制
- ✅ 包含流程设计器和任务管理 UI
- ✅ 支持 Python 代码节点
- ✅ 支持循环逻辑的暂停和恢复执行

## 📋 目录结构

```
src_new/
├── requirements.txt          # 项目依赖
├── README.md                 # 本文档
├── workflows/                # 工作流定义
│   ├── basic_workflow.py     # 基础工作流示例
│   └── pause_resume_workflow.py  # 暂停/恢复功能演示
├── utils/                    # 工具脚本
│   └── control_api.py        # API 控制工具
└── flows/                    # 流程定义(预留)
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd src_new
pip install -r requirements.txt
```

### 2. 启动 Prefect 服务器(可选,用于 UI 界面)

Prefect 提供了一个现代化的 Web UI 来管理和监控工作流:

```bash
# 启动 Prefect 服务器
prefect server start
```

访问 UI: http://localhost:4200

### 3. 运行基础工作流示例

```bash
cd workflows
python basic_workflow.py
```

这个示例演示了:
- 任务定义和依赖管理
- 数据在任务间传递
- 错误处理和验证

### 4. 运行暂停/恢复功能演示

这是**核心功能验证**,演示如何在循环逻辑中暂停和恢复执行。

#### 步骤 1: 启动工作流(在终端1)

```bash
cd workflows
python pause_resume_workflow.py
```

工作流将在处理 3 个项目后自动暂停,并显示暂停提示。

#### 步骤 2: 查看暂停的工作流(在终端2)

```bash
cd utils
python control_api.py list
```

这将列出所有工作流运行,找到状态为 "Paused" 的工作流 ID。

#### 步骤 3: 恢复工作流执行(在终端2)

```bash
python control_api.py resume <flow_run_id>
```

将 `<flow_run_id>` 替换为实际的工作流 ID。

终端1 中的工作流将立即恢复执行,继续处理剩余项目。

## 📚 详细功能说明

### 基础工作流 (basic_workflow.py)

演示 Prefect 的核心功能:

```python
from prefect import flow, task

@task
def prepare_data(data_size: int):
    # 准备数据
    return data

@task
def process_data(data: list):
    # 处理数据
    return result

@flow
def basic_data_pipeline(data_size: int = 10):
    raw_data = prepare_data(data_size)
    processed_data = process_data(raw_data)
    return processed_data
```

**特点:**
- 使用 `@task` 装饰器定义任务
- 使用 `@flow` 装饰器定义工作流
- 自动管理任务依赖关系
- 内置错误处理和重试机制

### 暂停/恢复工作流 (pause_resume_workflow.py)

演示如何在循环逻辑中实现暂停和恢复:

```python
from prefect import flow, pause_flow_run

@flow
def pausable_loop_workflow(items_count: int = 10, pause_after: int = 3):
    items = initialize_loop_task(items_count)
    results = []
    
    for i, item in enumerate(items, 1):
        result = process_item_in_loop(item, i, len(items))
        results.append(result)
        
        # 在指定位置暂停
        if i == pause_after:
            pause_flow_run(timeout=3600)  # 暂停最多1小时
    
    return {"results": results}
```

**核心功能:**
1. **循环处理**: 在循环中处理多个项目
2. **动态暂停**: 在任意位置调用 `pause_flow_run()` 暂停
3. **状态保存**: 暂停时保存所有状态(变量、进度等)
4. **API 恢复**: 通过 API 恢复后,从暂停点继续执行
5. **超时控制**: 设置暂停超时时间

### API 控制工具 (control_api.py)

提供命令行工具来控制工作流:

#### 列出所有工作流运行

```bash
python control_api.py list
```

输出示例:
```
找到 3 个工作流运行:

1. ⏸️  Flow Run ID: abc-123-def-456
   名称: pausable-loop-workflow
   状态: Paused
   开始时间: 2025-10-21 23:30:00
   ⚠️  此工作流已暂停，可以恢复执行

2. ✅ Flow Run ID: xyz-789-ghi-012
   名称: basic-data-pipeline
   状态: Completed
   开始时间: 2025-10-21 23:25:00
```

#### 恢复指定的工作流

```bash
python control_api.py resume abc-123-def-456
```

#### 查看工作流日志

```bash
python control_api.py logs abc-123-def-456
```

## 🎨 Prefect UI 功能

启动 Prefect 服务器后,访问 http://localhost:4200 可以使用以下功能:

1. **流程设计器**: 可视化查看和管理工作流
2. **任务监控**: 实时查看任务执行状态
3. **日志查看**: 集中查看所有日志
4. **手动触发**: 在 UI 中手动触发工作流
5. **参数配置**: 为工作流配置不同的参数
6. **暂停/恢复控制**: 在 UI 中控制工作流的暂停和恢复

## 🔧 高级功能

### 1. 自定义 UI

Prefect 支持通过 API 定制 UI:

```python
from prefect.server.api.server import create_app

# 创建自定义 API 端点
app = create_app()

@app.get("/custom/endpoint")
def custom_endpoint():
    return {"message": "Custom endpoint"}
```

### 2. 集成外部系统

Prefect 支持与各种外部系统集成:

```python
from prefect_aws import S3Bucket
from prefect_docker import DockerContainer

@task
def upload_to_s3(data):
    s3_bucket = S3Bucket.load("my-bucket")
    s3_bucket.upload_from_path("data.json", data)

@task
def run_in_docker(command):
    container = DockerContainer.load("my-container")
    result = container.run(command)
    return result
```

### 3. 调度和触发

```python
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

# 每天凌晨2点运行
deployment = Deployment.build_from_flow(
    flow=basic_data_pipeline,
    name="daily-pipeline",
    schedule=CronSchedule(cron="0 2 * * *")
)
```

## 📊 性能特点

- **轻量级**: 最小化资源占用,适合本地开发
- **高性能**: 支持并行执行,高效处理大量任务
- **可扩展**: 可以从本地部署扩展到 Kubernetes 集群
- **容错性**: 内置重试机制和错误处理

## 🆚 与其他工作流引擎对比

| 特性 | Prefect | Airflow | Windmill |
|------|---------|---------|----------|
| 学习曲线 | 低 | 高 | 中 |
| 动态工作流 | ✅ 强力支持 | ⚠️ 有限 | ✅ 支持 |
| 本地运行 | ✅ 简单 | ⚠️ 复杂 | ✅ 简单 |
| UI 体验 | ✅ 现代化 | ✅ 成熟 | ✅ 优秀 |
| Python 原生 | ✅ 是 | ✅ 是 | ❌ 否(Rust) |
| 暂停/恢复 | ✅ 原生支持 | ⚠️ 有限 | ✅ 支持 |
| 资源占用 | ✅ 低 | ⚠️ 高 | ✅ 极低 |

## 🛠️ 故障排查

### 1. Prefect 服务器启动失败

```bash
# 重置数据库
prefect database reset -y

# 重新启动
prefect server start
```

### 2. 工作流无法暂停

确保:
- Prefect 服务器正在运行
- 使用正确的工作流 ID
- 工作流状态是 "Running" 或 "Paused"

### 3. API 控制失败

检查:
```bash
# 检查 Prefect 配置
prefect config view

# 测试连接
python -c "from prefect.client.orchestration import get_client; import asyncio; asyncio.run(get_client().__aenter__())"
```

## 📖 参考资源

- [Prefect 官方文档](https://docs.prefect.io/)
- [Prefect GitHub](https://github.com/PrefectHQ/prefect)
- [Prefect 社区](https://discourse.prefect.io/)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📄 许可证

本项目使用 MIT 许可证。
