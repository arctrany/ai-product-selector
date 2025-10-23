"""
Workflow Engine - 轻量级本地工作流引擎

基于LangGraph的工作流编排引擎，支持Python节点和条件节点，
提供RESTful API和实时控制台功能。
"""

from .core.registry import register_function
from .core.engine import WorkflowEngine
from .api.server import create_app

__version__ = "1.0.0"
__all__ = ["register_function", "WorkflowEngine", "create_app"]