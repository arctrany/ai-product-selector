"""
Scenes模块 - 应用场景集合
包含各种自动化场景的实现
"""

from .automation_scenario import AutomationScenario
from .scene_interface import SceneInterface
from .seerfar_scene import SeerfarScene
from .seerfar_launcher import SeerfarLauncher

__all__ = ['AutomationScenario', 'SceneInterface', 'SeerfarScene', 'SeerfarLauncher']