"""
Seerfar场景Web模块 - 智能选品场景的Web界面实现
包含场景特定的表单、接口和Web服务
"""

from .seerfar_web import app
from .seerfar_interface import WebUserInterface

__all__ = ['app', 'WebUserInterface']